# ruff: noqa: E501, E402
"""Execute the full existing DRAFT family queue against licensed Canadian raw datasets."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import SourceRegistry  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.knowledge import ImportManifest  # noqa: E402
from app.services.knowledge_import import (
    enqueue,
    process_job,
    publish_job,
    review_job,
    store_document,
)  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main():
    from app.services.market_priority import policy

    if policy().get("active") and not policy().get("allow_uniform_catalog_expansion"):
        raise SystemExit("AZ_MARKET_FIRST: uniform NRCan expansion disabled; use the reviewed local market queue")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-manifests",
        action="store_true",
        help="Explicitly create a new local batch with current reviewed model boundaries",
    )
    args = parser.parse_args()
    queue = json.loads(
        (ROOT / "data/manifests/verified-data-work-queue.json").read_text(encoding="utf-8")
    )
    mappings = [{"make": r["make"], "model": r["model"]} for r in queue["families"]]
    boundaries = json.loads((ROOT / "data/manifests/nrcan-model-boundaries.json").read_text())[
        "rules"
    ]
    for rule in boundaries:
        family = {"make": rule["make"], "model": rule["model"]}
        if family not in mappings:
            mappings.append(family)
    receipts = json.loads((ROOT / "deliverables/VerifiedData/acquisition-ledger.json").read_text())
    downloads = {
        r["url"]: r
        for r in receipts
        if r.get("http_status") == 200
        and r["url"].endswith(".csv")
        and "open.canada.ca" in r["url"]
    }
    results = []
    with SessionLocal() as db:
        if not db.get(SourceRegistry, "nrcan"):
            db.add(
                SourceRegistry(
                    id="nrcan",
                    title="Natural Resources Canada · fuel consumption ratings",
                    state="APPROVED",
                    config={
                        "owner": "Natural Resources Canada",
                        "markets": ["CA"],
                        "data_types": ["certification_configuration", "consumption", "emissions"],
                        "documentation_url": "https://open.canada.ca/data/dataset/98f1a129-f628-4ce4-b24d-6f16bf24dd64",
                        "rights_url": "https://open.canada.ca/en/open-government-licence-canada",
                        "rights": "OPEN_GOVERNMENT_LICENCE_CANADA_2.0",
                        "checked_at": "2026-09-20",
                        "adapter": "nrcan-csv-v1",
                        "authentication": "NONE_PUBLIC",
                        "cost_model": "FREE",
                        "commercial_reuse": True,
                        "storage_rights": "OPEN_LICENSE",
                        "display_rights": "ATTRIBUTION_REQUIRED",
                        "resale_rights": "OPEN_LICENSE",
                        "attribution": "Contains information licensed under the Open Government Licence – Canada.",
                        "verified_rate_limit": None,
                        "request_budget": 5,
                        "allowed_download_urls": [],
                        "freshness_days": {"specifications": 90, "rights": 90},
                        "limitations": "Canadian rows; tested cycle, not AZ real consumption. No generation or drivetrain inferred from US records. No logo licence.",
                    },
                )
            )
        actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
        if not actor:
            raise ValueError("EXISTING_REVIEW_ACTOR_REQUIRED")
        db.commit()
        for index, (url, r) in enumerate(downloads.items()):
            kind = "BEV" if "battery" in url else "PHEV" if "plug-in" in url else "CONVENTIONAL"
            raw = (ROOT / ".localdata/verified-source-documents" / r["sha256"]).read_bytes()
            doc = store_document(db, "nrcan", raw, locator=url, media_type="text/csv")
            manifest_path = ROOT / f"data/manifests/nrcan-batch-{index + 1}.json"
            manifest = (
                ImportManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
                if manifest_path.exists() and not args.refresh_manifests
                else ImportManifest(
                    source_id="nrcan",
                    parser="nrcan-csv-v1",
                    document_id=doc.id,
                    dataset_kind=kind,
                    family_mappings=mappings,
                    family_limit=1000,
                    versions_per_family=12,
                    year_min=2015,
                    year_max=2026,
                    selection_basis=f"Existing DRAFT queue plus reviewed source-name boundaries ({len(mappings)} mappings); longest same-make model prefix for search; original names preserved; 12 latest rows per family/dataset; not AZ prevalence",
                )
            )
            manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
            job = enqueue(db, manifest)
            while job.state in {"QUEUED", "RUNNING"}:
                process_job(db, job.id, batch_size=500)
                print(
                    json.dumps({"dataset": kind, "state": job.state, "cursor": job.cursor}),
                    flush=True,
                )
            if job.state == "STAGED":
                review_job(
                    db,
                    job,
                    actor,
                    approve=True,
                    note="Agent technical review: licensed NRCan one-row tuples, strict schema and source field locators; no exact generation promotion",
                )
            if job.state == "APPROVED":
                publish_job(
                    db,
                    job,
                    actor,
                    note="Publish licensed Canadian certification facts; retain original US and Report snapshots",
                )
            results.append(
                {
                    "job_id": job.id,
                    "state": job.state,
                    "dataset": kind,
                    "source_url": url,
                    "sha256": r["sha256"],
                    "rows": job.cursor,
                    "errors": job.errors,
                }
            )
            (ROOT / "deliverables/VerifiedData/nrcan-publications.json").write_text(
                json.dumps(results, indent=2)
            )
            if job.state != "PUBLISHED":
                raise ValueError("BATCH_NOT_PUBLISHED")
    print(json.dumps(results), flush=True)


if __name__ == "__main__":
    main()

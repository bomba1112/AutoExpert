"""Publish reviewed annual trim headings for batch 08 through the existing importer.

The source map is data/manifests/us-bulk-data-08-trim-review.json. Frozen reviewed
manifests make retries idempotent; no application matching or readiness rules change.
"""

# ruff: noqa: E402
import argparse
import copy
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal
from app.models.catalog import VehicleVariant
from app.models.user import User
from app.schemas.knowledge import CatalogRecord, FactInput, ImportManifest
from app.services.catalog_verification import validate_publication
from app.services.knowledge_import import enqueue, process_job, publish_job, review_job
from sqlalchemy import select

OUT = ROOT / "deliverables/VerifiedData/us-bulk-data-08"
REVIEW = ROOT / "data/manifests/us-bulk-data-08-trim-review.json"
PREPARED = OUT / "prepared.json"


def manifests(db):
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    targets = json.loads(PREPARED.read_text(encoding="utf-8"))["targets"]
    assert len(targets) == 60
    groups = defaultdict(list)
    seen = set()
    for target in targets:
        key = target["family_id"] + "/" + target["group_id"]
        if key not in review["trim_by_family_group"]:
            continue
        seen.add(key)
        previous = db.scalar(
            select(VehicleVariant).where(VehicleVariant.catalog_key == target["catalog_key"])
        )
        if previous is None or not previous.published_revision_id:
            raise ValueError("PUBLISHED_VARIANT_REQUIRED:" + target["catalog_key"])
        current = previous.specifications["catalog"]
        if current["facts"].get("trim", {}).get("status") == "CONFIRMED":
            raise ValueError("TRIM_ALREADY_CONFIRMED:" + target["catalog_key"])
        value = {k: copy.deepcopy(v) for k, v in current.items() if k in CatalogRecord.model_fields}
        value["facts"] = {
            name: {
                key: copy.deepcopy(item)
                for key, item in fact.items()
                if key in FactInput.model_fields
            }
            for name, fact in current["facts"].items()
        }
        label = review["trim_by_family_group"][key]
        source = copy.deepcopy(value["facts"]["engine_description"]["documentary_source"])
        value["facts"]["trim"] = {
            "value": label,
            "status": "CONFIRMED",
            "locator": (
                "US annual manufacturer trim heading and matching engine/drive column: "
                + source["locator"]
            )[:500],
            "documentary_source": source,
        }
        value["identity_verification"]["previous_revision_id"] = previous.published_revision_id
        value["revision_note"] = (
            "Batch08 annual manufacturer trim heading confirmed; original "
            "engine/transmission/drive applicability unchanged."
        )
        record = CatalogRecord.model_validate(value)
        groups[target["source_id"]].append(record)
    if seen != set(review["trim_by_family_group"]):
        raise ValueError("TRIM_REVIEW_GROUP_NOT_IN_PREPARED_BATCH")
    if sum(map(len, groups.values())) != 54:
        raise ValueError("EXPECTED_54_ANNUAL_TRIM_CONFIGURATIONS")
    result = []
    for source_id, rows in sorted(groups.items()):
        value = ImportManifest(
            source_id=source_id,
            parser="manifest-json-v1",
            records=rows,
            selection_basis=(
                "Reviewed batch08 annual manufacturer trim headings; no trim guessed "
                "from configuration labels; exact US model year applicability"
            ),
        )
        path = OUT / f"trim-reviewed-{source_id}.json"
        path.write_text(
            json.dumps(value.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result.append(path)
    return result


def run(publish):
    started = time.perf_counter()
    with SessionLocal() as db:
        paths = sorted(OUT.glob("trim-reviewed-factory-*-us.json"))
        if not paths:
            paths = manifests(db)
        actor = None
        if publish:
            actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
            if actor is None:
                raise ValueError("EXISTING_REVIEW_ACTOR_REQUIRED")
        results = []
        for path in paths:
            manifest = ImportManifest.model_validate_json(path.read_text(encoding="utf-8"))
            job = enqueue(db, manifest) if publish else None
            if job is not None and job.state == "PUBLISHED":
                results.append(
                    {
                        "source_id": manifest.source_id,
                        "records": len(manifest.records),
                        "state": "PUBLISHED",
                        "unchanged_replay": True,
                    }
                )
                continue
            for record in manifest.records:
                previous = db.scalar(
                    select(VehicleVariant).where(
                        VehicleVariant.catalog_key == manifest.source_id + ":" + record.external_key
                    )
                )
                if previous is None or validate_publication(db, record, previous) is None:
                    raise ValueError("TRIM_PREFLIGHT_FAILED:" + record.external_key)
            if publish:
                while job.state in {"QUEUED", "RUNNING"}:
                    process_job(db, job.id, batch_size=25)
                if job.state == "STAGED":
                    review_job(
                        db, job, actor, note="Annual US factory trim cells reviewed", approve=True
                    )
                if job.state != "PUBLISHED":
                    publish_job(db, job, actor, note="Publish annual source-backed trim facts")
            results.append(
                {
                    "source_id": manifest.source_id,
                    "records": len(manifest.records),
                    "state": "PUBLISHED" if publish else "PREFLIGHT_PASS",
                }
            )
    output = {
        "state": "PUBLISHED" if publish else "PREFLIGHT_PASS",
        "records": sum(item["records"] for item in results),
        "seconds": round(time.perf_counter() - started, 3),
        "results": results,
    }
    if publish:
        name = (
            "trim-replay.json"
            if all(item.get("unchanged_replay") for item in results)
            else "trim-publication.json"
        )
        (OUT / name).write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-reviewed", action="store_true")
    args = parser.parse_args()
    run(args.publish_reviewed)

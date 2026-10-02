"""Versioned source-name correction; original EPA data and raw NRCan identity are retained."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.knowledge import CatalogRecord, ImportManifest  # noqa: E402
from app.services.catalog_buyer import records  # noqa: E402
from app.services.knowledge_import import (  # noqa: E402
    enqueue,
    process_job,
    publish_job,
    review_job,
)
from sqlalchemy import select  # noqa: E402

rules = json.loads((ROOT / "data/manifests/nrcan-model-boundaries.json").read_text())["rules"]
manifest_path = ROOT / "data/manifests/nrcan-reviewed-model-corrections.json"
with SessionLocal() as db:
    corrections = []
    for _, c in records(db):
        if c["source_registry_id"] != "nrcan":
            continue
        match = next(
            (
                r
                for r in rules
                if r["make"].casefold() == c["make"].casefold()
                and (
                    c["configuration"].casefold().startswith(r["prefix"].casefold() + " ")
                    or c["configuration"].casefold() == r["prefix"].casefold()
                )
            ),
            None,
        )
        if not match or c["model"] == match["model"]:
            continue
        payload = {k: c[k] for k in CatalogRecord.model_fields if k in c}
        payload["model"] = match["model"]
        payload["aliases"] = [
            a for a in payload["aliases"] if a.casefold() != c["model"].casefold()
        ]
        payload["facts"] = {
            key: {
                k: v
                for k, v in f.items()
                if k in {"value", "unit", "status", "locator", "source_date", "labels", "titles"}
            }
            for key, f in c["facts"].items()
        }
        payload["revision_note"] = (
            "Source model-name boundary correction; no inferred generation/engine/trim"
        )
        corrections.append(CatalogRecord.model_validate(payload))
    if corrections:
        manifest = ImportManifest(
            source_id="nrcan",
            parser="manifest-json-v1",
            records=corrections,
            selection_basis=("Reviewed distinct NRCan model names; do not collapse IONIQ 5/9, "
                             "Corolla Cross and named EV models into prefix families"),
        )
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
        job = enqueue(db, manifest)
        while job.state in {"QUEUED", "RUNNING"}:
            process_job(db, job.id, batch_size=100)
        review_job(
            db,
            job,
            actor,
            approve=True,
            note="Source Model names reviewed; only family boundary changes",
        )
        publish_job(
            db,
            job,
            actor,
            note="Publish source-name correction while retaining all earlier revisions",
        )
        result = {"state": job.state, "job_id": job.id, "corrected_rows": len(corrections)}
        (ROOT / "deliverables/VerifiedData/model-boundary-correction.json").write_text(
            json.dumps(result, indent=2)
        )
        print(json.dumps(result))
    else:
        print("Model boundaries already corrected; no new job")

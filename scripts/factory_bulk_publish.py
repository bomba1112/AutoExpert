"""Run prepared factory facts through the existing reviewed import publisher.

The default preflight is read-only. Publication requires --publish-reviewed and a
prior local backup; the operator coordinates this with any other active batch.
"""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from catalog_writer_lock import catalog_writer_lock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal
from app.models.catalog import VehicleVariant
from app.models.user import User
from app.schemas.knowledge import ImportManifest
from app.services.catalog_verification import validate_publication
from app.services.knowledge_import import (
    enqueue,
    process_job,
    publish_job,
    review_job,
)
from sqlalchemy import select

OUT = ROOT / "deliverables/VerifiedData/us-bulk-data-08"
MANIFESTS = [OUT / "factory-reviewed-epa.json", OUT / "factory-reviewed-factory-kia-us.json"]
LOCALIZATION_MANIFESTS = [
    OUT / "factory-localized-epa.json",
    OUT / "factory-localized-factory-kia-us.json",
]


def run(*, publish_reviewed: bool, localization: bool = False, manifests=None, output=None):
    started = time.perf_counter()
    results = []
    selected = manifests or (LOCALIZATION_MANIFESTS if localization else MANIFESTS)
    out = output or OUT
    with catalog_writer_lock(), SessionLocal() as db:
        actor = None
        if publish_reviewed:
            actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
            if actor is None:
                raise ValueError("EXISTING_REVIEW_ACTOR_REQUIRED")
        for path in selected:
            if not path.exists():
                continue
            manifest = ImportManifest.model_validate_json(path.read_text(encoding="utf-8"))
            job = enqueue(db, manifest) if publish_reviewed else None
            if job is not None and job.state == "PUBLISHED":
                results.append(
                    {
                        "source_id": manifest.source_id,
                        "records": len(manifest.records),
                        "job_state": "PUBLISHED",
                        "unchanged_replay": True,
                    }
                )
                continue
            checked = 0
            for record in manifest.records:
                key = manifest.source_id + ":" + record.external_key
                previous = db.scalar(
                    select(VehicleVariant).where(VehicleVariant.catalog_key == key)
                )
                if previous is None:
                    raise ValueError("FACTORY_EXISTING_VARIANT_REQUIRED:" + key)
                result = validate_publication(db, record, previous)
                if result is None or result["state"] != "VERIFIED_SCOPED":
                    raise ValueError("FACTORY_VERIFICATION_GATE_REQUIRED:" + key)
                checked += 1
            if publish_reviewed:
                while job.state in {"QUEUED", "RUNNING"}:
                    process_job(db, job.id, batch_size=25)
                if job.state == "STAGED":
                    review_job(
                        db,
                        job,
                        actor,
                        note=(
                            "Reviewed cached US factory documents and exact applicability; "
                            "preserve existing verified body/MY and trim/engine/drive restrictions"
                        ),
                        approve=True,
                    )
                if job.state != "PUBLISHED":
                    publish_job(
                        db,
                        job,
                        actor,
                        note=(
                            "Publish source-backed factory facts to existing variants; "
                            "preserve all prior revisions and identity gates"
                        ),
                    )
                results.append(
                    {"source_id": manifest.source_id, "records": checked, "job_state": job.state}
                )
            else:
                results.append(
                    {"source_id": manifest.source_id, "records": checked, "state": "PREFLIGHT_PASS"}
                )
    output = {
        "state": "PUBLISHED" if publish_reviewed else "PREFLIGHT_PASS",
        "scope": "AZ_RU_LABELS_ONLY" if localization else "NEW_FACTORY_FACTS",
        "seconds": round(time.perf_counter() - started, 3),
        "results": results,
    }
    if publish_reviewed:
        prefix = "factory-localization" if localization else "factory"
        replay = all(item.get("unchanged_replay") for item in results)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{prefix}-{'replay' if replay else 'publication'}.json").write_text(
            json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-reviewed", action="store_true")
    parser.add_argument("--localization", action="store_true")
    parser.add_argument("--manifest", action="append", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run(
        publish_reviewed=args.publish_reviewed,
        localization=args.localization,
        manifests=args.manifest,
        output=args.output,
    )

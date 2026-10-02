"""Local operator entry point. Never prints credentials or tokens."""

import argparse
import csv
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.db.session import SessionLocal
from app.models.knowledge_ops import RawDocument
from app.models.user import User
from app.schemas.knowledge import ImportManifest
from app.services.catalog_buyer import coverage, records
from app.services.knowledge_import import (
    document_text,
    enqueue,
    epa_record,
    parse_records,
    private_path,
    process_job,
)
from app.services.knowledge_registry import seed_registry
from sqlalchemy import select

parser = argparse.ArgumentParser()
parser.add_argument("command", choices=["seed-registry", "grant-admin", "import", "coverage"])
parser.add_argument("--email")
parser.add_argument("--manifest")
parser.add_argument("--reuse-cache", action="store_true")
parser.add_argument("--include-published", action="store_true")
args = parser.parse_args()
with SessionLocal() as db:
    if args.command == "seed-registry":
        seed_registry(db)
        print("Registry initialized; existing policy retained")
    elif args.command == "grant-admin":
        user = db.scalar(select(User).where(User.email == (args.email or "").casefold()))
        if not user:
            raise SystemExit("Register the operator account first")
        user.is_admin = True
        db.commit()
        print("Existing operator account granted admin access locally")
    elif args.command == "import":
        manifest = ImportManifest.model_validate_json(
            Path(args.manifest).read_text(encoding="utf-8")
        )
        if args.reuse_cache:
            doc = db.scalar(
                select(RawDocument)
                .where(RawDocument.source_id == manifest.source_id)
                .order_by(RawDocument.created_at.desc())
            )
            if doc is None:
                raise SystemExit("No cached source document; run the authorized download first")
            manifest = manifest.model_copy(
                update={"document_id": doc.id, "download_url": None, "expected_sha256": doc.sha256}
            )
            if args.include_published and manifest.parser == "epa-csv-v1":
                from types import SimpleNamespace

                selected = {
                    r["external_key"]: r
                    for r in parse_records(
                        SimpleNamespace(manifest=manifest.model_dump(mode="json")), doc
                    )
                }
                existing = {
                    c["external_key"]
                    for _, c in records(db)
                    if c["source_registry_id"] == manifest.source_id
                }
                for row in csv.DictReader(
                    io.StringIO(document_text(private_path(doc.storage_key).read_bytes()))
                ):
                    if row["id"] in existing:
                        selected[row["id"]] = epa_record(row).model_dump(mode="json")
                manifest = ImportManifest.model_validate(
                    {**manifest.model_dump(mode="json"), "records": list(selected.values())}
                )
        job = enqueue(db, manifest)
        while job.state in {"QUEUED", "RUNNING"}:
            job = process_job(db, job.id)
        print(
            json.dumps(
                {"id": job.id, "state": job.state, "metrics": job.metrics, "errors": job.errors}
            )
        )
    else:
        print(json.dumps(coverage(db)))

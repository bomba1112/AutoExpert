# ruff: noqa: E402
"""Validate a permitted minimal export before storing it in the publication pipeline."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.knowledge import ImportManifest  # noqa: E402
from app.services.knowledge_import import (
    enqueue,
    process_job,
    publish_job,
    review_job,
    store_document,
)  # noqa: E402
from app.services.knowledge_registry import require_source  # noqa: E402
from app.services.market_discovery import parse_csv, validate_records  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--source", default="turbo-market-discovery")
    parser.add_argument("--publish-reviewed", action="store_true")
    args = parser.parse_args()
    if args.path.stat().st_size > 20 * 1024 * 1024:
        raise SystemExit("MARKET_EXPORT_SIZE_BUDGET")
    text = args.path.read_text(encoding="utf-8-sig")
    rows = parse_csv(text) if args.path.suffix.lower() == ".csv" else json.loads(text)
    with SessionLocal() as db:
        source = require_source(db, args.source)
        # Unknown fields (including account/session/contact data) fail before any raw copy.
        sanitized = validate_records(rows, source)
        raw = json.dumps(sanitized, ensure_ascii=False).encode()
        doc = store_document(db, source.id, raw, locator="owner-permitted-minimal-export")
        manifest = ImportManifest(
            source_id=source.id,
            document_id=doc.id,
            parser="market-discovery-json-v1",
            selection_basis="Owner-permitted AZ market export; seller market claims only",
        )
        job = enqueue(db, manifest)
        while job.state in {"QUEUED", "RUNNING"}:
            process_job(db, job.id, batch_size=100)
        if args.publish_reviewed:
            actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
            if not actor:
                raise ValueError("EXISTING_REVIEW_ACTOR_REQUIRED")
            if job.state == "STAGED":
                review_job(
                    db,
                    job,
                    actor,
                    approve=True,
                    note="Review source rights, dated count scope and minimal seller claims",
                )
            if job.state == "APPROVED":
                publish_job(
                    db,
                    job,
                    actor,
                    note="Publish market discovery only; no technical identity mutations",
                )
        print(
            json.dumps(
                {
                    "job_id": job.id,
                    "status": job.state,
                    "records": job.cursor,
                    "errors": job.errors,
                    "paid_calls": 0,
                }
            )
        )


if __name__ == "__main__":
    main()

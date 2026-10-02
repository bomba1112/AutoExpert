"""Offline normalized-data replay into a migrated database; never restores private accounts."""

import argparse
import json
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import SourceRegistry  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.knowledge import ImportManifest  # noqa: E402
from app.services.knowledge_import import (  # noqa: E402
    enqueue,
    process_job,
    publish_job,
    review_job,
)
from sqlalchemy import select  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--publish-reviewed",
        action="store_true",
        help="Explicitly publish the inspected normalized manifests; default stages only",
    )
    args = parser.parse_args()
    with SessionLocal() as db:
        for source in json.loads((args.directory / "source-registry.json").read_text()):
            if db.get(SourceRegistry, source["id"]) is None:
                db.add(SourceRegistry(**source))
        actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
        if actor is None:
            actor = User(
                email="catalog-review@local.invalid",
                password_hash=hash_password(secrets.token_urlsafe(48)),
                is_admin=True,
                is_active=False,
                preferred_language="ru",
                country_code="AZ",
            )
            db.add(actor)
        db.commit()
        manifests = sorted(args.directory.glob("*-catalog.json")) + sorted(
            args.directory.glob("*-ownership.json")
        )
        for path in manifests:
            manifest = ImportManifest.model_validate_json(path.read_text(encoding="utf-8"))
            job = enqueue(db, manifest)
            while job.state in {"QUEUED", "RUNNING"}:
                process_job(db, job.id, batch_size=100)
            if args.publish_reviewed and job.state == "STAGED":
                review_job(
                    db,
                    job,
                    actor,
                    approve=True,
                    note="Offline replay of reviewed source facts; no human image approval",
                )
            if args.publish_reviewed and job.state == "APPROVED":
                publish_job(
                    db,
                    job,
                    actor,
                    note="Offline replay; original source rights and publication scope retained",
                )
            print(
                json.dumps(
                    {
                        "manifest": path.name,
                        "job_id": job.id,
                        "state": job.state,
                        "cursor": job.cursor,
                        "errors": len(job.errors),
                    }
                ),
                flush=True,
            )
            if job.errors or job.state not in {"STAGED", "PUBLISHED"}:
                raise SystemExit("Replay requires review; remaining data not imported")


if __name__ == "__main__":
    main()

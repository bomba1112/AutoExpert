"""Idempotently register Ford US factory documents (owner's manuals, warranty and maintenance
guides) as local research evidence; mirrors scripts/register_factory_tesla_us.py."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import SourceRegistry  # noqa: E402


def main():
    source_id = "factory-ford-us"
    with SessionLocal() as db:
        existing = db.get(SourceRegistry, source_id)
        if existing:
            if not existing.config.get("factory_identity_evidence"):
                raise SystemExit("Existing Ford registry cannot establish factory identity")
            print("EXISTS factory-ford-us")
            return
        db.add(
            SourceRegistry(
                id=source_id,
                title="Ford Motor Company - factory documents",
                state="LOCAL_RESEARCH",
                config={
                    "owner": "Ford Motor Company · factory documents",
                    "markets": ["US"],
                    "cost_model": "FREE",
                    "commercial_reuse": False,
                    "factory_identity_evidence": True,
                    "data_types": ["factory_specification", "maintenance"],
                    "storage_rights": "LOCAL_PUBLIC_FACT_RESEARCH",
                    "display_rights": "LOCAL_RESEARCH_ONLY",
                    "rights": "COMMERCIAL_REUSE_NOT_ESTABLISHED",
                    "checked_at": datetime.now(UTC).date().isoformat(),
                },
            )
        )
        db.commit()
    print("REGISTERED factory-ford-us")


if __name__ == "__main__":
    main()

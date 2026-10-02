"""Idempotently register official Tesla US service documents as local research evidence."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import SourceRegistry  # noqa: E402


def main():
    source_id = "factory-tesla-us"
    with SessionLocal() as db:
        existing = db.get(SourceRegistry, source_id)
        if existing:
            if not existing.config.get("factory_identity_evidence"):
                raise SystemExit("Existing Tesla registry cannot establish factory identity")
            print("EXISTS factory-tesla-us")
            return
        db.add(
            SourceRegistry(
                id=source_id,
                title="Tesla official US service manuals",
                state="LOCAL_RESEARCH",
                config={
                    "owner": "Tesla official manufacturer service documentation",
                    "markets": ["US"],
                    "cost_model": "FREE",
                    "commercial_reuse": False,
                    "factory_identity_evidence": True,
                    "data_types": ["factory_specification", "service_manual"],
                    "storage_rights": "LOCAL_PUBLIC_FACT_RESEARCH",
                    "display_rights": "LOCAL_RESEARCH_ONLY",
                    "rights": "COMMERCIAL_REUSE_NOT_ESTABLISHED",
                    "checked_at": datetime.now(UTC).date().isoformat(),
                },
            )
        )
        db.commit()
    print("REGISTERED factory-tesla-us")


if __name__ == "__main__":
    main()

"""Idempotently register auto-data.net (secondary specification database, prompt 5.9) as a local
research source; mirrors scripts/register_carcomplaints.py. European listings, matched to US
configurations only where no US owner's manual exists; no factory identity."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import SourceRegistry  # noqa: E402


def main():
    source_id = "auto-data"
    with SessionLocal() as db:
        if db.get(SourceRegistry, source_id):
            print("EXISTS auto-data")
            return
        db.add(
            SourceRegistry(
                id=source_id,
                title="auto-data.net - specification database (secondary)",
                state="LOCAL_RESEARCH",
                config={
                    "owner": "auto-data.net · secondary specification database",
                    "markets": ["EU"],
                    "cost_model": "FREE",
                    "commercial_reuse": False,
                    "factory_identity_evidence": False,
                    "data_types": ["engine_oil_capacity", "coolant_capacity"],
                    "storage_rights": "LOCAL_PUBLIC_FACT_RESEARCH",
                    "display_rights": "LOCAL_RESEARCH_ONLY",
                    "rights": "COMMERCIAL_REUSE_NOT_ESTABLISHED",
                    "robots_txt": "User-agent: * Allow: / (checked 2026-10-02)",
                    "usage": "SECONDARY; European listings matched to US configurations by designation, displacement, cylinders, drive and years; only where no US owner's manual",
                    "checked_at": datetime.now(UTC).date().isoformat(),
                },
            )
        )
        db.commit()
    print("REGISTERED auto-data")


if __name__ == "__main__":
    main()

"""Idempotently register CarComplaints.com (owner-report summaries, prompt sections 5 and 7) as
a local research source; mirrors scripts/register_factory_tesla_us.py. Owner reports only:
no factory identity, no commercial reuse established."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import SourceRegistry  # noqa: E402


def main():
    source_id = "carcomplaints"
    with SessionLocal() as db:
        if db.get(SourceRegistry, source_id):
            print("EXISTS carcomplaints")
            return
        db.add(
            SourceRegistry(
                id=source_id,
                title="CarComplaints.com - owner complaint summaries",
                state="LOCAL_RESEARCH",
                config={
                    "owner": "CarComplaints.com · owner reports",
                    "markets": ["US"],
                    "cost_model": "FREE",
                    "commercial_reuse": False,
                    "factory_identity_evidence": False,
                    "data_types": ["owner_reports", "repair_cost", "repair_mileage"],
                    "storage_rights": "LOCAL_PUBLIC_FACT_RESEARCH",
                    "display_rights": "LOCAL_RESEARCH_ONLY",
                    "rights": "COMMERCIAL_REUSE_NOT_ESTABLISHED",
                    "robots_txt": "general crawling allowed (checked 2026-10-02)",
                    "checked_at": datetime.now(UTC).date().isoformat(),
                },
            )
        )
        db.commit()
    print("REGISTERED carcomplaints")


if __name__ == "__main__":
    main()

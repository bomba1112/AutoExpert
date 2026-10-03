"""Register Teoalida (paid car databases; the owner's samples in C:\\AutoExpertData\\raw\\teoalida)
as a secondary, research-only source, store one raw_documents row per unique file and write
data_work/_shared/manifest_teoalida.csv. Idempotent; mirrors register_autodata.py.

raw_documents keeps a JSON descriptor (file, sha256, sheets and row counts, raw-store path); the
workbook itself stays in the raw store outside OneDrive, as for the batch PDFs.

  AUTOEXPERT_DATABASE_URL=sqlite:///<absolute path> uv run --no-project --with openpyxl --with xlrd \\
      --with-requirements backend/requirements.txt python scripts/register_teoalida.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import SourceRegistry  # noqa: E402
from app.services.knowledge_import import store_document  # noqa: E402
from teoalida_common import descriptor, inventory, write_manifest  # noqa: E402

SOURCE_ID = "teoalida"


def main() -> int:
    rows = inventory()
    with SessionLocal() as db:
        if not db.get(SourceRegistry, SOURCE_ID):
            db.add(SourceRegistry(
                id=SOURCE_ID,
                title="Teoalida car databases (owner's samples) - secondary",
                state="LOCAL_RESEARCH",
                config={
                    "owner": "Teoalida (teoalida.com) · compiled car databases; Ravenol oil-finder scrape",
                    "markets": ["US", "EU", "CN", "JP", "UK", "ES", "IN"],
                    "cost_model": "PAID",
                    "tier": "SECONDARY",
                    "commercial_reuse": False,
                    "factory_identity_evidence": False,
                    "data_types": ["specifications", "fluid_capacities", "unit_codes", "service_intervals",
                                   "tire_sizes", "platform_codes"],
                    "storage_rights": "LOCAL_RESEARCH_ONLY",
                    "display_rights": "LOCAL_RESEARCH_ONLY",
                    "rights": "RESEARCH_ONLY",
                    "usage": "SECONDARY_NOTE only; agreement with an official source is a second confirmation; "
                             "a field is written only when its agreement with official values is at least 90%",
                    "checked_at": datetime.now(UTC).date().isoformat(),
                },
            ))
            db.flush()
            print("REGISTERED teoalida")
        else:
            print("EXISTS teoalida")
        for row in rows:
            if row["duplicate_of"]:
                row["status"] = "duplicate"
                continue
            doc = store_document(db, SOURCE_ID, descriptor(row), locator=f"rawstore:teoalida/{row['file']}",
                                 media_type="application/json")
            row["raw_document_id"] = doc.id
            row["status"] = "registered"
        db.commit()
    for row in rows:
        if row["duplicate_of"]:
            row["raw_document_id"] = next(r["raw_document_id"] for r in rows if r["file"] == row["duplicate_of"])
    write_manifest(rows)
    print(f"files {len(rows)}; unique {sum(1 for r in rows if not r['duplicate_of'])}; duplicates "
          f"{sum(1 for r in rows if r['duplicate_of'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

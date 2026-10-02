"""Read-only snapshot of EPA annual RAV4 tuples from the existing local raw document."""
# ruff: noqa: E501

import csv
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.knowledge_ops import RawDocument
from app.services.knowledge_import import document_text, private_path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07/rav4-source-work/epa-rav4-tuples.json"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"

with SessionLocal() as db:
    doc = db.get(RawDocument, EPA_DOC)
    rows = list(csv.DictReader(document_text(private_path(doc.storage_key).read_bytes()).splitlines()))
    found = [
        {key: row.get(key) for key in ("id", "year", "make", "model", "baseModel", "displ", "cylinders", "fuelType", "trany", "drive", "city08", "highway08", "comb08")}
        for row in rows
        if row.get("make") == "Toyota"
        and row.get("year") in {"2019", "2020", "2021"}
        and "RAV4" in row.get("model", "").upper()
    ]

OUT.write_text(json.dumps(found, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"EPA_RAV4_annual_rows": len(found), "by_year": {year: sum(r["year"] == year for r in found) for year in ("2019", "2020", "2021")}}))
for row in found:
    print(" | ".join(str(row[k]) for k in ("id", "year", "model", "displ", "fuelType", "trany", "drive")))

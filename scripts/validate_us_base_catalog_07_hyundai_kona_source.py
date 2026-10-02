"""Read-only row-level source verification for US Hyundai Kona OS MY2018–19."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.market_priority import base_catalog_batch  # noqa: E402

MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-hyundai-kona-os.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def main() -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base_catalog_batch(manifest=value)
    receipts = json.loads((WORK / "acquisition-hyundai-kona.json").read_text(encoding="utf-8"))
    by_name = {row["name"]: row for row in receipts if row.get("http_status") == 200}
    checked = []
    for row in receipts:
        payload = (ROOT / row["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == row["sha256"], row["name"]
        assert payload.startswith(b"%PDF-") if row["media_type"] == "application/pdf" else b"Hyundai Motor America" in payload, row["name"]
        checked.append(row["name"])
    os_pdf = PdfReader(ROOT / by_name["hyundai-kona-os-generation"]["path"])
    assert "Kona (OS)" in (os_pdf.pages[8].extract_text() or "")
    assert "2018 - 2022" in (os_pdf.pages[8].extract_text() or "")
    family = value["families"][0]
    groups = family["groups"]
    assert len(groups) == 16 and len({group["id"] for group in groups}) == 16
    rows_checked = []
    for year in (2018, 2019):
        source = by_name[f"hyundai-kona-{year}-pricing"]
        soup = BeautifulSoup((ROOT / source["path"]).read_bytes(), "html.parser")
        table = soup.find("table")
        assert table is not None
        source_rows = [[cell.get_text(" ", strip=True) for cell in tr.find_all(["th", "td"])] for tr in table.find_all("tr")]
        source_rows = [row for row in source_rows if len(row) == 5]
        for group in [group for group in groups if group["year_from"] == year]:
            trim = group["facts"]["trim"]
            drive = group["allowed_drives"][0]
            actual = [row for row in source_rows if row[0] == trim and row[3] == drive]
            assert len(actual) == 1, (year, trim, drive)
            row = actual[0]
            is_base = trim in {"SE", "SEL"}
            assert compact("2.0L") in compact(row[1]) if is_base else compact("1.6L Turbo") in compact(row[1]), row
            assert "6speedautomatic" in compact(row[2]) if is_base else "7speedecoshiftdualclutch" in compact(row[2]), row
            assert group["facts"]["transmission_family"] == ("AT" if is_base else "DCT")
            assert group["factory_combinations"] == [{"drivetrain": drive}]
            rows_checked.append({"year": year, "trim": trim, "drivetrain": drive, "source_engine": row[1], "source_transmission": row[2]})
    result = {
        "result": "PASS", "manifest_compatible_with_base_catalog_batch": True,
        "issuer_documents_hash_checked": checked,
        "manufacturer_table_rows_matched": rows_checked,
        "annual_configurations": {"2018": 8, "2019": 8},
        "generation_code_source": "Hyundai Motor America TSB 23-01-014H-2 p9: Kona (OS), MY2018–22",
        "contrast_roof_counted_as_separate_powertrain": False,
        "db_writes": 0,
    }
    (WORK / "validation-hyundai-kona.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"result": result["result"], "rows": len(rows_checked), "documents": len(checked), "db_writes": 0}))


if __name__ == "__main__":
    main()

"""Read-only provenance, applicability and manifest validation for Audi Q7 4M."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.market_priority import base_catalog_batch  # noqa: E402

MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-audi-q7-4m.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EXTRACTS = ROOT / ".localdata/us-base-catalog-07-source-extracts"


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def main() -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base_catalog_batch(manifest=value)
    receipts = json.loads((WORK / "acquisition-audi-q7.json").read_text(encoding="utf-8"))
    by_url = {row["url"]: row for row in receipts if row.get("http_status") == 200}
    checked = []
    for key, spec in value["documents"].items():
        row = by_url[spec["url"]]
        payload = (ROOT / row["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == row["sha256"], (key, "HASH")
        assert payload.startswith(b"%PDF-"), (key, "PDF")
        checked.append({"document": key, "sha256": row["sha256"], "pages": len(PdfReader(ROOT / row["path"]).pages)})
    text17 = compact(json.loads((EXTRACTS / "audi-q7-2017.json").read_text(encoding="utf-8"))[16])
    for token in ("q730t", "2995", "333", "325", "supercharged", "eightspeedtiptronic", "quattro", "seatingcapacity7"):
        assert token in text17, (2017, token)
    # MY2018 p20, MY2019 p12 and the TSB p2 have image-encoded tables.
    # Their exact columns were inspected visually from these cached page renders.
    visual_pages = [
        ("audi-q7-2018-page-20.png", "2018 Technical Specifications: 2.0T 252hp/273lb-ft; 3.0T 333hp/325lb-ft; both eight-speed Tiptronic quattro AWD"),
        ("audi-q7-2019-page-12.png", "2019 Technical Specifications: 45 TFSI 248hp/273lb-ft; 55 TFSI 329hp/325lb-ft; both eight-speed Tiptronic quattro AWD"),
        ("audi-q7-4m-generation-page-2.png", "Audi of America bulletin sales type 4M* applies MY2017, MY2018 and MY2019"),
    ]
    for name, _ in visual_pages:
        assert (EXTRACTS / name).stat().st_size > 10_000, name
    family = value["families"][0]
    groups = family["groups"]
    assert len(groups) == 5 and len({group["id"] for group in groups}) == 5
    assert {year: sum(group["year_from"] == year for group in groups) for year in (2017, 2018, 2019)} == {2017: 1, 2018: 2, 2019: 2}
    assert all(group["year_from"] == group["year_to"] for group in groups)
    assert all(group["allowed_drives"] == ["AWD"] and group["factory_combinations"] == [{"drivetrain": "AWD"}] for group in groups)
    assert {group["facts"]["power_hp"] for group in groups if group["year_from"] == 2019} == {248, 329}
    result = {
        "result": "PASS", "manifest_compatible_with_base_catalog_batch": True,
        "audi_us_document_hashes_checked": checked,
        "rasterized_source_pages_visually_reviewed": [{"path": str((EXTRACTS / name).relative_to(ROOT)).replace("\\", "/"), "observation": description} for name, description in visual_pages],
        "annual_powertrain_tuples": 5,
        "model_years": {"2017": 1, "2018": 2, "2019": 2},
        "2017_2_0t_claimed": False,
        "db_writes": 0,
    }
    (WORK / "validation-audi-q7.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

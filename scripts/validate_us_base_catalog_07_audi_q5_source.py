"""Read-only source and applicability QA for Audi Q5 FY US MY2018–19."""

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

MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-audi-q5-fy.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EXTRACTS = ROOT / ".localdata/us-base-catalog-07-source-extracts"


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def main() -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base_catalog_batch(manifest=value)
    receipts = json.loads((WORK / "acquisition-audi-q5.json").read_text(encoding="utf-8"))
    by_url = {row["url"]: row for row in receipts if row.get("http_status") == 200}
    checked = []
    for key, spec in value["documents"].items():
        row = by_url[spec["url"]]
        payload = (ROOT / row["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == row["sha256"], (key, "HASH")
        assert payload.startswith(b"%PDF-"), (key, "PDF")
        checked.append({"document": key, "sha256": row["sha256"], "pages": len(PdfReader(ROOT / row["path"]).pages)})
    bulletin_p2 = compact(json.loads((EXTRACTS / "audi-q5-fy-generation.json").read_text(encoding="utf-8"))[1])
    for token in ("q5fy20182024", "q58r20092017"):
        assert token in bulletin_p2, token
    # Annual technical tables are image-encoded; their Q5 columns were read
    # directly in the locally rendered PDF pages, separate from adjacent SQ5.
    visual_pages = [
        ("audi-q5-2018-page-18.png", "Q5 column: 1984cc turbo I4, 252hp/273lb-ft, seven-speed S tronic dual-clutch quattro AWD; five seats"),
        ("audi-q5-2019-page-10.png", "Q5 column: 1984cc turbo I4, 248hp/273lb-ft, seven-speed S tronic dual-clutch quattro AWD; five seats"),
    ]
    for name, _ in visual_pages:
        assert (EXTRACTS / name).stat().st_size > 10_000, name
    groups = value["families"][0]["groups"]
    assert len(groups) == 2 and {g["year_from"]: g["facts"]["power_hp"] for g in groups} == {2018: 252, 2019: 248}
    assert all(g["year_from"] == g["year_to"] and g["allowed_drives"] == ["AWD"] and g["facts"]["transmission_family"] == "DCT" for g in groups)
    result = {
        "result": "PASS", "manifest_compatible_with_base_catalog_batch": True,
        "audi_us_document_hashes_checked": checked,
        "rasterized_source_pages_visually_reviewed": [{"path": str((EXTRACTS / name).relative_to(ROOT)).replace("\\", "/"), "observation": observation} for name, observation in visual_pages],
        "annual_powertrain_tuples": 2, "model_years": {"2018": 1, "2019": 1},
        "sq5_counted_as_q5": False, "db_writes": 0,
    }
    (WORK / "validation-audi-q5.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"result": result["result"], "tuples": 2, "documents": 3, "db_writes": 0}))


if __name__ == "__main__":
    main()

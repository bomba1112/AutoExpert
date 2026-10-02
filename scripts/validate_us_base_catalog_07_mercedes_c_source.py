"""Read-only provenance and annual tuple checks for C-Class W205 staging."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.market_priority import base_catalog_batch  # noqa: E402

MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-mercedes-c-w205.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def main() -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base_catalog_batch(manifest=value)
    receipts = json.loads((WORK / "acquisition-mercedes-c.json").read_text(encoding="utf-8"))
    by_url = {row["url"]: row for row in receipts if row.get("http_status") == 200}
    checked = []
    for key, spec in value["documents"].items():
        row = by_url[spec["url"]]
        payload = (ROOT / row["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == row["sha256"], (key, "HASH")
        assert payload.startswith(b"%PDF-") if spec["format"] == "pdf" else b"2019 Mercedes-Benz C-Class Sedan" in payload, (key, "FORMAT")
        checked.append(key)
    for year, spec_page in ((2019, 26), (2020, 26), (2021, 35)):
        pages = json.loads((ROOT / f".localdata/us-base-catalog-07-source-extracts/mercedes-c-{year}.json").read_text(encoding="utf-8"))
        models = compact(pages[5])
        specs = compact(pages[spec_page])
        for token in ("c300", "amgc43", "amgc63", "amgc63s", "sedan", "255hp", "385hp", "469hp", "503hp"):
            assert token in models, (year, "MODEL", token)
        for token in ("255hp", "385hp", "469hp", "503hp", "9gtronic9speed", "amgspeedshifttct", "amgspeedshiftmct", "rearwheeldrive", "allwheeldrive"):
            assert token in specs, (year, "SPEC", token)
    groups = value["families"][0]["groups"]
    assert len(groups) == 15 and len({row["id"] for row in groups}) == 15
    assert {year: sum(row["year_from"] == year for row in groups) for year in (2019, 2020, 2021)} == {2019: 5, 2020: 5, 2021: 5}
    for row in groups:
        assert row["year_from"] == row["year_to"]
        assert row["allowed_drives"] == [row["factory_combinations"][0]["drivetrain"]]
        trim = row["facts"]["trim"]
        if trim.startswith("AMG C 63"):
            assert row["allowed_drives"] == ["RWD"] and "MCT" in row["facts"]["transmission_description"]
        if trim == "AMG C 43":
            assert row["allowed_drives"] == ["AWD"] and "TCT" in row["facts"]["transmission_description"]
    result = {
        "result": "PASS", "manifest_compatible_with_base_catalog_batch": True,
        "official_mbusa_documents_hash_checked": checked,
        "annual_powertrain_tuples": 15, "model_years": {"2019": 5, "2020": 5, "2021": 5},
        "body_scope": "US C-Class W205 facelift sedan only",
        "gearbox_scope": "C300 9G-TRONIC; AMG C43 TCT; AMG C63/C63S MCT",
        "db_writes": 0,
    }
    (WORK / "validation-mercedes-c.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

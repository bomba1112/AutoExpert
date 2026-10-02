"""Read-only source and annual tuple checks for BMW X1 F48 staging."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.market_priority import base_catalog_batch  # noqa: E402

MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-bmw-x1-f48.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"


def compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def main() -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base_catalog_batch(manifest=value)
    receipts = json.loads((WORK / "acquisition-bmw-x1.json").read_text(encoding="utf-8"))
    by_url = {row["url"]: row for row in receipts if row.get("http_status") == 200}
    checked = []
    for key, spec in value["documents"].items():
        row = by_url[spec["url"]]
        payload = (ROOT / row["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == row["sha256"], (key, "HASH")
        assert payload.startswith(b"%PDF-") if spec["format"] == "pdf" else b"BMW X1" in payload, (key, "FORMAT")
        checked.append(key)
    for year in (2017, 2018):
        pages = json.loads((ROOT / f".localdata/us-base-catalog-07-source-extracts/bmw-x1-{year}-tech.json").read_text(encoding="utf-8"))
        first, second = (compact(page) for page in pages)
        for token in (f"{year}bmwx1sportsactivityvehicle", "x1sdrive28ix1xdrive28i", "fwdawd", "b46a20o0b46a20o0", "2285000600022850006000", "2581450450025814504500"):
            assert token in first, (year, "POWERTRAIN", token)
        assert "aisinf22aisinf22" in first + second, (year, "TRANSMISSION")
    raw16 = compact((ROOT / by_url[value["documents"]["bmw-x1-2016-launch-source07"]["url"]]["path"]).read_text(encoding="utf-8"))
    for token in ("secondgeneration", "2016bmwx1xdrive28i", "228horsepower", "8speedsteptronicautomatic", "aisinf22"):
        assert token in raw16, (2016, token)
    raw20 = compact((ROOT / by_url[value["documents"]["bmw-x1-2020-update-source07"]["url"]]["path"]).read_text(encoding="utf-8"))
    for token in ("2020bmwx1", "x1sdr28i", "x1xdr28i", "fwd", "awd", "b46a20o1", "ga8y45ew", "228", "258"):
        assert token in raw20, (2020, token)
    groups = [group for family in value["families"] for group in family["groups"]]
    assert len(groups) == 7 and len({(g["year_from"], g["id"]) for g in groups}) == 7
    assert {year: sum(g["year_from"] == year for g in groups) for year in (2016, 2017, 2018, 2019, 2020)} == {2016: 1, 2017: 2, 2018: 2, 2019: 0, 2020: 2}
    assert all(g["year_from"] == g["year_to"] for g in groups)
    assert all(g["allowed_drives"] == [g["factory_combinations"][0]["drivetrain"]] for g in groups)
    result = {
        "result": "PASS", "manifest_compatible_with_base_catalog_batch": True,
        "official_bmw_us_documents_hash_checked": checked,
        "annual_powertrain_tuples": 7,
        "model_years": {"2016": 1, "2017": 2, "2018": 2, "2020": 2},
        "excluded_unverified_year": 2019,
        "engine_and_transmission_change": "MY2017/18 B46A20O0 + Aisin F22; MY2020 B46A20O1 + GA8Y45EW",
        "db_writes": 0,
    }
    (WORK / "validation-bmw-x1.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

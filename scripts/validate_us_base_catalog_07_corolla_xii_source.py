"""Read-only document, tuple and manifest validation for Corolla XII staging."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.market_priority import base_catalog_batch  # noqa: E402

MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-toyota-corolla-xii.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base_catalog_batch(manifest=manifest)
    receipts = json.loads((WORK / "acquisition-receipts.json").read_text(encoding="utf-8"))
    by_url = {row["url"]: row for row in receipts if row.get("http_status") == 200}
    checked = []
    for key, spec in manifest["documents"].items():
        receipt = by_url[spec["url"]]
        payload = (ROOT / receipt["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == receipt["sha256"], (key, "HASH")
        assert (payload.startswith(b"%PDF-") if spec["format"] == "pdf" else b"12th-generation Toyota Corolla" in payload), (key, "FORMAT_OR_GENERATION")
        checked.append(key)

    text20 = json.loads((ROOT / ".localdata/us-base-catalog-07-source-extracts/toyota-corolla-2020.json").read_text(encoding="utf-8"))
    text21 = json.loads((ROOT / ".localdata/us-base-catalog-07-source-extracts/toyota-corolla-2021.json").read_text(encoding="utf-8"))
    for token in ("1.8L 4-cylinder engine with 139 hp", "2.0L 4-cylinder Dynamic Force Engine with 169 hp", "SE Nightshade Edition", "Hybrid LE"):
        assert token in "\n".join(text20[16:19]), (2020, token)
    for token in ("Electronically controlled Continuously Variable Transmission (ECVT)", "Continuously Variable Transmission with intelligence", "Dynamic-Shift Continuously Variable Transmission (CVT)", "6-speed Intelligent Manual Transmission (iMT)", "Front-Wheel Drive (FWD) S S S S S S S S"):
        assert token in text20[25], (2020, token)
    for token in ("1.8L 4-cylinder engine with 139 hp", "2.0L 4-cylinder Dynamic Force Engine", "169 hp @ 6600 rpm", "Available 6-speed intelligent Manual Transmission (iMT)", "SE Apex Edition", "XSE Apex Edition", "Hybrid LE"):
        assert token in "\n".join(text21[8:11]), (2021, token)
    for token in ("Electronically controlled Continuously Variable Transmission (ECVT)", "Dynamic-Shift Continuously Variable Transmission (CVT)", "6-speed intelligent Manual Transmission (iMT)", "Front-Wheel Drive (FWD) S S S S S S S S S"):
        assert token in text21[17], (2021, token)

    groups = manifest["families"][0]["groups"]
    assert len(groups) == 19
    assert len({g["id"] for g in groups}) == len(groups)
    assert {y: sum(g["year_from"] == y for g in groups) for y in (2020, 2021)} == {2020: 8, 2021: 11}
    for group in groups:
        assert group["year_from"] == group["year_to"] and group["allowed_drives"] == ["FWD"]
        if group["facts"]["transmission_family"] == "MANUAL" and group["year_from"] == 2021:
            assert group["facts"]["trim"] in ("SE", "SE Apex Edition")
        if group["facts"]["powertrain"] == "HEV":
            assert group["facts"]["trim"] == "Hybrid LE" and group["facts"]["transmission_family"] == "ECVT"
    receipt = {
        "result": "PASS",
        "manifest_compatible_with_base_catalog_batch": True,
        "factory_documents_hash_checked": checked,
        "annual_powertrain_tuples": 19,
        "model_years": {"2020": 8, "2021": 11},
        "body_scope": "US Corolla XII sedan; hatchback excluded",
        "manual_scope_2021": "SE and SE Apex Edition only",
        "db_writes": 0,
    }
    (WORK / "validation-corolla-xii.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Read-only source and schema checks for Corolla/Jetta staging manifest."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.market_priority import base_catalog_batch  # noqa: E402

MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-toyota-vw.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"


def main() -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base_catalog_batch(manifest=value)
    own = json.loads((WORK / "acquisition-receipts.json").read_text(encoding="utf-8"))
    shared = json.loads((ROOT / "deliverables/VerifiedData/base-catalog-acquisition.json").read_text(encoding="utf-8"))
    receipts = {row["url"]: row for row in shared + own if row.get("http_status") == 200}
    found = []
    for key, spec in value["documents"].items():
        receipt = receipts.get(spec["url"])
        assert receipt is not None, ("MISSING_RECEIPT", key)
        raw = (ROOT / ".localdata/verified-source-documents" / receipt["sha256"])
        if not raw.exists():
            raw = ROOT / receipt["path"]
        payload = raw.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == receipt["sha256"], ("HASH", key)
        if spec["format"] == "pdf":
            assert payload.startswith(b"%PDF-"), ("PDF", key)
        found.append(key)
    records = [json.loads(line) for line in (ROOT / "deliverables/VerifiedData/us-ai-verify-09/epa-candidates.jsonl").open(encoding="utf-8")]
    epa = []
    for family in value["families"]:
        for group in family["groups"]:
            match = group.get("epa_drive_match")
            if not match:
                continue
            hits = [
                row for row in records
                if row["master_make"] == family["make"]
                and row["master_model_candidate"] == family["model"]
                and row["model_year"] == group["year_from"]
                and all(row["raw_fields"].get(key) in allowed for key, allowed in match.items())
            ]
            assert len(hits) == 1 and hits[0]["raw_fields"]["drive"] == "Front-Wheel Drive", group["id"]
            epa.append({"group_id": group["id"], "epa_vehicle_id": hits[0]["epa_vehicle_id"]})
    texts = {
        row["name"]: json.loads((ROOT / ".localdata/us-base-catalog-07-source-extracts" / (row["name"] + ".json")).read_text(encoding="utf-8"))
        for row in own if row["media_type"] == "application/pdf"
    }
    for year, page in ((2017, 24), (2018, 20), (2019, 21)):
        content = texts[f"toyota-corolla-{year}"][page]
        for required in (
            "1.8-Liter 4-Cylinder DOHC", "Valvematic technology", "6-speed manual transmission",
            "Continuously Variable Transmission", "Front-Wheel Drive (FWD)",
        ):
            assert required in content, (year, required)
        assert "140 hp" in content and "132 hp" in content, year
    jetta19 = texts["volkswagen-jetta-2019-order-guide"][3]
    for required in ("1.4L TSI", "147 HP", "6-speed manual transmission", "8-speed automatic transmission", "Front-wheel drive"):
        assert required.lower() in jetta19.lower(), required
    count = sum(len(family["groups"]) for family in value["families"])
    keys = [
        (family["id"], group["id"], group["year_from"], drive["drivetrain"])
        for family in value["families"] for group in family["groups"] for drive in group["factory_combinations"]
    ]
    assert count == 32 and len(keys) == len(set(keys)), "CANDIDATE_KEYS"
    receipt = {
        "result": "PASS", "db_writes": 0,
        "manifest_compatible_with_base_catalog_batch": True,
        "factory_documents_hash_checked": len(found),
        "annual_powertrain_tuples": count,
        "epa_full_tuples_for_vw_2016": epa,
        "source_review": "Toyota MY2017/18/19 annual engine-transmission-drive columns; VW MY2019 US order guide direct trim matrix; VW MY2016 OEM inventory plus exact EPA tuples",
    }
    (WORK / "validation.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()

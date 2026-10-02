"""Read-only hash, source, EPA and AI-draft review of Audi A4 8W candidate."""

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

MANIFEST = ROOT / "data/manifests/us-base-catalog-07-source-audi-a4-8w.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EXTRACTS = ROOT / ".localdata/us-base-catalog-07-source-extracts"
EPA = ROOT / ".localdata/epa-bulk-cache"
AI = ROOT / "deliverables/VerifiedData/us-base-catalog-07/ai-work/ai-drafts-07.jsonl"


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def pages(stem: str) -> list[str]:
    return json.loads((EXTRACTS / f"{stem}.json").read_text(encoding="utf-8"))


def main() -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base_catalog_batch(manifest=value)
    receipts = json.loads((WORK / "acquisition-audi-a4.json").read_text(encoding="utf-8"))
    by_url = {row["url"]: row for row in receipts if row.get("http_status") == 200}
    checked = []
    for key, spec in value["documents"].items():
        row = by_url[spec["url"]]
        payload = (ROOT / row["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == row["sha256"], (key, "HASH")
        assert (payload.startswith(b"%PDF-") if spec["format"] == "pdf" else b"<html" in payload[:1000].lower()), (key, "FORMAT")
        checked.append({"document": key, "sha256": row["sha256"], "pages": len(PdfReader(ROOT / row["path"]).pages) if spec["format"] == "pdf" else None})

    brochure = pages("audi-a4-2017-brochure")
    assert "2017" in compact(brochure[0]), "brochure must identify actual MY2017"
    technical = compact(brochure[19])
    for token in ("252", "273", "1984", "sevenspeeds tronic".replace(" ", ""), "frontwheeldrive", "quattroallwheeldrive"):
        assert token in technical, ("BROCHURE", token)
    engines = compact(" ".join(pages("audi-a4-2017-engines")))
    for token in ("dpba", "190hp", "2360lbft", "cymc", "252hp", "273lbft"):
        assert token in engines, ("ENGINES", token)
    manual_release = compact((EXTRACTS / "audi-a4-2017-manual-release.txt").read_text(encoding="utf-8"))
    for token in ("2017audia4", "sixspeedmanual", "quattro", "252hp", "273lbft"):
        assert token in manual_release, ("MANUAL_RELEASE", token)
    price_release = compact((EXTRACTS / "audi-a4-2018-pricing-release.txt").read_text(encoding="utf-8"))
    for token in ("a4sedan20tultrafwds tronic".replace(" ", ""), "a4sedan20tquattros tronic".replace(" ", ""), "a4sedan20tquattromanual"):
        assert token in price_release, ("PRICING_RELEASE", token)
    tires = compact(pages("audi-a4-2018-tire-chart")[0])
    for token in ("a420190hp", "a420252hp"):
        assert token in tires, ("TIRE_CHART", token)
    generation = compact(" ".join(pages("audi-a4-8w-generation")))
    for token in ("a48w", "20172024", "a48k", "20092016"):
        assert token in generation, ("GENERATION", token)

    # Audi Monroney labels are raster-only PDFs. Inspect their private renderings
    # visually; retain only technical observations and hashes, never VIN/dealer data.
    visual = [
        ("audi-a4-2017-ultra-window-label.png", "MY2017 A4 Sedan 2.0T ultra: 190hp/236lb-ft, 7-speed S tronic FWD"),
        ("audi-a4-2018-ultra-window-label.png", "MY2018 A4 Sedan 2.0T ultra: 190hp/236lb-ft, 7-speed S tronic FWD"),
        ("audi-a4-2018-quattro-window-label.png", "MY2018 A4 Sedan 2.0T quattro: 252hp/273lb-ft, 7-speed S tronic AWD"),
    ]
    for filename, _ in visual:
        assert (EXTRACTS / filename).stat().st_size > 10_000, filename

    expected = {
        "38013": (2017, 190, "FWD", "DCT", 7),
        "37302": (2017, 252, "FWD", "DCT", 7),
        "37301": (2017, 252, "AWD", "DCT", 7),
        "38467": (2017, 252, "AWD", "MANUAL", 6),
        "39327": (2018, 190, "FWD", "DCT", 7),
        "38572": (2018, 252, "AWD", "DCT", 7),
    }
    groups = [group for family in value["families"] for group in family["groups"]]
    assert len(groups) == len(expected)
    for group in groups:
        match = re.search(r"vehicles\.csv:id=(\d+)", group["locator"])
        assert match, group["id"]
        year, hp, drive, trans, gears = expected[match.group(1)]
        power = group["facts"]["power_hp"]
        if isinstance(power, dict):
            power = power["value"]
        assert (group["year_from"], group["year_to"], power, group["allowed_drives"], group["facts"]["transmission_family"], group["facts"]["gears"]) == (year, year, hp, [drive], trans, gears), group["id"]
    epa_rows = {}
    for path in EPA.glob("*.jsonl"):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                eid = row.get("epa_vehicle_id")
                if eid in expected and eid not in epa_rows:
                    epa_rows[eid] = row
        if len(epa_rows) == len(expected):
            break
    assert set(epa_rows) == set(expected), ("EPA_ROWS", set(expected) - set(epa_rows))
    for eid, row in epa_rows.items():
        year, _, drive, trans, gears = expected[eid]
        raw = row["raw_fields"]
        assert int(raw["year"]) == year and raw["make"] == "Audi" and raw["displ"] == "2.0"
        assert raw["drive"] == ("All-Wheel Drive" if drive == "AWD" else "Front-Wheel Drive")
        assert raw["trany"] == ("Manual 6-spd" if trans == "MANUAL" else "Automatic (AM-S7)")
        assert raw["model"] != "A4 allroad quattro"

    draft = next(json.loads(line) for line in AI.read_text(encoding="utf-8").splitlines() if '"id": "ai07-36d5e9d9977b45843b"' in line)
    assert draft["provenance"] == "AI_DRAFT" and draft["publication_eligible"] is False
    d = draft["fields"]
    assert (d["make"]["value"], d["model"]["value"], d["model_years"]["value"], d["drivetrain"]["value"], d["transmission_type"]["value"]) == ("Audi", "A4", [2017, 2018], "AWD", "DCT")
    review = {
        "ai_draft_id": draft["id"], "classification": "CORE_HYPOTHESIS_INDEPENDENTLY_VERIFIED_AND_ENRICHED",
        "independent_source_result": "US MY2017–18 A4 8W sedan 2.0L turbo 7-speed S tronic quattro 252hp annual groups verified by Audi-authored year-specific documents and EPA rows; the AI draft itself is not evidence.",
        "new_source_confirmed_variants": ["2017 190hp Ultra FWD 7DCT", "2017 252hp standard FWD 7DCT", "2017 252hp quattro AWD 6MT", "2018 190hp Ultra FWD 7DCT"],
        "held_variant": "MY2018 252hp quattro 6MT was excluded from manifest. Audi annual price list and EPA establish a quattro manual offering; same-year direct factory proof of engine power × manual linkage remains missing.",
        "conflicts": [], "vocabulary_equivalence": "EPA Automatic (AM-S7) versus Audi 7-speed S tronic dual-clutch is not a factory conflict.",
        "ai_draft_published": False, "db_writes": 0,
    }
    (WORK / "review-audi-a4.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "result": "PASS", "manifest_compatible_with_base_catalog_batch": True,
        "audi_us_document_hashes_checked": checked,
        "rasterized_source_pages_visually_reviewed": [{"private_path": str((EXTRACTS / filename).relative_to(ROOT)).replace("\\", "/"), "technical_observation": note} for filename, note in visual],
        "epa_vehicle_ids_checked": list(expected), "annual_powertrain_tuples": 6,
        "model_years": {"2017": 4, "2018": 2}, "allroad_or_s4_counted_as_a4_sedan": False,
        "manual_2018_held": True, "db_writes": 0,
    }
    (WORK / "validation-audi-a4.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"result": result["result"], "tuples": 6, "documents": len(checked), "db_writes": 0}))


if __name__ == "__main__":
    main()

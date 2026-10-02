"""Stage source-confirmed Audi Q7 4M US MY2017–19 powertrain tuples."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/manifests/us-base-catalog-07-source-audi-q7-4m.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"


def document(url: str, year_from: int, year_to: int, locator: str) -> dict:
    return {
        "url": url,
        "source_id": "factory-audi-us",
        "publisher": "Audi of America, Inc.",
        "market": "US",
        "year_from": year_from,
        "year_to": year_to,
        "locator": locator,
        "format": "pdf",
    }


documents = {
    "audi-q7-2017-source07": document(
        "https://www.auto-brochures.com/makes/Audi/Q7/Audi_US%20Q7_2017.pdf",
        2017, 2017,
        "Audi of America US 2017 Q7 brochure PDF p17 (printed pp30–31): Q7 3.0T technical table, 2995cc supercharged V6 333hp/325lb-ft and eight-speed Tiptronic quattro AWD; p14–15 US trim context. This edition does not document a 2017 2.0T.",
    ),
    "audi-q7-2018-source07": document(
        "https://s3.amazonaws.com/cdn.autoipacket.com/brochures/audi/2018/2018.audi.q7.1532617022.005508.pdf",
        2018, 2018,
        "Audi of America US 2018 Q7 brochure PDF p20 rasterized Technical Specifications, individually inspected: 3.0T 2995cc supercharged V6 333hp/325lb-ft and 2.0T 1984cc turbo I4 252hp/273lb-ft, both eight-speed Tiptronic quattro AWD; p18–19 trim/body context.",
    ),
    "audi-q7-2019-source07": document(
        "https://www.auto-brochures.com/makes/Audi/Q7/Audi_US%20Q7_2019.pdf",
        2019, 2019,
        "Audi of America US 2019 Q7 brochure PDF p12 rasterized Technical Specifications, individually inspected: 45 TFSI 2.0T 1984cc turbo I4 248hp/273lb-ft and 55 TFSI 3.0T 2995cc supercharged V6 329hp/325lb-ft, both eight-speed Tiptronic quattro AWD; p11 and p13–14 identify exact US model badges.",
    ),
    "audi-q7-4m-generation-source07": document(
        "https://static.nhtsa.gov/odi/tsbs/2025/MC-11016516-0001.pdf",
        2017, 2019,
        "Audi of America US technical service bulletin 2067804/5 p2 Vehicle data sales types: Q7/Q8 type 4M* MY2017–2019 (among additional years); generation-code identity only, not engine/transmission evidence.",
    ),
}

family = {
    "id": "audi-q7-4m-us-2017-2019-source07",
    "make": "Audi", "model": "Q7", "generation": "4M SUV", "generation_code": "4M",
    "market": "US", "year_from": 2017, "year_to": 2019,
    "local_relevance_tier": 1, "local_generation_year_priority": 1, "source_availability_rank": 1,
    "annual_documents": {
        "2017": ["audi-q7-2017-source07"],
        "2018": ["audi-q7-2018-source07"],
        "2019": ["audi-q7-2019-source07"],
    },
    "generation_documents": ["audi-q7-4m-generation-source07"],
    "scope_note": "Audi-authored US annual brochures establish only five listed Q7 SUV gasoline engine/Tiptronic/quattro combinations. 2017 2.0T is not claimed from this brochure; later years and other markets are excluded.",
    "exclude": [
        "2017 2.0T absent from reviewed annual brochure",
        "Other model years, markets and Q7 4L generation",
        "Unlisted engines, trim packages or gearbox variants",
        "Exact VIN configuration without VIN-specific check",
    ],
    "facts": {
        "body": "SUV", "seats": 7, "powertrain": "ICE", "fuel": "GASOLINE",
        "length_in": {"value": 199.6, "unit": "in"},
        "width_in": {"value": 77.5, "unit": "in"},
        "height_in": {"value": 68.5, "unit": "in"},
        "wheelbase_in": {"value": 117.9, "unit": "in"},
        "fuel_tank_us_gal": {"value": 22.5, "unit": "US gal"},
    },
    "groups": [],
}


def add(year: int, badge: str, liters: float, cc: int, cylinders: int, aspiration: str, hp: int, torque: int, page: int) -> None:
    desc = f"{liters:.1f}L {'turbo inline-4' if cylinders == 4 else 'supercharged V6'} TFSI"
    family["groups"].append({
        "id": f"{year}-{badge.lower().replace(' ', '-')}-quattro",
        "year_from": year, "year_to": year,
        "configuration": f"Q7 {badge} {desc} / 8-speed Tiptronic automatic / quattro AWD",
        "allowed_drives": ["AWD"], "factory_combinations": [{"drivetrain": "AWD"}],
        "locator": f"Audi of America US MY{year} Q7 brochure PDF p{page}, same technical-specifications column: {badge}, {cc}cc {aspiration.lower()} {cylinders}-cylinder, {hp}hp/{torque}lb-ft, eight-speed Tiptronic quattro AWD; seven-seat SUV. No cross-year transfer.",
        "facts": {
            "trim": badge,
            "engine_description": desc,
            "engine_displacement": {"value": liters, "unit": "L"},
            "engine_displacement_cc": cc,
            "cylinders": cylinders,
            "aspiration": aspiration,
            "power_hp": hp,
            "torque_lb_ft": {"value": torque, "unit": "lb-ft"},
            "transmission_description": "8-speed Tiptronic automatic",
            "transmission_family": "AT", "gears": 8,
        },
    })


add(2017, "3.0T", 3.0, 2995, 6, "SUPERCHARGED", 333, 325, 17)
add(2018, "2.0T", 2.0, 1984, 4, "TURBO", 252, 273, 20)
add(2018, "3.0T", 3.0, 2995, 6, "SUPERCHARGED", 333, 325, 20)
add(2019, "45 TFSI", 2.0, 1984, 4, "TURBO", 248, 273, 12)
add(2019, "55 TFSI", 3.0, 2995, 6, "SUPERCHARGED", 329, 325, 12)

manifest = {
    "version": "basic-catalog-07-independent-source-candidate-5",
    "batch_id": "us-base-catalog-07-source-audi-q7-4m",
    "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
    "selection_status": "OWNER_MASTER_LIST_AUDI_US_BROCHURES",
    "epa_document_id": EPA_DOC,
    "documents": documents,
    "families": [family],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
WORK.mkdir(parents=True, exist_ok=True)
summary = {
    "state": "SOURCE_CANDIDATE_UNPUBLISHED", "make": "Audi", "model": "Q7",
    "generation": "4M SUV", "exact_model_years": [2017, 2018, 2019],
    "annual_configurations": {"2017": 1, "2018": 2, "2019": 2},
    "total_annual_configurations": len(family["groups"]),
    "official_audi_us_documents": len(documents), "db_writes": 0,
}
(WORK / "source-candidate-summary-audi-q7.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))

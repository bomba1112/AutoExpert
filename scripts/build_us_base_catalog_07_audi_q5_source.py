"""Stage exact US Audi Q5 FY MY2018–19 gasoline powertrain tuples."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/manifests/us-base-catalog-07-source-audi-q5-fy.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"


def document(url: str, first: int, last: int, locator: str) -> dict:
    return {
        "url": url, "source_id": "factory-audi-us", "publisher": "Audi of America, Inc.",
        "market": "US", "year_from": first, "year_to": last,
        "locator": locator, "format": "pdf",
    }


documents = {
    "audi-q5-2018-source07": document(
        "https://www.auto-brochures.com/makes/Audi/Q5/Audi_US%20Q5_2018.pdf",
        2018, 2018,
        "Audi of America US MY2018 Q5 brochure PDF p18 rasterized Technical Specifications, Q5 (not SQ5) same column: 1984cc turbo I4 252hp/273lb-ft, seven-speed S tronic dual-clutch automatic quattro AWD with ultra technology, five-seat SUV, 111.0in wheelbase/183.6in length/65.3in height.",
    ),
    "audi-q5-2019-source07": document(
        "https://www.auto-brochures.com/makes/Audi/Q5/Audi_US%20Q5_2019.pdf",
        2019, 2019,
        "Audi of America US MY2019 Q5 brochure PDF p10 rasterized Technical Specifications, Q5 (not SQ5) same column: 1984cc turbo I4 248hp/273lb-ft, seven-speed S tronic dual-clutch automatic quattro AWD, five-seat SUV, 111.0in wheelbase/183.6in length/65.3in height. p3 names Q5 45 TFSI badge.",
    ),
    "audi-q5-fy-generation-source07": document(
        "https://static.nhtsa.gov/odi/tsbs/2024/MC-10253261-0001.pdf",
        2018, 2019,
        "Audi of America US technical service bulletin 2017082/14 PDF p2 explicitly lists Q5 (FY) 2018–2024 and prior Q5 (8R) 2009–2017; identity/generation boundary only, not powertrain evidence.",
    ),
}

family = {
    "id": "audi-q5-fy-us-2018-2019-source07",
    "make": "Audi", "model": "Q5", "generation": "FY SUV", "generation_code": "FY",
    "market": "US", "year_from": 2018, "year_to": 2019,
    "local_relevance_tier": 1, "local_generation_year_priority": 1, "source_availability_rank": 1,
    "annual_documents": {
        "2018": ["audi-q5-2018-source07"],
        "2019": ["audi-q5-2019-source07"],
    },
    "generation_documents": ["audi-q5-fy-generation-source07"],
    "scope_note": "Only annual US Q5 2.0T gasoline 7-speed S tronic/quattro entries from the two Audi-authored brochures; MY2018 252hp and MY2019 248hp are not conflated. SQ5 remains outside this model family.",
    "exclude": ["SQ5 and other model lines", "MY2020+ or earlier Q5 8R", "Other markets", "Unlisted engines, transmissions or drivetrain variants", "Exact VIN without VIN-specific check"],
    "facts": {
        "body": "SUV", "seats": 5, "powertrain": "ICE", "fuel": "GASOLINE",
        "length_in": {"value": 183.6, "unit": "in"},
        "height_in": {"value": 65.3, "unit": "in"},
        "wheelbase_in": {"value": 111.0, "unit": "in"},
        "fuel_tank_us_gal": {"value": 18.5, "unit": "US gal"},
    },
    "groups": [],
}


for year, badge, hp, page in ((2018, "2.0T", 252, 18), (2019, "45 TFSI", 248, 10)):
    family["groups"].append({
        "id": f"{year}-{badge.lower().replace(' ', '-')}-quattro",
        "year_from": year, "year_to": year,
        "configuration": f"Q5 {badge} 2.0L turbo TFSI inline-4 / 7-speed S tronic dual-clutch / quattro AWD",
        "allowed_drives": ["AWD"], "factory_combinations": [{"drivetrain": "AWD"}],
        "locator": f"Audi of America US MY{year} Q5 brochure PDF p{page}, Q5 same technical-specifications column, not adjacent SQ5: 1984cc turbo I4 {hp}hp/273lb-ft, seven-speed S tronic dual-clutch automatic and quattro AWD, five-seat SUV.",
        "facts": {
            "trim": badge,
            "engine_description": "2.0L turbo TFSI inline-4",
            "engine_displacement": {"value": 2.0, "unit": "L"},
            "engine_displacement_cc": 1984,
            "cylinders": 4, "aspiration": "TURBO", "power_hp": hp,
            "torque_lb_ft": {"value": 273, "unit": "lb-ft"},
            "transmission_description": "7-speed S tronic dual-clutch automatic",
            "transmission_family": "DCT", "gears": 7,
        },
    })

manifest = {
    "version": "basic-catalog-07-independent-source-candidate-7",
    "batch_id": "us-base-catalog-07-source-audi-q5-fy",
    "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
    "selection_status": "OWNER_MASTER_LIST_AUDI_US_BROCHURES",
    "epa_document_id": EPA_DOC,
    "documents": documents, "families": [family],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
WORK.mkdir(parents=True, exist_ok=True)
summary = {
    "state": "SOURCE_CANDIDATE_UNPUBLISHED", "make": "Audi", "model": "Q5", "generation": "FY SUV",
    "exact_model_years": [2018, 2019], "annual_configurations": {"2018": 1, "2019": 1},
    "total_annual_configurations": len(family["groups"]), "official_audi_us_documents": len(documents), "db_writes": 0,
}
(WORK / "source-candidate-summary-audi-q5.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))

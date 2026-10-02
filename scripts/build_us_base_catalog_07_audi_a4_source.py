"""Stage independently sourced Audi A4 B9/8W US sedan MY2017–18 tuples.

This writes only a candidate manifest and review artifacts, never the live DB.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/manifests/us-base-catalog-07-source-audi-a4-8w.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"


def doc(url: str, year_from: int, year_to: int, locator: str, fmt: str = "pdf") -> dict:
    return {
        "url": url,
        "source_id": "factory-audi-us",
        "publisher": "Audi of America, Inc.",
        "market": "US",
        "year_from": year_from,
        "year_to": year_to,
        "locator": locator,
        "format": fmt,
    }


documents = {
    "audi-a4-2017-brochure-source07": doc(
        "https://salesrater.com/uploads/brochures/2018_Audi_A4.pdf?brochureId=2823",
        2017, 2017,
        "Audi-authored US A4 brochure, cover explicitly says 2017 despite mirror URL basename. PDF p20 technical specification table: A4 2.0T 1984cc 252hp/273lb-ft; 7-speed S tronic dual-clutch with FWD standard, quattro AWD available; sedan 5 seats. Do not apply to Ultra 190hp.",
    ),
    "audi-a4-2017-ultra-source07": doc(
        "https://monroneylabels.com/cars/13678935-2017-audi-a4/window_sticker.pdf?cfl=5247144447",
        2017, 2017,
        "Audi-issued US MY2017 A4 Sedan 2.0T ultra window label; rasterized technical panel visually inspected: 190hp/236lb-ft 2.0T, 7-speed S tronic, FWD. Vehicle/dealer identifiers are not copied into candidate data.",
    ),
    "audi-a4-2017-manual-source07": doc(
        "https://www.autospies.com/iphone/article.aspx?submissionId=89690",
        2017, 2017,
        "Audi of America September 21 2016 MY2017 release republished verbatim: A4 quattro six-speed manual with 2.0 TFSI 252hp/273lb-ft; distinguishes FWD or quattro 7-speed S tronic option.",
        "html",
    ),
    "audi-a4-2017-engines-source07": doc(
        "https://static.nhtsa.gov/odi/tsbs/2016/SB-10105867-2280.pdf",
        2017, 2017,
        "Audi technical training, PDF pp8–9: MY2017 A4 2.0T performance class 1 DPBA 1984cc 190hp/236lb-ft and performance class 2 CYMC 1984cc 252hp/273lb-ft. Applies only to MY2017 group facts here.",
    ),
    "audi-a4-2018-ultra-source07": doc(
        "https://monroneylabels.com/cars/14193012-2018-audi-a4/window_sticker.pdf?cfl=5101225076",
        2018, 2018,
        "Audi-issued US MY2018 A4 Sedan 2.0T ultra window label; rasterized technical panel visually inspected: 190hp/236lb-ft, 7-speed S tronic, FWD. Vehicle/dealer identifiers are not copied.",
    ),
    "audi-a4-2018-quattro-source07": doc(
        "https://monroneylabels.com/cars/3698965-2018-audi-a4/window_sticker.pdf?cfl=3396240023",
        2018, 2018,
        "Audi-issued US MY2018 A4 Sedan 2.0T quattro window label; rasterized technical panel visually inspected: 252hp/273lb-ft, 7-speed S tronic, AWD. Vehicle/dealer identifiers are not copied.",
    ),
    "audi-a4-2018-pricing-source07": doc(
        "https://jomomag.blogspot.com/2017/05/usa-audi-announces-2018-model-year.html",
        2018, 2018,
        "Audi-issued US MY2018 full-line release reproduced on publisher page, model pricing table: A4 sedan 2.0T ultra FWD S tronic; A4 Sedan 2.0T quattro S tronic; A4 Sedan 2.0T quattro manual. Does not by itself assign horsepower to manual.",
        "html",
    ),
    "audi-a4-2018-tire-source07": doc(
        "https://static.nhtsa.gov/odi/tsbs/2017/MC-10128253-9999.pdf",
        2018, 2018,
        "Audi MY2018 US technical tire chart PDF p1 identifies separate A4 2.0 190hp and A4 2.0 252hp variants. It does not assign transmission by itself.",
    ),
    "audi-a4-8w-generation-source07": doc(
        "https://static.nhtsa.gov/odi/tsbs/2024/MC-10253261-0001.pdf",
        2017, 2018,
        "Audi US service bulletin PDF p2 explicitly gives A4 (8W) MY2017–24 versus preceding A4 (8K) MY2009–16; generation identity only.",
    ),
}

family = {
    "id": "audi-a4-8w-sedan-us-2017-2018-source07",
    "make": "Audi", "model": "A4", "generation": "B9 / 8W sedan", "generation_code": "8W",
    "market": "US", "year_from": 2017, "year_to": 2018,
    "local_relevance_tier": 1, "local_generation_year_priority": 1, "source_availability_rank": 1,
    "annual_documents": {},
    "generation_documents": ["audi-a4-8w-generation-source07"],
    "scope_note": "Only US A4 8W sedan annual manufacturer/EPA-linked tuples. 2017 252hp FWD is distinct from 190hp Ultra FWD; no 252hp FWD tuple is inferred for 2018. MY2018 manual remains held because acquired Audi annual documents do not directly link 252hp to manual/quattro on one model-year source.",
    "exclude": ["A4 allroad wagon", "S4/RS4", "A4 8K MY2016 or earlier", "MY2019+", "Other markets", "Unlisted powertrain combinations", "Exact VIN without VIN-specific check"],
    "facts": {"body": "SEDAN", "powertrain": "ICE", "fuel": "GASOLINE"},
    "groups": [],
}


def add(year: int, badge: str, hp: int, torque: int, transmission: str, gears: int, drive: str, epa_id: str, proof: str, annual_docs: list[str], engine_code: str | None = None) -> None:
    manual = transmission == "MANUAL"
    transmission_description = "6-speed manual" if manual else "7-speed S tronic dual-clutch automatic"
    engine_description = f"2.0L turbo TFSI inline-4 {hp}hp"
    facts = {
        "trim": badge,
        "engine_description": engine_description,
        "engine_displacement": {"value": 2.0, "unit": "L"},
        "cylinders": 4,
        "aspiration": "TURBO",
        "power_hp": hp,
        "torque_lb_ft": {"value": torque, "unit": "lb-ft"},
        "transmission_description": transmission_description,
        "transmission_family": transmission,
        "gears": gears,
    }
    if year == 2017:
        facts["engine_displacement_cc"] = {"value": 1984, "document_key": "audi-a4-2017-engines-source07"}
        if engine_code:
            facts["engine_code"] = {"value": engine_code, "document_key": "audi-a4-2017-engines-source07"}
    if year == 2018 and manual:
        # The annual model-line release proves gearbox availability; the
        # contemporaneous factory label and chart separately prove engine spec.
        for key in ("engine_description", "engine_displacement", "cylinders", "aspiration", "power_hp", "torque_lb_ft"):
            existing = facts[key]
            facts[key] = {"value": existing, "document_key": "audi-a4-2018-quattro-source07"} if not isinstance(existing, dict) else {**existing, "document_key": "audi-a4-2018-quattro-source07"}
    family["groups"].append({
        "id": f"{year}-{badge.lower().replace(' ', '-')}-{hp}hp-{drive.lower()}-{gears}{'mt' if manual else 'dct'}",
        "year_from": year, "year_to": year,
        "configuration": f"A4 Sedan {badge} {engine_description} / {transmission_description} / {drive}",
        "allowed_drives": [drive], "factory_combinations": [{"drivetrain": drive}],
        "locator": f"{proof} EPA vehicles.csv:id={epa_id} independently corroborates US MY{year} A4 sedan/base model, 2.0L, {drive}, {'Manual 6-spd' if manual else 'Automatic (AM-S7)'}; EPA vocabulary AM-S7 means Audi's 7-speed automated dual-clutch, not a factory conflict.",
        "epa_drive_match": {
            "model": ["A4 Ultra" if "ultra" in badge.lower() else "A4 quattro" if drive == "AWD" else "A4"],
            "displ": ["2.0"],
            "trany": ["Manual 6-spd" if manual else "Automatic (AM-S7)"],
        },
        "facts": facts,
        "_annual_documents": annual_docs,
    })


add(2017, "2.0T ultra", 190, 236, "DCT", 7, "FWD", "38013", "Audi-issued MY2017 ultra window label, technical panel; Audi technical training PDF p8 DPBA 190hp/236lb-ft.", ["audi-a4-2017-ultra-source07", "audi-a4-2017-engines-source07"], "DPBA")
add(2017, "2.0T", 252, 273, "DCT", 7, "FWD", "37302", "Audi MY2017 A4 brochure PDF p20 performance A4 252hp/273lb-ft with S tronic FWD standard; technical training PDF p9 CYMC.", ["audi-a4-2017-brochure-source07", "audi-a4-2017-engines-source07"], "CYMC")
add(2017, "2.0T quattro", 252, 273, "DCT", 7, "AWD", "37301", "Audi MY2017 A4 brochure PDF p20 performance A4 252hp/273lb-ft, S tronic quattro available; technical training PDF p9 CYMC.", ["audi-a4-2017-brochure-source07", "audi-a4-2017-engines-source07"], "CYMC")
add(2017, "2.0T quattro", 252, 273, "MANUAL", 6, "AWD", "38467", "Audi of America September 2016 MY2017 manual-A4 release explicitly links 252hp/273lb-ft 2.0 TFSI, six-speed manual, quattro AWD; technical training PDF p9 CYMC.", ["audi-a4-2017-manual-source07", "audi-a4-2017-engines-source07"], "CYMC")
add(2018, "2.0T ultra", 190, 236, "DCT", 7, "FWD", "39327", "Audi-issued MY2018 ultra window label, technical panel; 2018 Audi line pricing release separately lists A4 sedan ultra FWD S tronic; Audi 2018 tire chart identifies 190hp A4.", ["audi-a4-2018-ultra-source07", "audi-a4-2018-pricing-source07", "audi-a4-2018-tire-source07"])
add(2018, "2.0T quattro", 252, 273, "DCT", 7, "AWD", "38572", "Audi-issued MY2018 quattro window label, technical panel; 2018 Audi line pricing release lists A4 sedan quattro S tronic; Audi tire chart identifies 252hp A4.", ["audi-a4-2018-quattro-source07", "audi-a4-2018-pricing-source07", "audi-a4-2018-tire-source07"])
# Do not publish a 2018 quattro/manual tuple from a cross-document horsepower
# inference. The Audi price list and EPA establish manual/quattro availability,
# but direct annual factory engine×manual power proof is still missing.

families = []
for group in family["groups"]:
    scoped = copy.deepcopy(family)
    scoped["id"] = family["id"] + "-" + group["id"]
    scoped["year_from"] = group["year_from"]
    scoped["year_to"] = group["year_to"]
    scoped["annual_documents"] = {str(group["year_from"]): group.pop("_annual_documents")}
    scoped["groups"] = [copy.deepcopy(group)]
    families.append(scoped)

manifest = {
    "version": "basic-catalog-07-independent-source-candidate-8",
    "batch_id": "us-base-catalog-07-source-audi-a4-8w",
    "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
    "selection_status": "OWNER_MASTER_LIST_AUDI_US_FACTORY_YEAR_DOCS_EPA",
    "epa_document_id": "761a077a-3298-4796-aaa3-755f7763d69e",
    "documents": documents,
    "families": families,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
WORK.mkdir(parents=True, exist_ok=True)
summary = {
    "state": "SOURCE_CANDIDATE_UNPUBLISHED", "make": "Audi", "model": "A4", "generation": "B9 / 8W sedan",
    "exact_model_years": [2017, 2018], "annual_configurations": {"2017": 4, "2018": 2},
    "total_annual_configurations": 6, "official_audi_us_documents": len(documents), "db_writes": 0,
}
(WORK / "source-candidate-summary-audi-a4.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
hold = {
    "status": "HELD_NOT_PUBLISHED", "make": "Audi", "model": "A4", "generation": "B9 / 8W sedan",
    "market": "US", "model_year": 2018,
    "observed": "Audi MY2018 pricing lists A4 Sedan 2.0T quattro manual; EPA vehicles.csv:id=38573 lists A4 quattro 2.0L AWD Manual 6-spd. Audi MY2018 tire chart has A4 252hp and an Audi 252hp quattro window label exists, but neither explicitly links 252hp to the manual in the same annual configuration.",
    "missing": "Audi-issued MY2018 factory document directly linking manual/quattro with engine power/variant, or another officially verifiable exact factory combination source.",
    "reason": "STRICT_ENGINE_TRANSMISSION_JOINT_APPLICABILITY_NOT_DIRECTLY_PROVEN",
}
(WORK / "held-audi-a4-2018-manual.json").write_text(json.dumps(hold, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))

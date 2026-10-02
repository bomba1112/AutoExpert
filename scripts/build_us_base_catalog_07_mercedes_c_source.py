"""Stage Mercedes-Benz C-Class W205 facelift US sedan MY2019–21 tuples."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/manifests/us-base-catalog-07-source-mercedes-c-w205.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"


def document(url: str, first: int, last: int, locator: str, fmt: str = "pdf") -> dict:
    return {
        "url": url, "source_id": "factory-mercedes-us",
        "publisher": "Mercedes-Benz USA manufacturer brochure" if fmt == "pdf" else "Mercedes-Benz USA Media Newsroom",
        "market": "US", "year_from": first, "year_to": last,
        "locator": locator, "format": fmt,
    }


docs = {
    "mb-c2019-source07": document(
        "https://www.mbusa.com/content/dam/mb-nafta/us/brochures/pdf/MY19_C-Class_WebPDF_181212.pdf",
        2019, 2019,
        "Official MY2019 US brochure PDF p6 sedan model/drive list and p27 C300/C43/C63/C63S specification columns: engine/power/torque/transmission/drivetrain. Sedan only; coupe/cabriolet excluded.",
    ),
    "mb-c2020-source07": document(
        "https://www.mbusa.com/content/dam/mb-nafta/us/brochures/pdf/MY20_C-CLASS_WebPDF_11.14.19.pdf",
        2020, 2020,
        "Official MY2020 US brochure PDF p6 sedan model/drive list and p27 specification columns: C300/C43/C63/C63S engine/power/torque/automatic transmission/drivetrain. Sedan only.",
    ),
    "mb-c2021-source07": document(
        "https://www.mbusa.com/content/dam/mb-nafta/us/brochures/pdf/MY21_C-Class_WebPDF_01132021%20%281%29.pdf",
        2021, 2021,
        "Official MY2021 US brochure PDF p6 sedan model/drive list and p36 specification columns: C300/C43/C63/C63S engine/power/torque/automatic transmission/drivetrain. Sedan only.",
    ),
    "mb-c-w205-facelift-source07": document(
        "https://media.mbusa.com/news/the-2019-mercedes-benz-c-class-sedan",
        2019, 2021,
        "MBUSA 2019 facelift announcement identifies updated C-Class sedan as current generation launched four years earlier and US sale. Existing published W205 family identity retained; 2022 redesign excluded.",
        "html",
    ),
}

family = {
    "id": "mb-cclass-w205-facelift-us-2019-2021-source07",
    "make": "Mercedes-Benz", "model": "C-Class",
    "generation": "W205 sedan (2019 facelift)", "generation_code": "W205",
    "market": "US", "year_from": 2019, "year_to": 2021,
    "local_relevance_tier": 1, "local_generation_year_priority": 1,
    "source_availability_rank": 1,
    "annual_documents": {str(y): [f"mb-c{y}-source07"] for y in (2019, 2020, 2021)},
    "generation_documents": ["mb-c-w205-facelift-source07"],
    "scope_note": "US W205 facelift sedan. Exact MY2019/2020/2021 MBUSA annual brochure model and specification columns. W205 body-code provenance also exists in published earlier-generation catalog; no coupe, cabriolet, wagon or MY2022 extrapolation.",
    "exclude": ["Coupe", "Cabriolet", "Wagon", "Other model years/markets", "Unlisted engines, transmissions or drives"],
    "facts": {"body": "SEDAN", "powertrain": "ICE", "fuel": "GASOLINE"},
    "groups": [],
}

rows = (
    # Grade, displacement, cylinders, power, torque, engine, automatic box, drive.
    ("C 300", 2.0, 4, 255, 273, "2.0L turbo direct-injection inline-4", "9G-TRONIC 9-speed automatic", "RWD"),
    ("C 300 4MATIC", 2.0, 4, 255, 273, "2.0L turbo direct-injection inline-4", "9G-TRONIC 9-speed automatic", "AWD"),
    ("AMG C 43", 3.0, 6, 385, 384, "AMG-enhanced 3.0L V6 biturbo direct injection", "AMG SPEEDSHIFT TCT 9-speed automatic", "AWD"),
    ("AMG C 63", 4.0, 8, 469, 479, "handcrafted AMG 4.0L V8 biturbo direct injection", "AMG SPEEDSHIFT MCT 9-speed automatic", "RWD"),
    ("AMG C 63 S", 4.0, 8, 503, 516, "handcrafted AMG 4.0L V8 biturbo direct injection", "AMG SPEEDSHIFT MCT 9-speed automatic", "RWD"),
)

for year, spec_page in ((2019, 27), (2020, 27), (2021, 36)):
    for trim, displacement, cylinders, power, torque, engine, gearbox, drive in rows:
        ident = f'{year}-{trim.lower().replace(" ", "-")}-{drive.lower()}'
        family["groups"].append({
            "id": ident, "year_from": year, "year_to": year,
            "configuration": f"{trim} sedan / {engine} / {gearbox} / {drive}",
            "allowed_drives": [drive], "factory_combinations": [{"drivetrain": drive}],
            "locator": f"MBUSA MY{year} C-Class US brochure PDF pp6,{spec_page}: {trim} sedan is listed for {drive}; {trim.removesuffix(' 4MATIC')} specification column identifies {engine}, {power} hp, {gearbox} and applicable drivetrain. No body/grade transfer.",
            "facts": {
                "trim": trim,
                "engine_description": engine,
                "engine_displacement": {"value": displacement, "unit": "L"},
                "cylinders": cylinders,
                "aspiration": "TURBO",
                "power_hp": power,
                "torque_lb_ft": {"value": torque, "unit": "lb-ft"},
                "transmission_family": "AT",
                "transmission_description": gearbox,
                "gears": 9,
            },
        })

manifest = {
    "version": "basic-catalog-07-independent-source-candidate-3",
    "batch_id": "us-base-catalog-07-source-mercedes-c-w205",
    "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
    "selection_status": "OWNER_MASTER_LIST_OFFICIAL_MBUSA_ANNUAL_SPEC_COLUMNS",
    "epa_document_id": EPA_DOC,
    "documents": docs, "families": [family],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
WORK.mkdir(parents=True, exist_ok=True)
summary = {
    "state": "SOURCE_CANDIDATE_UNPUBLISHED", "make": "Mercedes-Benz", "model": "C-Class",
    "generation": "W205 sedan (2019 facelift)", "model_years": [2019, 2020, 2021],
    "annual_configurations_per_year": 5, "total_annual_configurations": len(family["groups"]),
    "manufacturer_documents": len(docs), "ai_draft_publication": 0, "db_writes": 0,
}
(WORK / "source-candidate-summary-mercedes-c.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))

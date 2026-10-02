"""Stage the Toyota Corolla XII MY2020–21 US sedan tuples without DB writes."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/manifests/us-base-catalog-07-source-toyota-corolla-xii.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"


def document(url: str, start: int, end: int, locator: str, fmt: str = "pdf") -> dict:
    return {
        "url": url,
        "source_id": "factory-toyota-us",
        "publisher": "Toyota manufacturer-authored US brochure" if fmt == "pdf" else "Toyota USA Newsroom",
        "market": "US",
        "year_from": start,
        "year_to": end,
        "locator": locator,
        "format": fmt,
    }


documents = {
    "corolla-xii-2020-source07": document(
        "https://www.auto-brochures.com/makes/Toyota/Corolla/Toyota_US%20Corolla_2020-3.pdf",
        2020, 2020,
        "PDF pp17–19: annual trim powertrain descriptions; p26: exact eight-column transmission/FWD matrix and seating capacity. Sedan scope; hatchback excluded.",
    ),
    "corolla-xii-2021-source07": document(
        "https://www.auto-brochures.com/makes/Toyota/Corolla/Toyota_US%20Corolla_2021.pdf",
        2021, 2021,
        "PDF pp9–11: annual trim engine and transmission applicability, including SE and SE Apex optional 6MT; p18: nine-column standard/optional transmission and FWD matrix.",
    ),
    "corolla-xii-generation-source07": document(
        "https://pressroom.toyota.com/all-new-2020-toyota-corolla-ready-to-rock-the-sedan-world/",
        2020, 2021,
        "Toyota USA announcement calls the all-new MY2020 Corolla sedan twelfth generation. Annual brochures establish MY2020 and MY2021 configurations separately; no adjacent-year transfer.",
        "html",
    ),
}

family = {
    "id": "toyota-corolla-xii-us-2020-2021-source07",
    "make": "Toyota",
    "model": "Corolla",
    "generation": "XII sedan (TNGA)",
    "generation_code": "XII",
    "market": "US",
    "year_from": 2020,
    "year_to": 2021,
    "local_relevance_tier": 1,
    "local_generation_year_priority": 1,
    "source_availability_rank": 1,
    "annual_documents": {"2020": ["corolla-xii-2020-source07"], "2021": ["corolla-xii-2021-source07"]},
    "generation_documents": ["corolla-xii-generation-source07"],
    "scope_note": "US Corolla XII sedan only. Each model year, grade, engine, transmission and FWD tuple is taken from its own Toyota manufacturer brochure; no hatchback or adjacent-year inheritance.",
    "exclude": ["Corolla hatchback", "Other model years or markets", "Unlisted engine, transmission, body or grade", "6MT on SE Nightshade, XSE or Hybrid LE"],
    "facts": {"body": "SEDAN", "seats": 5, "fuel": "GASOLINE", "cylinders": 4},
    "groups": [],
}


def add(year: int, trim: str, displacement: float, hp: int | None, transmission: str, locator: str) -> None:
    hybrid = trim == "Hybrid LE"
    manual = transmission == "iMT 6-speed manual"
    if hybrid:
        engine = "1.8L 4-cylinder Hybrid Synergy Drive"
        family_name = "ECVT"
        trans_description = "electronically controlled continuously variable transmission (ECVT)"
    elif displacement == 1.8:
        engine = "1.8L 4-cylinder naturally aspirated gasoline"
        family_name = "CVT"
        trans_description = "CVTi-S continuously variable transmission" if year == 2020 else "continuously variable transmission (CVT)"
    elif manual:
        engine = "2.0L 4-cylinder Dynamic Force gasoline"
        family_name = "MANUAL"
        trans_description = "6-speed intelligent manual transmission (iMT)"
    else:
        engine = "2.0L 4-cylinder Dynamic Force gasoline"
        family_name = "CVT"
        trans_description = "Dynamic-Shift continuously variable transmission (CVT)"
    fields = {
        "trim": trim,
        "powertrain": "HEV" if hybrid else "ICE",
        "engine_description": engine,
        "engine_displacement": {"value": displacement, "unit": "L"},
        "aspiration": "NATURALLY_ASPIRATED",
        "transmission_family": family_name,
        "transmission_description": trans_description,
    }
    if hp is not None:
        fields["power_hp"] = hp
    if manual:
        fields["gears"] = 6
    group_id = f"{year}-{trim.lower().replace(' ', '-').replace('/', '-')}-{family_name.lower()}"
    family["groups"].append({
        "id": group_id,
        "year_from": year,
        "year_to": year,
        "configuration": f"Corolla {trim} {displacement} / {transmission} / FWD",
        "allowed_drives": ["FWD"],
        "factory_combinations": [{"drivetrain": "FWD"}],
        "locator": locator,
        "facts": fields,
    })


for trim in ("L", "LE", "XLE"):
    add(2020, trim, 1.8, 139, "CVTi-S CVT", f"Toyota Corolla MY2020 US brochure PDF pp17,26: {trim} 1.8L 139 hp/CVT/FWD; exact same grade column in p26.")
add(2020, "SE", 2.0, 169, "iMT 6-speed manual", "Toyota Corolla MY2020 US brochure PDF pp18,26: SE 6MT grade 2.0L 169 hp/intelligent 6MT/FWD.")
for trim in ("SE", "SE Nightshade Edition", "XSE"):
    add(2020, trim, 2.0, 169, "Dynamic-Shift CVT", f"Toyota Corolla MY2020 US brochure PDF pp18–19,26: {trim} 2.0L 169 hp/Dynamic-Shift CVT/FWD; exact p26 grade column.")
add(2020, "Hybrid LE", 1.8, None, "ECVT", "Toyota Corolla MY2020 US brochure PDF pp19,26: Hybrid LE 1.8L Hybrid Synergy Drive/ECVT/FWD. Power omitted because this annual brochure does not state a clear net-system rating.")

for trim in ("L", "LE", "XLE"):
    add(2021, trim, 1.8, 139, "CVT", f"Toyota Corolla MY2021 US brochure PDF pp9,18: {trim} inherited 1.8L 139 hp/CVT/FWD from L; annual grade matrix confirms same column.")
for trim in ("SE", "SE Nightshade Edition", "SE Apex Edition", "XSE", "XSE Apex Edition"):
    add(2021, trim, 2.0, 169, "Dynamic-Shift CVT", f"Toyota Corolla MY2021 US brochure PDF pp10–11,18: {trim} 2.0L 169 hp/Dynamic-Shift CVT/FWD; annual grade matrix marks CVT standard.")
for trim in ("SE", "SE Apex Edition"):
    add(2021, trim, 2.0, 169, "iMT 6-speed manual", f"Toyota Corolla MY2021 US brochure PDF pp10,18: {trim} 2.0L 169 hp/optional 6-speed intelligent manual/FWD; annual grade matrix marks 6MT optional only in this column.")
add(2021, "Hybrid LE", 1.8, None, "ECVT", "Toyota Corolla MY2021 US brochure PDF pp11,18: Hybrid LE 1.8L hybrid/ECVT/FWD. Brochure's '121 hp' phrasing is not promoted to a net-system fact.")

manifest = {
    "version": "basic-catalog-07-independent-source-candidate-2",
    "batch_id": "us-base-catalog-07-source-toyota-corolla-xii",
    "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
    "selection_status": "OWNER_MASTER_LIST_INDEPENDENT_MANUFACTURER_US_TABLES",
    "epa_document_id": EPA_DOC,
    "documents": documents,
    "families": [family],
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
WORK.mkdir(parents=True, exist_ok=True)
summary = {
    "state": "SOURCE_CANDIDATE_UNPUBLISHED",
    "make": "Toyota", "model": "Corolla", "generation": "XII sedan (TNGA)",
    "model_years": [2020, 2021],
    "annual_configurations": {"2020": 8, "2021": 11},
    "total_annual_configurations": len(family["groups"]),
    "exact_us_source_documents": len(documents),
    "ai_draft_publication": 0, "db_writes": 0,
}
(WORK / "source-candidate-summary-corolla-xii.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))

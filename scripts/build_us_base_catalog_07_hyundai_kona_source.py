"""Stage Hyundai Kona OS US MY2018–19 trim/powertrain/drivetrain rows."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/manifests/us-base-catalog-07-source-hyundai-kona-os.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"


def document(url: str, first: int, last: int, locator: str, fmt: str) -> dict:
    return {
        "url": url, "source_id": "factory-hyundai-us", "publisher": "Hyundai Motor America",
        "market": "US", "year_from": first, "year_to": last,
        "locator": locator, "format": fmt,
    }


documents = {
    "hyundai-kona-2018-pricing-source07": document(
        "https://www.prnewswire.com/news-releases/2018-hyundai-kona-suv-pricing-released-a-crossover-for-urban-adventurers-300590920.html",
        2018, 2018,
        "Hyundai Motor America-authored Jan. 31, 2018 US 2018 Kona pricing release, '2018 HYUNDAI KONA PRICING' table: SE/SEL 2.0L six-speed SHIFTRONIC FWD/AWD; Limited/Ultimate 1.6L Turbo seven-speed EcoShift DCT FWD/AWD. Contrast roof is an SEL package, not another powertrain.",
        "html",
    ),
    "hyundai-kona-2019-pricing-source07": document(
        "https://www.prnewswire.com/news-releases/hyundai-announces-pricing-for-2019-kona-300723441.html",
        2019, 2019,
        "Hyundai Motor America-authored Oct. 3, 2018 US 2019 Kona release, '2019 Hyundai Kona Pricing' table: SE/SEL 2.0L six-speed SHIFTRONIC FWD/AWD; Limited/Ultimate 1.6L Turbo seven-speed EcoShift DCT FWD/AWD. MY2019 later Iron Man edition is outside this edition's reviewed table.",
        "html",
    ),
    "hyundai-kona-os-generation-source07": document(
        "https://static.nhtsa.gov/odi/tsbs/2023/MC-10233547-0001.pdf",
        2018, 2019,
        "Hyundai Motor America TSB 23-01-014H-2 PDF p9, ROM ID model-year table explicitly labels 'Kona (OS)' and '2018 - 2022'; generation-code identity only, not engine or transmission evidence.",
        "pdf",
    ),
}

family = {
    "id": "hyundai-kona-os-us-2018-2019-source07",
    "make": "Hyundai", "model": "Kona", "generation": "OS SUV", "generation_code": "OS",
    "market": "US", "year_from": 2018, "year_to": 2019,
    "local_relevance_tier": 1, "local_generation_year_priority": 1, "source_availability_rank": 1,
    "annual_documents": {
        "2018": ["hyundai-kona-2018-pricing-source07"],
        "2019": ["hyundai-kona-2019-pricing-source07"],
    },
    "generation_documents": ["hyundai-kona-os-generation-source07"],
    "scope_note": "Hyundai Motor America US MY2018/19 annual launch/pricing tables directly pair standard trim, 2.0L or 1.6L Turbo engine, SHIFTRONIC AT or EcoShift DCT, and FWD/AWD. No engine-family code or horsepower claimed without separate applicable factory evidence.",
    "exclude": [
        "Other model years or markets", "Kona Electric and later N variants",
        "2018 SEL contrast-roof appearance package as separate powertrain",
        "2019 Iron Man edition absent from reviewed October 2018 release",
        "Exact VIN configuration without VIN-specific check",
    ],
    "facts": {"body": "SUV", "powertrain": "ICE", "fuel": "GASOLINE"},
    "groups": [],
}


def add(year: int, trim: str, drive: str) -> None:
    base = trim in {"SE", "SEL"}
    engine = "2.0L inline-4" if base else "1.6L turbo inline-4"
    box = "6-speed SHIFTRONIC automatic" if base else "7-speed EcoShift dual-clutch"
    family["groups"].append({
        "id": f"{year}-{trim.lower()}-{drive.lower()}",
        "year_from": year, "year_to": year,
        "configuration": f"Kona {trim} {engine} / {box} / {drive}",
        "allowed_drives": [drive], "factory_combinations": [{"drivetrain": drive}],
        "locator": f"Hyundai Motor America MY{year} Kona launch/pricing release, annual model/engine/transmission/drivetrain table, {trim} {drive} same row: {engine}, {box}. SUV gasoline. Do not transfer trim/engine pairing between years.",
        "facts": {
            "trim": trim,
            "engine_description": engine,
            "engine_displacement": {"value": 2.0 if base else 1.6, "unit": "L"},
            "cylinders": 4,
            **({"aspiration": "TURBO"} if not base else {}),
            "transmission_description": box,
            "transmission_family": "AT" if base else "DCT",
            "gears": 6 if base else 7,
        },
    })


for year in (2018, 2019):
    for trim in ("SE", "SEL", "Limited", "Ultimate"):
        for drive in ("FWD", "AWD"):
            add(year, trim, drive)

manifest = {
    "version": "basic-catalog-07-independent-source-candidate-6",
    "batch_id": "us-base-catalog-07-source-hyundai-kona-os",
    "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
    "selection_status": "OWNER_MASTER_LIST_HYUNDAI_US_ISSUER_RELEASES",
    "epa_document_id": EPA_DOC,
    "documents": documents, "families": [family],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
WORK.mkdir(parents=True, exist_ok=True)
summary = {
    "state": "SOURCE_CANDIDATE_UNPUBLISHED", "make": "Hyundai", "model": "Kona",
    "generation": "OS SUV", "exact_model_years": [2018, 2019],
    "annual_configurations": {"2018": 8, "2019": 8},
    "total_annual_configurations": len(family["groups"]),
    "official_hyundai_us_issuer_documents": len(documents), "db_writes": 0,
}
(WORK / "source-candidate-summary-hyundai-kona.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))

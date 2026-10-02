"""Source-reviewed Lexus GX 460 US MY2017-2019 annual factory tuple packet."""
# ruff: noqa: E501

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/manifests/us-base-catalog-07-source-lexus-gx-2017-2019.json"
REVIEW = ROOT / "deliverables/VerifiedData/us-base-catalog-07/lexus-gx-source-review.json"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"


def fact(value, unit=None):
    return {"value": value, **({"unit": unit} if unit else {})}


docs = {
    f"gx-{year}-us-source07": {
        "url": f"https://www.auto-brochures.com/makes/lexus/GX/Lexus_US%20GX_{year}.pdf",
        "source_id": "factory-lexus-us",
        "publisher": "Lexus USA",
        "market": "US",
        "year_from": year,
        "year_to": year,
        "locator": (
            f"Lexus-authored US GX {year} brochure, PDF pp2 and 18 (zero-based): GX 460 4.6L V8, "
            "301 hp/329 lb-ft, six-speed automatic/full-time 4WD, annual GX/GX Premium/GX Luxury "
            "feature columns, dimensions and 15/18/16 EPA estimates."
        ),
        "format": "pdf",
    }
    for year in (2017, 2018, 2019)
}
docs["gx-second-gen-lineage-source07"] = {
    "url": "https://pressroom.lexus.com/lexus-introduces-second-generation-gx-460-luxury-suv-for-2010/",
    "source_id": "factory-lexus-us",
    "publisher": "Lexus USA Newsroom",
    "market": "US",
    "year_from": 2017,
    "year_to": 2019,
    "locator": (
        "Generation lineage only: Lexus introduced the second-generation GX 460 for MY2010; "
        "the MY2017-2019 annual Lexus brochures identify continued GX 460 US model identity. "
        "This 2010 release is not used to transfer 2010 technical values."
    ),
    "format": "html",
}

groups = []
for label, suffix, wheels, height in (
    ("GX 460", "base", "18-inch six-spoke alloy", 74.2),
    ("GX 460 Premium", "premium", "18-inch split-six-spoke alloy", 74.2),
    ("GX 460 Luxury", "luxury", "18-inch split-six-spoke alloy, Liquid Graphite finish", 73.8),
):
    facts = {
        "trim": label,
        "wheels": wheels,
        "height_in": fact(height, "in"),
    }
    if suffix == "base":
        facts["seats"] = 7
    if suffix == "luxury":
        facts["suspension"] = "Adaptive Variable Suspension; auto-leveling rear air suspension"
    groups.append(
        {
            "id": f"gx-460-{suffix}",
            "year_from": 2017,
            "year_to": 2019,
            "configuration": f"{label} US MY2017-2019",
            "allowed_drives": ["4WD"],
            "factory_combinations": [{"drivetrain": "4WD"}],
            "epa_drive_match": {
                "model": ["GX 460"],
                "displ": ["4.6"],
                "trany": ["Automatic (S6)"],
            },
            "locator": (
                "Lexus USA MY2017/2018/2019 GX brochures PDF p18: each annual features/specification "
                f"table explicitly lists {label} with 4.6L V8, six-speed automatic, full-time 4WD; "
                "same annual page for trim-specific equipment and dimensions. "
                "EPA vehicles.csv exact annual GX 460 4.6L Automatic(S6) 4WD tuple corroborates drive."
            ),
            "facts": facts,
        }
    )

manifest = {
    "version": "basic-catalog-07-independent-source-candidate-lexus-gx-1",
    "batch_id": "us-base-catalog-07-source-lexus-gx-2017-2019",
    "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
    "selection_status": "OWNER_MASTER_LIST_LEXUS_US_ANNUAL_BROCHURES",
    "epa_document_id": EPA_DOC,
    "documents": docs,
    "families": [
        {
            "id": "lexus-gx-ii-us-2017-2019-source07",
            "make": "Lexus",
            "model": "GX",
            "generation": "II (2010 redesign)",
            "generation_code": None,
            "market": "US",
            "year_from": 2017,
            "year_to": 2019,
            "local_relevance_tier": 1,
            "local_generation_year_priority": 1,
            "source_availability_rank": 1,
            "annual_documents": {
                str(year): [f"gx-{year}-us-source07"] for year in (2017, 2018, 2019)
            },
            "generation_documents": ["gx-second-gen-lineage-source07"],
            "scope_note": (
                "Only Lexus USA annual GX 460, Premium, Luxury grade tuples for MY2017-2019. "
                "Sport Design is an optional package, not a separate grade. Seating is recorded "
                "only for the unambiguous standard GX 460 base; optional second-row captain's "
                "chairs change Premium/Luxury capacity."
            ),
            "exclude": [
                "MY2014-2016 already published and not reimported",
                "Other years, markets, packages, and unlisted engine/transmission tuples",
                "Premium/Luxury seven-seat assertions without option-level confirmation",
                "Exact VIN identity without VIN-specific confirmation",
            ],
            "facts": {
                "body": "SUV",
                "powertrain": "ICE",
                "fuel": "GASOLINE",
                "engine_description": "GX 460 4.6L V8",
                "engine_displacement": fact(4.6, "L"),
                "cylinders": 8,
                "power_hp": 301,
                "torque_lb_ft": fact(329, "lb-ft"),
                "transmission_family": "AT",
                "transmission_description": "6-speed automatic",
                "gears": 6,
                "length_in": fact(192.1, "in"),
                "width_in": fact(74.2, "in"),
                "wheelbase_in": fact(109.8, "in"),
                "epa_city_mpg": fact(15, "US mpg"),
                "epa_highway_mpg": fact(18, "US mpg"),
                "epa_combined_mpg": fact(16, "US mpg"),
            },
            "groups": groups,
        }
    ],
}
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
REVIEW.write_text(
    json.dumps(
        {
            "review_status": "SOURCE_REVIEWED_NOT_PUBLISHED",
            "schema_validation": "CatalogRecord.model_validate PASS: 9 annual rows; no DB writes",
            "live_scope_before": {
                "Lexus GX US MY2014-2016": "9 existing BASE_READY trim-year rows",
                "Lexus GX US MY2017-2019": "0 existing BASE_READY trim-year rows",
            },
            "new_candidate_rows": 9,
            "exact_annual_rows": [
                f"{year} | {trim} | 4.6L V8 | 6AT | full-time 4WD"
                for year in (2017, 2018, 2019)
                for trim in ("GX 460", "GX 460 Premium", "GX 460 Luxury")
            ],
            "epa_exact_annual_ids": {"2017": "38077", "2018": "39406", "2019": "40680"},
            "holds": [
                "Premium/Luxury seating varies with second-row captain's-chair package, so no seven-seat fact is asserted for these grades.",
                "MY2017 Luxury standard captain's chairs are reported by Lexus USA; optional substitutions were not fully reviewed, so capacity omitted.",
                "Sport Design remains an option package, not a separate powertrain/grade row.",
                "J150 platform code was not established from reviewed Lexus USA primary material; generation_code remains null.",
                "Pressroom annual HTML returned HTTP403 to local acquisition; annual primary evidence is Lexus-authored brochure PDFs, with receipts SHA256 and HTTP200.",
            ],
            "source_urls": [spec["url"] for spec in docs.values()],
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps({"manifest": str(OUT.relative_to(ROOT)), "families": 1, "rows": 9}))

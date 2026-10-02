"""Stage source-confirmed BMW X1 F48 US MY2016–18 and MY2020 tuples."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/manifests/us-base-catalog-07-source-bmw-x1-f48.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"


def document(url: str, first: int, last: int, locator: str, fmt: str) -> dict:
    return {
        "url": url, "source_id": "factory-bmw-us", "publisher": "BMW Group PressClub USA",
        "market": "US", "year_from": first, "year_to": last,
        "locator": locator, "format": fmt,
    }


docs = {
    "bmw-x1-2016-launch-source07": document(
        "https://www.press.bmwgroup.com/usa/article/detail/T0220582EN_US/the-all-new-bmw-x1",
        2016, 2018,
        "BMW Group USA launch release explicitly identifies second-generation F48 US MY2016 xDrive28i as launch variant, 2.0L TwinPower Turbo 228 hp/258 lb-ft, 8-speed Steptronic AWD; inline technical table gives seats and dimensions. Generation identity supports subsequent annual US sheets, not technical year transfer.",
        "html",
    ),
    "bmw-x1-2017-tech-source07": document(
        "https://www.press.bmwgroup.com/usa/article/attachment/T0220582EN_US/391951",
        2017, 2017,
        "BMW USA 2017 X1 Technical Data PDF pp1–2, same-column sDrive28i/xDrive28i: FWD/AWD, 5 seats, B46A20O0 1998cc 228hp/258lb-ft, Aisin F22 8-speed automatic, dimensions.",
        "pdf",
    ),
    "bmw-x1-2018-tech-source07": document(
        "https://www.press.bmwgroup.com/usa/article/attachment/T0220582EN_US/391953",
        2018, 2018,
        "BMW USA 2018 X1 Technical Data PDF pp1–2, same-column sDrive28i/xDrive28i: FWD/AWD, 5 seats, B46A20O0 1998cc 228hp/258lb-ft, Aisin F22 8-speed automatic, dimensions.",
        "pdf",
    ),
    "bmw-x1-2020-update-source07": document(
        "https://www.press.bmwgroup.com/usa/article/detail/T0296549EN_US/the-2020-bmw-x1-sports-activity-vehicle",
        2020, 2020,
        "BMW Group USA MY2020 facelift release and inline two-column technical specification table: sDrive28i FWD/xDrive28i AWD, 5 seats, B46A20O1 1998cc 228hp/258lb-ft, GA8Y45EW 8-speed Steptronic automatic, dimensions.",
        "html",
    ),
}


def family(ident: str, first: int, last: int, annual: dict, generation_docs: list[str], note: str) -> dict:
    return {
        "id": ident, "make": "BMW", "model": "X1", "generation": "F48 SAV", "generation_code": "F48",
        "market": "US", "year_from": first, "year_to": last,
        "local_relevance_tier": 1, "local_generation_year_priority": 1, "source_availability_rank": 1,
        "annual_documents": annual, "generation_documents": generation_docs,
        "scope_note": note,
        "exclude": ["Other model years, especially MY2019", "Other markets", "E84/U11 X1", "Unlisted engines or transmissions"],
        "facts": {
            "body": "SUV", "seats": 5, "powertrain": "ICE", "fuel": "GASOLINE",
            "engine_description": "2.0L BMW TwinPower Turbo inline-4",
            "engine_displacement": {"value": 2.0, "unit": "L"},
            "cylinders": 4, "aspiration": "TURBO", "power_hp": 228,
            "torque_lb_ft": {"value": 258, "unit": "lb-ft"},
            "transmission_family": "AT", "gears": 8,
        },
        "groups": [],
    }


def add(row: dict, year: int, trim: str, drive: str, engine_code: str | None, box_code: str | None, dims: tuple[float, float, float], locator: str) -> None:
    fields = {
        "trim": trim,
        "transmission_description": "8-speed Steptronic automatic",
        "length_in": {"value": dims[0], "unit": "in"},
        "width_in": {"value": dims[1], "unit": "in"},
        "wheelbase_in": {"value": dims[2], "unit": "in"},
    }
    if engine_code:
        fields["engine_code"] = engine_code
    if box_code:
        fields["transmission_code"] = box_code
    row["groups"].append({
        "id": f"{year}-{trim.lower()}-{drive.lower()}",
        "year_from": year, "year_to": year,
        "configuration": f"X1 {trim} 2.0L TwinPower Turbo / 8-speed Steptronic / {drive}",
        "allowed_drives": [drive], "factory_combinations": [{"drivetrain": drive}],
        "locator": locator,
        "facts": fields,
    })


early = family(
    "bmw-x1-f48-us-2016-2018-source07", 2016, 2018,
    {"2016": ["bmw-x1-2016-launch-source07"], "2017": ["bmw-x1-2017-tech-source07"], "2018": ["bmw-x1-2018-tech-source07"]},
    ["bmw-x1-2016-launch-source07"],
    "US BMW X1 F48 MY2016 launch xDrive28i, then exact two-column US annual MY2017/18 technical sheets. 2016 sDrive not asserted; no MY2019 extrapolation.",
)
add(early, 2016, "xDrive28i", "AWD", "B46", "Aisin F22", (175.4, 71.7, 105.1),
    "BMW Group USA all-new 2016 X1 release: second-generation F48, US launch xDrive28i only; inline spec table B46 1998cc 228hp/258lb-ft and Aisin F22 8-speed AWD, 5 seats and dimensions. Do not infer MY2016 sDrive.")
for year in (2017, 2018):
    for trim, drive in (("sDrive28i", "FWD"), ("xDrive28i", "AWD")):
        add(early, year, trim, drive, "B46A20O0", "Aisin F22", (175.4, 71.7, 105.1),
            f"BMW Group USA MY{year} X1 F48 Technical Data PDF pp1–2, {trim} same column: {drive}, 5 seats, B46A20O0 1998cc/228hp/258lb-ft, Aisin F22 8-speed automatic. No MY2019 transfer.")

facelift = family(
    "bmw-x1-f48-us-2020-source07", 2020, 2020,
    {"2020": ["bmw-x1-2020-update-source07"]}, ["bmw-x1-2020-update-source07"],
    "US BMW X1 F48 MY2020 facelift; manufacturer release contains annual two-column sDrive28i/xDrive28i table. MY2019 intentionally absent.",
)
for trim, drive in (("sDrive28i", "FWD"), ("xDrive28i", "AWD")):
    add(facelift, 2020, trim, drive, "B46A20O1", "GA8Y45EW", (175.5, 71.7, 105.1),
        f"BMW Group USA 2020 X1 update release inline Technical Specifications table: {trim} {drive}, 5 seats, B46A20O1 1998cc/228hp/258lb-ft and GA8Y45EW 8-speed Steptronic automatic. Dimensions are same-column values; MY2019 not claimed.")

manifest = {
    "version": "basic-catalog-07-independent-source-candidate-4",
    "batch_id": "us-base-catalog-07-source-bmw-x1-f48",
    "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
    "selection_status": "OWNER_MASTER_LIST_BMW_US_TECH_SHEETS",
    "epa_document_id": EPA_DOC,
    "documents": docs, "families": [early, facelift],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
WORK.mkdir(parents=True, exist_ok=True)
summary = {
    "state": "SOURCE_CANDIDATE_UNPUBLISHED", "make": "BMW", "model": "X1", "generation": "F48 SAV",
    "exact_model_years": [2016, 2017, 2018, 2020],
    "unverified_gap_years": [2019],
    "annual_configurations": {"2016": 1, "2017": 2, "2018": 2, "2020": 2},
    "total_annual_configurations": sum(len(x["groups"]) for x in manifest["families"]),
    "official_bmw_us_documents": len(docs), "ai_draft_publication": 0, "db_writes": 0,
}
(WORK / "source-candidate-summary-bmw-x1.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))

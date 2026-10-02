"""Serialize independently reviewed factory GX/FX tables; no AI draft input."""
# ruff: noqa: E501

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fact(value, unit=None, **kwargs):
    return {"value": value, **({"unit": unit} if unit else {}), **kwargs}


def doc(url, make, first, last, locator, fmt="pdf"):
    return dict(
        url=url,
        source_id=f"factory-{make}-us",
        publisher=f"{make.title()} manufacturer-authored US material",
        market="US",
        year_from=first,
        year_to=last,
        locator=locator,
        format=fmt,
    )


def family(id, make, model, generation, code, first, last, annual, gen):
    return dict(
        id=id,
        make=make,
        model=model,
        market="US",
        generation=generation,
        generation_code=code,
        year_from=first,
        year_to=last,
        local_relevance_tier=1,
        local_generation_year_priority=1,
        source_availability_rank=1,
        annual_documents=annual,
        generation_documents=gen,
        scope_note="Only explicit annual US factory engine/transmission/drive/trim tuples. No adjacent-year extrapolation.",
        exclude=["Unlisted years, bodies, trims and markets"],
        facts={},
        groups=[],
    )


def group(id, trim, first, last, drives, fields, locator):
    return dict(
        id=id,
        year_from=first,
        year_to=last,
        configuration=trim,
        allowed_drives=drives,
        factory_combinations=[dict(drivetrain=x) for x in drives],
        locator=locator,
        facts={"trim": trim, **fields},
    )


m = dict(
    version="basic-catalog-9-root-source",
    batch_id="us-ai-verify-09-root",
    selection_status="OWNER_MASTER_LIST_SOURCE_FIRST",
    epa_document_id="761a077a-3298-4796-aaa3-755f7763d69e",
    documents={},
    families=[],
)
for y in (2014, 2015, 2016):
    m["documents"][f"gx-{y}-09"] = doc(
        f"https://www.auto-brochures.com/makes/lexus/GX/Lexus_US%20GX_{y}.pdf",
        "lexus",
        y,
        y,
        f"Annual US GX brochure PDF p2 and p{19 if y == 2016 else 11}; printed specifications and trim columns, footnotes retained; visual table review.",
    )
m["documents"]["gx-generation-09"] = doc(
    "https://pressroom.lexus.com/lexus-introduces-second-generation-gx-460-luxury-suv-for-2010/",
    "lexus",
    2014,
    2016,
    "Generation lineage only: manufacturer introduces second-generation GX460 MY2010. Joined to annual MY2014/15/16 GX460 and manufacturer chronology ending generation at third-generation launch2023. No 2010 technical values transferred.",
    "html",
)
m["documents"]["gx-chronology-09"] = doc(
    "https://pressroom.lexus.com/history-lexus/",
    "lexus",
    2014,
    2016,
    "Generation-lineage cross-check: 2023 third-generation GX launch; annual GX460 documents establish scoped years. J150 code not claimed.",
    "html",
)
gx = family(
    "lexus-gx-ii-us-2014-2016-09",
    "Lexus",
    "GX",
    "II (2010 redesign)",
    None,
    2014,
    2016,
    {str(y): [f"gx-{y}-09"] for y in (2014, 2015, 2016)},
    ["gx-generation-09", "gx-chronology-09"],
)
gx["facts"] = {
    "body": "SUV",
    "powertrain": "ICE",
    "fuel": "GASOLINE",
    "engine_description": "GX 460 4.6L V8 DOHC dual VVT-i",
    "engine_displacement": fact(4.6, "L"),
    "cylinders": 8,
    "power_hp": 301,
    "torque_lb_ft": fact(329, "lb-ft"),
    "transmission_family": "AT",
    "transmission_description": "6-speed electronically controlled automatic, sequential shift",
    "gears": 6,
    "seats": 7,
    "length_in": fact(192.1, "in"),
    "width_in": fact(74.2, "in"),
    "wheelbase_in": fact(109.8, "in"),
    "ground_clearance": fact(8.1, "in"),
    "cargo_volume_max_cu_ft": fact(64.7, "cu ft"),
    "epa_city_mpg": fact(15, "US mpg"),
    "epa_highway_mpg": fact(20, "US mpg"),
    "epa_combined_mpg": fact(17, "US mpg"),
}
for trim, height, wheels in [
    ("GX 460", 74.2, "18-inch six-spoke alloy"),
    ("GX 460 Premium", 74.2, "18-inch split-six-spoke alloy"),
    ("GX 460 Luxury", 73.8, "18-inch split-six-spoke alloy, Liquid Graphite finish"),
]:
    extra = {"height_in": fact(height, "in"), "wheels": wheels}
    if trim.endswith("Luxury"):
        extra["suspension"] = (
            "Adaptive Variable Suspension; auto-leveling rear air suspension (Luxury standard only)"
        )
    gx["groups"].append(
        group(
            trim.lower().replace(" ", "-"),
            trim,
            2014,
            2016,
            ["4WD"],
            extra,
            "US GX460 MY2014/15 PDFp11 and MY2016p19: trim-specific height/wheels and Luxury-only suspension; all trims4.6V8/6AT/full-time4WD/7 seats.",
        )
    )
m["families"].append(gx)
fxurl = "https://pictures.dealer.com/kuniinfiniti/806986ab0a0d028a00b125bde344479c.pdf"
m["documents"]["fx-spec-2013-09"] = doc(
    fxurl,
    "infiniti",
    2013,
    2013,
    "2013 Infiniti FX Technical Specifications, current Aug2012: PDFp1 engine/gearbox/drive; p2 suspension/brakes; p3 wheel/tire/dimensions; p7 seats/capacities/weights/EPA. Manufacturer document hosted by dealer; visual p1,p7 checked.",
)
m["documents"]["fx-factsheet-2013-09"] = doc(
    "https://www.auto-brochures.com/makes/Infiniti/FX/Infiniti_US%20FX_Factsheet_2013.pdf",
    "infiniti",
    2013,
    2013,
    "MY2013 US FX factsheet pp2-4; cross-check only. Fuel recommended vs required wording differs from technical specifications; fuel_grade held.",
)
m["documents"]["fx-s51-09"] = doc(
    "https://static.nhtsa.gov/odi/tsbs/2024/MC-11009064-0001.pdf",
    "infiniti",
    2013,
    2013,
    "Infiniti ITB19-024D PDFp1 APPLIED VEHICLES identifies2009-2013FX(S51). Platform identity only; no campaign/damage applicability claim.",
)
fx = family(
    "infiniti-fx-s51-us-2013-09",
    "Infiniti",
    "FX",
    "S51",
    "S51",
    2013,
    2013,
    {"2013": ["fx-spec-2013-09", "fx-factsheet-2013-09"]},
    ["fx-s51-09"],
)
fx["facts"] = {
    "body": "SUV",
    "powertrain": "ICE",
    "fuel": "GASOLINE",
    "transmission_family": "AT",
    "transmission_description": "7-speed electronically controlled automatic with ASC and manual shift mode",
    "gears": 7,
    "seats": 5,
    "length_in": fact(191.3, "in"),
    "width_in": fact(75.9, "in"),
    "wheelbase_in": fact(113.6, "in"),
    "ground_clearance": fact(7.36, "in"),
    "fuel_tank_us_gal": fact(23.8, "US gal"),
    "cargo_volume_cu_ft": fact(24.8, "cu ft"),
    "cargo_volume_max_cu_ft": fact(62.0, "cu ft"),
    "front_suspension": "Independent aluminum double-wishbone with stabilizer bar",
    "rear_suspension": "Independent multi-link with stabilizer bar",
}
for trim, drive, displ, code, cyl, hp, tq, weight, city, hwy in [
    ("FX37", "RWD", 3.7, "VQ37VHR", 6, 325, 267, 4209, 17, 24),
    ("FX37", "AWD", 3.7, "VQ37VHR", 6, 325, 267, 4321, 16, 22),
    ("FX37 Limited Edition", "AWD", 3.7, "VQ37VHR", 6, 325, 267, 4321, 16, 22),
    ("FX50", "AWD", 5.0, "VK50VE", 8, 390, 369, 4562, 14, 20),
]:
    large = cyl == 8
    special = "Limited" in trim
    fields = {
        "engine_description": f"{code} {displ:.1f}L V{cyl} DOHC VVEL",
        "engine_code": code,
        "engine_displacement": fact(displ, "L"),
        "cylinders": cyl,
        "power_hp": hp,
        "torque_lb_ft": fact(tq, "lb-ft"),
        "curb_weight_lb": fact(weight, "lb"),
        "epa_city_mpg": fact(city, "US mpg"),
        "epa_highway_mpg": fact(hwy, "US mpg"),
        "compression_ratio": 10.9 if large else 11.0,
        "wheels": "21 x 9.5 alloy"
        if large or special
        else "18 x 8.0 alloy;20-inch optional package excluded",
        "tires": "265/45R21 104V all-season" if large or special else "265/60R18 109V all-season",
        "front_brakes": "14.0 x 1.3 inch vented discs" if large else "12.6 x 1.3 inch vented discs",
        "rear_brakes": "13.8 x 0.8 inch vented discs" if large else "12.1 x 0.6 inch vented discs",
        "coolant": f"Factory table system capacity {11.6 if large else 9.7} L; fluid specification and routine service refill not established",
    }
    fx["groups"].append(
        group(
            trim.lower().replace(" ", "-") + "-" + drive.lower(),
            trim,
            2013,
            2013,
            [drive],
            fields,
            "US MY2013 FX technical specifications PDFpp1-3,7: exact FX50AWD/FX37AWD/FX37RWD columns; LimitedEditionAWD wheel exception; coolant is table capacity, not routine refill.",
        )
    )
m["families"].append(fx)
(ROOT / "data/manifests/us-ai-verify-09-root-candidate.json").write_text(
    json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("13 independently sourced annual configurations,2 families; optional oil/fuel conflicts held")

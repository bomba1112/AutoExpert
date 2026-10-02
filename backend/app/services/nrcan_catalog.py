"""NRCan published row adapter. No inferred generations, engine codes or gearbox internals."""

from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from decimal import Decimal

from app.schemas.knowledge import CatalogRecord
from app.services.knowledge_import import checksum, normalized

COMMON = {"Model year", "Make", "Model", "Vehicle class", "Transmission"}
FUEL = {
    "X": "Regular Gasoline",
    "Z": "Premium Gasoline",
    "D": "Diesel",
    "B": "Electricity",
    "E": "E85",
    "N": "Natural Gas",
}
ATTRIBUTION = "Contains information licensed under the Open Government Licence – Canada."


def nrcan_record(row, *, kind, source_url, line, family):
    facts = {}

    def add(key, value, column, unit=None, labels=None):
        if value not in (None, "", "n/a"):
            facts[key] = {
                "value": value,
                "unit": unit,
                "locator": f"CSV record {line}; {column}",
                "titles": labels or {},
            }

    fuel_code = row.get("Fuel type 2") or row.get("Fuel type")
    add("fuel_grade", FUEL.get(fuel_code), "Fuel type 2 / Fuel type")
    add(
        "fuel",
        "ELECTRICITY"
        if kind == "BEV"
        else "DIESEL"
        if fuel_code == "D"
        else "GASOLINE"
        if fuel_code in {"X", "Z"}
        else FUEL.get(fuel_code),
        "Fuel type",
    )
    add(
        "powertrain",
        kind if kind in {"BEV", "PHEV"} else "COMBUSTION_UNSPECIFIED",
        "Dataset category; conventional/hybrid source does not distinguish architecture",
    )
    add(
        "source_cycle",
        "NRCAN_5_CYCLE",
        "NRCan dataset methodology",
        labels={"ru": "Испытательный цикл", "az": "Sınaq dövrü"},
    )
    add("size_class", row["Vehicle class"], "Vehicle class")
    add("engine_displacement", row.get("Engine size (L)"), "Engine size (L)", "L")
    add("cylinders", row.get("Cylinders"), "Cylinders")
    add(
        "motor_power_kw",
        row.get("Motor (kW)"),
        "Motor (kW)",
        "kW",
        {"ru": "Пиковая мощность электромотора", "az": "Elektrik mühərrikinin pik gücü"},
    )
    trans = row["Transmission"]
    if not re.fullmatch(r"(?:AS|AM|AV|A|M)\d*", trans):
        raise ValueError("NRCAN_TRANSMISSION_CODE_CHANGED")
    family_trans = (
        "MANUAL"
        if trans.startswith("M")
        else "VARIABLE_UNSPECIFIED"
        if trans.startswith("AV")
        else "AMT_UNSPECIFIED"
        if trans.startswith("AM")
        else "AUTOMATIC_UNSPECIFIED"
    )
    add("transmission_description", trans, "Transmission; Understanding the tables XLSX")
    add("transmission_family", family_trans, "Transmission; construction unspecified")
    # AV7 represents simulated ratios; do not claim seven physical gears.
    if trans[0] == "M" or trans.startswith(("AS", "AM")) or re.fullmatch(r"A\d+", trans):
        gears = re.search(r"\d+", trans)
        if gears:
            add("gears", int(gears[0]), "Transmission")
    model = row["Model"]
    if re.search(r"\bAWD\b", model):
        add("drivetrain", "AWD", "Model AWD suffix; official abbreviation legend")
    elif re.search(r"\b(?:4WD|4X4)\b", model, re.I):
        add("drivetrain", "4WD", "Model 4WD/4X4 suffix; official abbreviation legend")
    elif re.search(r"\bFWD\b", model):
        add("drivetrain", "FWD", "Model explicit FWD suffix")
    elif re.search(r"\bRWD\b", model):
        add("drivetrain", "RWD", "Model explicit RWD suffix")
    for prefix, body in [
        ("Sport utility", "SUV"),
        ("Station wagon", "WAGON"),
        ("Pickup", "PICKUP"),
        ("Minivan", "MINIVAN"),
        ("Van:", "VAN"),
    ]:
        if row["Vehicle class"].startswith(prefix):
            add("body", body, "Vehicle class")
    for col, key, unit, labels in [
        (
            "City (L/100 km)",
            "fuel_city",
            "L/100km",
            {"ru": "Расход в городе · NRCan", "az": "Şəhər sərfiyyatı · NRCan"},
        ),
        (
            "Highway (L/100 km)",
            "fuel_highway",
            "L/100km",
            {"ru": "Расход на трассе · NRCan", "az": "Magistral sərfiyyatı · NRCan"},
        ),
        (
            "Combined (L/100 km)",
            "fuel_combined",
            "L/100km",
            {
                "ru": "Расход · NRCan (для PHEV — бензиновый режим)",
                "az": "Sərfiyyat · NRCan (PHEV üçün benzin rejimi)",
            },
        ),
        (
            "Combined (kWh/100 km)",
            "electricity_combined",
            "kWh/100km",
            {"ru": "Электроэнергия · NRCan", "az": "Elektrik sərfiyyatı · NRCan"},
        ),
        (
            "CO2 emissions (g/km)",
            "co2_tailpipe",
            "g/km",
            {"ru": "CO₂ на выхлопе · NRCan", "az": "Egzoz CO₂ · NRCan"},
        ),
        (
            "Range (km)",
            "range_km",
            "km",
            {"ru": "Запас хода · NRCan", "az": "Gediş ehtiyatı · NRCan"},
        ),
        (
            "Range 1 (km)",
            "electric_mode_range_km",
            "km",
            {
                "ru": "Пробег в электрическом режиме · NRCan",
                "az": "Elektrik rejimində məsafə · NRCan",
            },
        ),
        ("Recharge time (h)", "charge_ac_240v_hours", "h", None),
    ]:
        value = row.get(col)
        if value and value != "n/a":
            number = Decimal(value)
            if not number.is_finite() or number < 0:
                raise ValueError("NRCAN_INVALID_NUMBER")
            add(key, str(number), col, unit, labels)
    if kind == "PHEV":
        text = row["Combined Le/100 km"]
        add(
            "phev_electric_mode_original",
            text,
            "Combined Le/100 km",
            labels={"ru": "Электрический режим по источнику", "az": "Mənbədə elektrik rejimi"},
        )
        match = re.fullmatch(r"[\d.]+\s*\(([\d.]+) kWh/100 km\)\*?", text)
        blended = re.fullmatch(r"[\d.]+\s*\(\[([\d.]+) kWh \+ ([\d.]+) L\]/100 km\)\*?", text)
        if match or blended:
            add(
                "electricity_combined",
                (match or blended)[1],
                "Combined Le/100 km electricity component",
                "kWh/100km",
                {
                    "ru": "Электроэнергия в электрическом режиме · NRCan",
                    "az": "Elektrik rejimində sərfiyyat · NRCan",
                },
            )
            add(
                "electric_mode_fuel",
                blended[2] if blended else "0",
                "Combined Le/100 km gasoline component",
                "L/100km",
                {
                    "ru": "Бензин в электрическом режиме · испытание",
                    "az": "Elektrik rejimində benzin · sınaq",
                },
            )
        else:
            raise ValueError("NRCAN_PHEV_FORMAT_CHANGED")
    identity = {
        key: row.get(key)
        for key in [
            "Model year",
            "Make",
            "Model",
            "Vehicle class",
            "Engine size (L)",
            "Cylinders",
            "Motor (kW)",
            "Transmission",
            "Fuel type",
            "Fuel type 1",
            "Fuel type 2",
        ]
    }
    return CatalogRecord(
        external_key=kind + ":" + checksum(identity)[:40],
        make=family["make"],
        model=family["model"],
        configuration=model + " · " + (row.get("Engine size (L)") or kind) + " · " + trans,
        aliases=[model],
        original_market="CA",
        model_year=int(row["Model year"]),
        facts=facts,
        source_url=source_url,
        revision_note=ATTRIBUTION
        + (
            " Canadian certification row, generation and aggregate codes unverified. "
            "Family prefix is a search grouping, original source model retained."
        ),
    )


def parse_nrcan(text, manifest, source_url):
    kind = manifest.dataset_kind
    if kind is None:
        raise ValueError("NRCAN_DATASET_KIND_REQUIRED")
    reader = csv.DictReader(io.StringIO(text.replace("\r\r\n", "\n")))
    required = COMMON | (
        {"Combined (kWh/100 km)", "Motor (kW)"}
        if kind == "BEV"
        else {"Engine size (L)", "Combined (L/100 km)"}
    )
    if kind == "PHEV":
        required |= {"Combined Le/100 km", "Fuel type 1", "Fuel type 2"}
    if not required <= set(reader.fieldnames or []):
        raise ValueError("NRCAN_SCHEMA_CHANGED")
    groups = defaultdict(list)
    seen = {}
    for line, row in enumerate(reader, 2):
        if not row.get("Model year"):
            continue
        year = int(row["Model year"])
        if not manifest.year_min <= year <= manifest.year_max:
            continue
        make, model = normalized(row["Make"]), normalized(row["Model"])
        matches = [
            f
            for f in manifest.family_mappings
            if normalized(f["make"]) == make
            and (model == normalized(f["model"]) or model.startswith(normalized(f["model"]) + " "))
        ]
        if not matches:
            continue
        family = max(matches, key=lambda f: len(normalized(f["model"])))
        r = nrcan_record(
            row, kind=kind, source_url=source_url, line=line, family=family
        ).model_dump(mode="json")
        signature = checksum(row)
        if r["external_key"] in seen:
            if seen[r["external_key"]] != signature:
                raise ValueError("NRCAN_DUPLICATE_IDENTITY_CONFLICT")
            continue
        seen[r["external_key"]] = signature
        groups[(make, normalized(family["model"]))].append(r)
    result = []
    for key in sorted(groups)[: manifest.family_limit]:
        rows = sorted(groups[key], key=lambda r: (-r["model_year"], r["external_key"]))
        result.extend(rows[: manifest.versions_per_family])
    return result

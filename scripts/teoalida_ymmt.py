"""Teoalida "Year-Make-Model-Trim-Specs" (US trims): specifications per trim (next-stage prompt A.3).

Only US trims of our lines, MY2014–2026. Taken: dimensions, track, ground clearance, angles,
turning circle, Cd, interior and cargo volume, weights, payload, towing, cylinders, displacement,
power and torque with rpm, valves and valve timing, drive, transmission, 0–60, fuel type, tank,
EPA mpg, EV data, interior dimensions, suspension, tires and wheels, safety, NHTSA rating,
platform code / generation. Units converted to metric by the units module. Prices, colors,
reviews, pros/cons and expert ratings are never taken (they stay in the raw file).

Steps (no database writes): parse -> data_work/_shared/teoalida/ymmt_us.json;
check -> accuracy_ymmt.json (A.8); stage -> Teoalida documents for fields with >= 90% agreement.

  .venv/Scripts/python.exe scripts/teoalida_ymmt.py [parse|check|stage|all]
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "backend"))
from app.services.tech_units import convert  # noqa: E402
from teoalida_common import OUT, read_table, row_quote, unique_file  # noqa: E402
from us_tech_common import WORK  # noqa: E402
from us_tech_lines import MAKES, lines_for  # noqa: E402

SHEET, REQUIRED = "Full specs", ["Make", "Model", "Year"]
PUBLISHER = "Teoalida - Year-Make-Model-Trim-Specs database (US trims; secondary; owner's sample)"


def num(text):
    m = re.search(r"-?\d+(?:\.\d+)?", str(text or "").replace(",", ""))
    return Decimal(m.group(0)) if m else None


def conv(unit_from, unit_to, places=0):
    def f(v):
        n = num(v)
        if n is None:
            return None
        out = convert(n, unit_from, unit_to)
        return float(out.quantize(Decimal(1) if places == 0 else Decimal(10) ** -places, rounding=ROUND_HALF_UP))
    return f


def plain(places=None):
    def f(v):
        n = num(v)
        if n is None:
            return None
        return int(n) if places is None and n == n.to_integral_value() else float(n if places is None else round(n, places))
    return f


def text(v):
    v = " ".join(str(v).split()) if v not in (None, "") else None
    return None if v in (None, "-", "N/A", "None") else v


DRIVE = [(re.compile(r"all[- ]wheel|AWD", re.I), "AWD"), (re.compile(r"four[- ]wheel|4WD|4x4", re.I), "4WD"),
         (re.compile(r"front[- ]wheel|FWD", re.I), "FWD"), (re.compile(r"rear[- ]wheel|RWD", re.I), "RWD")]


def drive(v):
    return next((d for p, d in DRIVE if p.search(str(v or ""))), None)


# column -> (fact key, converter, unit)
FIELDS = {
    "Length (in)": ("length_mm", conv("in", "mm"), "mm"),
    "Width (in)": ("width_mm", conv("in", "mm"), "mm"),
    "Height (in)": ("height_mm", conv("in", "mm"), "mm"),
    "Wheelbase (in)": ("wheelbase_mm", conv("in", "mm"), "mm"),
    "Front track (in)": ("track_front_mm", conv("in", "mm"), "mm"),
    "Rear track (in)": ("track_rear_mm", conv("in", "mm"), "mm"),
    "Ground clearance (in)": ("ground_clearance", conv("in", "mm"), "mm"),
    "Angle of approach (degrees)": ("approach_angle_deg", plain(1), "deg"),
    "Angle of departure (degrees)": ("departure_angle_deg", plain(1), "deg"),
    "Turning circle (ft)": ("turning_circle_m", conv("ft", "m", 1), "m"),
    "Drag coefficient (Cd)": ("drag_coefficient", plain(3), None),
    "EPA interior volume (cu ft)": ("interior_volume_l", conv("cu_ft", "L"), "L"),
    "Cargo capacity (cu ft)": ("cargo_l", conv("cu_ft", "L"), "L"),
    "Maximum cargo capacity (cu ft)": ("cargo_max_l", conv("cu_ft", "L"), "L"),
    "Curb weight (lbs)": ("curb_weight_kg", conv("lb", "kg"), "kg"),
    "Gross weight (lbs)": ("gross_weight_kg", conv("lb", "kg"), "kg"),
    "Maximum payload (lbs)": ("payload_kg", conv("lb", "kg"), "kg"),
    "Maximum towing capacity (lbs)": ("towing_kg", conv("lb", "kg"), "kg"),
    "Total seating": ("seats", plain(), None),
    "Cylinders": ("cylinders", plain(), None),
    "Engine size (l)": ("engine_displacement_l", plain(1), "L"),
    "Horsepower (HP)": ("power_hp", plain(), "hp"),
    "Horsepower (rpm)": ("power_rpm", plain(), "rpm"),
    "Torque (ft-lbs)": ("torque_lb_ft", plain(), "lb-ft"),
    "Torque (rpm)": ("torque_rpm", plain(), "rpm"),
    "Valves": ("valves", plain(), None),
    "Valve timing": ("valve_timing", text, None),
    "Cam type": ("cam_type", text, None),
    "Drive type": ("drivetrain", drive, None),
    "Transmission": ("transmission_description", text, None),
    "Manufacturer 0-60 mph (sec)": ("acceleration_0_60_mph_s", plain(1), "s"),
    "Engine type": ("engine_type", text, None),
    "Fuel type": ("fuel_type", text, None),
    "Fuel tank capacity (gal)": ("fuel_tank_l", conv("gal", "L", 1), "L"),
    "EPA combined MPG": ("epa_combined_mpg", plain(), "mpg"),
    "EPA combined MPGe": ("epa_combined_mpge", plain(), "MPGe"),
    "EPA electricity range": ("epa_electric_range_km", conv("mi", "km"), "km"),
    "EPA kWh/100 mi": ("epa_kwh_per_100mi", plain(1), "kWh/100 mi"),
    "EPA time to charge battery (at 240V)": ("charge_time_240v_h", plain(1), "h"),
    "Battery capacity": ("battery_capacity_kwh", plain(1), "kWh"),
    "Fast-charge port type": ("fast_charge_port", text, None),
    "Front head room (in)": ("front_head_room_mm", conv("in", "mm"), "mm"),
    "Front hip room (in)": ("front_hip_room_mm", conv("in", "mm"), "mm"),
    "Front leg room (in)": ("front_leg_room_mm", conv("in", "mm"), "mm"),
    "Front shoulder room (in)": ("front_shoulder_room_mm", conv("in", "mm"), "mm"),
    "Rear head room (in)": ("rear_head_room_mm", conv("in", "mm"), "mm"),
    "Rear hip room (in)": ("rear_hip_room_mm", conv("in", "mm"), "mm"),
    "Rear leg room (in)": ("rear_leg_room_mm", conv("in", "mm"), "mm"),
    "Rear shoulder room (in)": ("rear_shoulder_room_mm", conv("in", "mm"), "mm"),
    "Suspension": ("suspension_features", text, None),
    "Tires and wheels": ("tires_wheels_features", text, None),
    "Safety features": ("safety_features", text, None),
    "NHTSA Overall Rating": ("nhtsa_overall_rating", text, None),
    "Platform code / generation number": ("platform_code", text, None),
}
MPG_SPLIT = "EPA city/highway MPG"


def our_line(make: str, model: str, trim: str, year: int):
    """The line a Teoalida model/trim belongs to, by the line's EPA names and include/exclude
    patterns (the trim is the designation, e.g. "330i" in "3 Series", "M3")."""
    for line in lines_for(make, include_done=True):
        if not (line.years[0] <= year <= line.years[1]):
            continue
        names = {n.lower() for n in (line.name, *line.epa_base)}
        full = f"{model} {trim}".strip()
        if line.epa_exclude and (re.search(line.epa_exclude, full) or re.search(line.epa_exclude, model)):
            continue
        if trim.lower() in names:
            return line
        if model.lower() in names and (line.epa_include == r".*" or re.search(line.epa_include, trim)
                                       or re.search(line.epa_include, full)):
            return line
    return None


def make_slug(name: str) -> str | None:
    return next((slug for slug, meta in MAKES.items() if str(meta.get("epa", "")).lower() == str(name).lower()), None)


BODY = [(re.compile(r"wagon|touring", re.I), "WAGON"), (re.compile(r"gran turismo|\bGT\b", re.I), "GT"),
        (re.compile(r"convertible|cabrio", re.I), "CONVERTIBLE"), (re.compile(r"coupe", re.I), "COUPE")]


def body_family(text_: str | None) -> str | None:
    return next((b for p, b in BODY if p.search(text_ or "")), None)


def label_of(row: dict) -> str:
    """The trim as the variant label: Trim, plus AWD and a non-sedan body when only the
    description says them ("LE" + "AWD", "328i xDrive" + "Wagon")."""
    trim = str(row.get("Trim") or "").strip()
    desc = str(row.get("Trim (description)") or "")
    label = trim
    if re.search(r"\bAWD\b", desc) and not re.search(r"\bAWD|xDrive|4MATIC|quattro|4Motion", trim, re.I):
        label += " AWD"
    body = str(row.get("Body type") or "")
    if body_family(body) and not body_family(trim):
        label += f" {body}"
    return label


def parse() -> dict:
    path = unique_file("ymm_trim_specs")
    _, head, rows = read_table(path, SHEET, REQUIRED, valid=lambda d: isinstance(d.get("Year"), (int, float)) and 1980 < d["Year"] < 2100)
    out, skipped = [], defaultdict(int)
    for r in rows:
        year = int(r["Year"])
        make = make_slug(r["Make"])
        if make is None or not (2014 <= year <= 2026):
            skipped["make not ours or year outside 2014-2026"] += 1
            continue
        line = our_line(make, str(r["Model"]), str(r.get("Trim") or ""), year)
        if line is None:
            skipped[f"{r['Make']} {r['Model']}: not one of our lines"] += 1
            continue
        values = {}
        for col, (key, f, unit) in FIELDS.items():
            if r.get(col) in (None, ""):
                continue
            v = f(r[col])
            if v is not None:
                values[key] = {"value": v, "unit": unit, "column": col, "original": str(r[col])}
        desc = str(r.get("Trim (description)") or "")
        if re.search(r"gas/electric (?:plug-in )?hybrid", desc) and not re.search(r"mild hybrid", desc):
            # a full or plug-in hybrid: the database's horsepower is the system output
            if "power_hp" in values:
                values["system_power_hp"] = values.pop("power_hp")
            values.pop("power_rpm", None)
        mpg = str(r.get(MPG_SPLIT) or "")
        m = re.match(r"^\s*(\d+)\s*/\s*(\d+)\s*$", mpg)
        if m:
            values["epa_city_mpg"] = {"value": int(m.group(1)), "unit": "mpg", "column": MPG_SPLIT, "original": mpg}
            values["epa_highway_mpg"] = {"value": int(m.group(2)), "unit": "mpg", "column": MPG_SPLIT, "original": mpg}
        out.append({"row": r["_row"], "make": make, "line": line.slug, "year": year, "model": r["Model"],
                    "trim": r.get("Trim"), "description": r.get("Trim (description)"), "body": r.get("Body type"),
                    "label": label_of(r), "drive": drive(r.get("Drive type")),
                    "plug_in": bool(re.search(r"plug-in", str(r.get("Trim (description)")), re.I)),
                    "values": values})
    data = {"source_file": path.name, "rows_read": len(rows), "records": out, "skipped": dict(skipped)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ymmt_us.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("rows", len(rows), "ours", len(out), "skipped", dict(skipped))
    return data


GEARS = re.compile(r"(\d{1,2})[- ]speed|\((?:A|AM-S|S|AV-S|M|AM)?(\d{1,2})\)", re.I)
FUEL = [(re.compile(r"premium", re.I), "premium"), (re.compile(r"diesel", re.I), "diesel"),
        (re.compile(r"electric", re.I), "electric"), (re.compile(r"regular|unleaded|gasoline", re.I), "regular")]


def fuel_class(v):
    return next((c for p, c in FUEL if p.search(str(v or ""))), None)


def gears(v):
    m = GEARS.search(str(v or ""))
    return int(next(g for g in m.groups() if g)) if m else None


def configs_for(staging: dict, rec: dict) -> list:
    """Configurations of the model year that fit the trim: same drive and plug-in status; EPA
    model names carrying the designation when the trim is a designation (BMW "330i xDrive")."""
    from teoalida_accuracy import designation_fits

    out = []
    for c in staging["configurations"]:
        if c["year"] != rec["year"]:
            continue
        if rec["drive"] and c.get("drivetrain") and rec["drive"] != c["drivetrain"]:
            continue
        if rec["plug_in"] != (c.get("powertrain") == "PHEV"):
            continue
        names = [v.get("epa_model") for v in c.get("epa_vehicles", [])]
        if re.search(r"\d", str(rec["trim"])) and not any(designation_fits(rec["trim"], n) for n in names):
            continue
        out.append(c)
    return out


def check() -> dict:
    from teoalida_accuracy import Tally, body_family, load_line, official_values, write_report

    data = json.loads((OUT / "ymmt_us.json").read_text(encoding="utf-8"))
    tally = Tally("teoalida/ymm_trim_specs")
    cache = {}
    for rec in data["records"]:
        st = cache.setdefault((rec["make"], rec["line"]), load_line(rec["make"], rec["line"]))
        if st is None:
            continue
        cfgs = configs_for(st, rec)
        body = body_family(rec["label"])
        where = f"{rec['make']}/{rec['line']} {rec['year']} {rec['label']}"
        for key, item in rec["values"].items():
            value = item["value"]
            officials = []
            for cfg in cfgs or [None]:
                officials += official_values(st, key, rec["year"], rec["label"], cfg)
            # a press value of another body (wagon, GT) is not the same vehicle
            officials = [o for o in officials if o[1] == "epa" or not body_family(o[2]) or body_family(o[2]) == body]
            if key == "drivetrain":
                officials = [(c["drivetrain"], "epa", c["configuration_key"]) for c in cfgs if c.get("drivetrain")]
            elif key == "transmission_description":
                key, value = "transmission (gear count vs EPA)", gears(value)
                officials = [(gears(c.get("epa_trany")), "epa", c.get("epa_trany")) for c in cfgs if gears(c.get("epa_trany"))]
                if value is None:
                    continue
            elif key == "fuel_type":
                key, value = "fuel_type (class vs EPA)", fuel_class(value)
                officials = [(fuel_class(v.get("fuel_type")), "epa", v.get("epa_model")) for c in cfgs
                             for v in c.get("epa_vehicles", []) if fuel_class(v.get("fuel_type"))]
            elif key == "platform_code":
                officials = [(g["code"], "generation", g["code"]) for g in st["generations"]
                             if g["start_year"] <= rec["year"] <= g["end_year"] and re.fullmatch(r"[A-Z]{1,3}\d{2,3}[A-Z]?", g["code"])]
                codes = re.findall(r"\b[A-Z]{1,3}\d{2,3}[A-Z]?\b", str(value))
                if officials:
                    value = officials[0][0] if officials[0][0] in codes else (codes[0] if codes else value)
            tally.add(key, value, officials, where)
    return write_report("ymmt", tally, {"records": len(data["records"])})


# accuracy-report field -> stored fact key (the report labels a few fields by their comparison)
REPORT_KEY = {"transmission (gear count vs EPA)": "transmission_description", "fuel_type (class vs EPA)": "fuel_type"}


def stage() -> dict:
    from teoalida_common import clear_docs, write_doc, write_pagetext

    report = json.loads((OUT / "accuracy_ymmt.json").read_text(encoding="utf-8"))
    allowed = {REPORT_KEY.get(k, k) for k, v in report["fields"].items() if v["write"]}
    data = json.loads((OUT / "ymmt_us.json").read_text(encoding="utf-8"))
    path = unique_file("ymm_trim_specs")
    sha = write_pagetext(path, SHEET, REQUIRED)
    _, head, rows = read_table(path, SHEET, REQUIRED)
    by_row = {r["_row"]: r for r in rows}
    removed = clear_docs("ymmt")
    groups = defaultdict(list)
    for rec in data["records"]:
        groups[(rec["make"], rec["line"], rec["year"])].append(rec)
    written = 0
    for (make, line, year), recs in sorted(groups.items()):
        facts = []
        for rec in recs:
            raw = by_row[rec["row"]]
            for key, item in rec["values"].items():
                if key not in allowed:
                    continue
                fact = {"key": key, "value": item["value"], "unit": item["unit"], "page": rec["row"],
                        "quote": row_quote(raw, head, [item["column"]]), "row": f"{rec['label']} ({rec['description']})",
                        "label": key.replace("_", " "), "engine_text": None, "variant": rec["label"],
                        "original": item["original"]}
                if rec["drive"]:
                    fact["drive"] = rec["drive"]
                facts.append(fact)
        if not facts:
            continue
        key = "teoalida-ymmt-" + hashlib.sha1(f"{make}|{line}|{year}".encode()).hexdigest()[:10]
        write_doc(make, "ymmt", key, [f"{make}/{line}"], [year], facts, path, sha,
                  f"Teoalida Year-Make-Model-Trim-Specs: {line} {year} (US trims)", PUBLISHER, "2026-10-03")
        written += 1
    out = {"allowed_fields": sorted(allowed), "documents": written, "removed_previous": removed}
    (OUT / "ymmt_stage.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("staged documents", written, "fields", sorted(allowed))
    return out


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("parse", "all"):
        parse()
    if step in ("check", "all"):
        rep = check()
        for k, r in rep["fields"].items():
            print(f"{k}: compared {r['compared']}, agreed {r['agreed']} ({r['agreement']}), no official {r['no_official']} -> {r['verdict']}")
    if step in ("stage", "all"):
        stage()

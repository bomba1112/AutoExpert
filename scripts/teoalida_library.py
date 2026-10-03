"""Teoalida databases of other markets -> library (next-stage prompt A.7, main prompt Appendix D)
and the Tuning database -> comparison of factory power/torque only (A.6). Nothing here is
written to the database.

Library: data_work/_library/<CN|JP|EU|UK|ES|IN>/teoalida/staging_specs.json with the fields of
section 4 of the main prompt (identification, engine, transmission, drive, power/torque, fuel and
consumption, tank, dimensions, weights, cargo, tires, suspension, brakes, steering) as the
database gives them (original units in the field name), with market and source row. The China
database has a row of Chinese labels under the English header: the pair is kept as the
dictionary (dictionary_zh_en.json). Japanese chassis / model codes and engine codes are kept.
Each library file is registered in data_work/_library/manifest.csv.

Tuning (dyno-chiptuningfiles, European engine versions): the "standard" output is compared with
our official power/torque where generation and designation match; reported, never written.

  .venv/Scripts/python.exe scripts/teoalida_library.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from teoalida_common import OUT, read_manifest, read_table, sheet_rows, unique_file  # noqa: E402
from us_tech_common import WORK  # noqa: E402

LIBRARY = WORK / "_library"
# dataset -> (market, sheet, required header names, {section-4 field: column})
DATASETS = {
    "china": ("CN", "Database", ["Manufacturer", "Model", "Version"], {
        "make": "Manufacturer", "model": "Model", "version": "Version", "displacement": "Displacement",
        "aspiration": "Intake form", "transmission": "Transmission type", "length_width_height_mm": "Length × width × height (mm)",
        "wheelbase_mm": "Wheelbase", "curb_weight_kg": "Curb weight", "seats": "Number of seats", "cargo_l": "Cargo space",
        "fuel_tank_l": "Gas tank size", "tire_front": "Front tires", "tire_rear": "Rear tires",
        "turning_diameter_m": "Minimum turning diameter", "power_kw": "Maximum power (kW)", "power_ps": "Maximum power (Ps)",
        "power_rpm": "Maximum power (rpm)", "torque_nm": "Maximum torque (N)", "torque_rpm": "Maximum torque (rpm)",
        "cylinders": "Number of cylinders", "injection": "Injection type", "compression_ratio": "Compression ratio",
        "fuel_ron": "Fuel RON", "gears": "Number of gears", "consumption": "Fuel consumption", "drive": "Drivetrain",
        "front_suspension": "Front suspension", "rear_suspension": "Rear suspension", "front_brakes": "Front brakes",
        "rear_brakes": "Rear brakes"}),
    "japan": ("JP", "jpcenter versions", ["Make", "Model", "Chassis code"], {
        "make": "Make", "model": "Model", "version": "Version", "chassis_code": "Chassis code", "years": "Dates releasing",
        "body": "Body type", "seats": "Seats", "length_mm": "Overall length", "width_mm": "Overall width",
        "height_mm": "Overall height", "wheelbase_mm": "Wheelbase", "track_front_mm": "Front track", "track_rear_mm": "Rear track",
        "curb_weight_kg": "Weight", "engine_code": "Engine code", "engine_type": "Engine type", "bore": "Bore", "stroke": "Stroke",
        "displacement": "Displacement", "compression_ratio": "Compression ratio", "injection": "Fuel injection system",
        "power": "Maximum power hp / t.min.", "torque": "Maximum torque, Nm / rpm", "aspiration": "Supercharger",
        "fuel_tank_l": "Fuel tank capacity, liters", "fuel_type": "Fuel type", "consumption_l_100km": "Fuel consumption, l/100 km",
        "steering": "Steering", "front_suspension": "Front suspension", "rear_suspension": "Rear suspension",
        "front_brakes": "Front brake", "rear_brakes": "Rear brake", "tire_front": "Front wheel", "tire_rear": "Rear wheel",
        "turning_radius_m": "Turning radius", "gears": "Number of gears", "drive": "Drive"}),
    "japan_goonet": ("JP", "goo-net versions", ["Make", "Model", "Model Code"], {
        "make": "Make", "model": "Model", "version": "Version", "model_code": "Model Code", "years": "Year of launch",
        "body": "Body Type", "seats": "Riding Capacity", "length_mm": "Overall Length (mm)", "width_mm": "Overall Width (mm)",
        "height_mm": "Overall Height (mm)", "wheelbase_mm": "Wheelbase (mm)", "track_front_mm": "Tread Front (mm)",
        "track_rear_mm": "Tread Rear (mm)", "curb_weight_kg": "Weight (kg)", "engine_code": "Engine Model",
        "cylinders": "Cylinders", "power_ps": "Maximum Power (ps)", "power_kw": "Maximum Power (kW)",
        "power_rpm": "Maximum Power (rpm)", "torque_nm": "Maximum Torque (Nm)", "torque_rpm": "Maximum Torque (rpm)",
        "displacement_cc": "Displacement (cc)", "compression_ratio": "Compression Ratio", "aspiration": "Charger",
        "fuel_tank_l": "Fuel Tank Equipment (L)", "fuel_type": "Fuel Type", "steering": "Steering System",
        "turning_radius_m": "Minimum Turning Radius", "front_suspension": "Suspension System (front)",
        "rear_suspension": "Suspension System (rear)", "front_brakes": "Braking System (front)",
        "rear_brakes": "Braking System (rear)", "tire_front": "Tires Size (front)", "tire_rear": "Tires Size (rear)",
        "drive": "Driving Wheel", "transmission": "Transmission"}),
    "europe": ("EU", "FULL SPECS", ["Brand", "Range", "Generation"], {
        "make": "Brand", "model": "Range", "generation": "Generation", "model_series": "Model series",
        "chassis_code": "Manufacturer internal code", "version": "Engine version", "years": "Model launch date",
        "years_end": "Model end date", "fuel_type": "Fuel type", "power_kw": "Power (KW)", "power_hp": "Power (HP)",
        "displacement_cc": "Displacement (ccm)", "engine_code": "Engine code", "drive": "Drivetrain type",
        "transmission": "Gearbox type", "gears": "Number of gears", "cylinders": "Number of cylinders (combustion engine)",
        "injection": "Injection type (internal combustion engine)", "aspiration": "Supercharging (internal combustion engine)",
        "power_rpm": "Maximum power at rpm. (Combustion engine)", "torque_rpm": "Maximum torque at rpm. (Combustion engine)",
        "length_mm": "Length (mm)", "width_mm": "Width (mm)", "height_mm": "Height (mm)", "wheelbase_mm": "Wheelbase (mm)",
        "ground_clearance_mm": "Ground clearance (mm)", "turning_circle_m": "Turning circle (m)",
        "cargo_l": "Luggage volume normal", "curb_weight_kg": "Curb weight (kg)", "gross_weight_kg": "Gross weight (kg)",
        "towing_braked_kg": "Towing capacity braked 12% (kg)", "body": "Body type", "seats": "Number of seats normal",
        "front_suspension": "Front suspension", "rear_suspension": "Rear suspension", "steering": "Power steering",
        "front_brakes": "Front brake", "rear_brakes": "Rear brake", "tire_front": "Tire size",
        "tire_rear": "Tire size rear (if different)", "consumption_wltp_mixed": "Fuel consumption mixed (one third mix)"}),
    "uk": ("UK", "Versions table", ["Make", "Model", "Trim / Version"], {
        "make": "Make", "model": "Model", "version": "Trim / Version", "years": "Year start", "years_end": "Year end",
        "power_bhp": "Power (bhp)", "torque_nm": "Torque (Nm)", "fuel_tank_l": "Fuel Capacity (litres)",
        "curb_weight_kg": "Weight (kg)", "length_mm": "Length (mm)", "width_mm": "Width (mm)", "height_mm": "Height (mm)",
        "wheelbase_mm": "Wheelbase (mm)", "turning_circle_m": "Turning Circle (m)", "displacement_cc": "Engine Size (cc)",
        "cylinders": "Cylinders", "valves": "Valves", "fuel_type": "Fuel Type", "transmission": "Transmission",
        "gearbox": "Gearbox", "drive": "Drivetrain", "seats": "Seats", "cargo_l": "Luggage Capacity (litres)",
        "towing_braked_kg": "Braked Towing Weight (kg)", "chassis_code": "Platform / generation number",
        "consumption_mpg_uk": "Fuel consumption (mpg)"}),
    "spain": ("ES", "Database", ["Marca", "Modelo", "Versione"], {
        "make": "Marca", "model": "Modelo", "version": "Versione", "years": "Fecha", "displacement_cc": "Cilindrada (cm3)",
        "power_cv": "Potencia (cv)", "body": "Carrocería", "transmission": "Caja de cambios", "fuel_type": "Combustible",
        "gears": "Número de velocidades", "seats": "Número de Plazas", "length_mm": "Longitud (mm)", "height_mm": "Alto (mm)",
        "width_mm": "Ancho (mm)", "wheelbase_mm": "Batalla (mm)", "curb_weight_kg": "Peso (kg)",
        "cargo_l": "Capacidad Mínima del Maletero (litros)", "cylinders": "Nº de Cilindros y Disposición",
        "torque_nm": "Par máximo (Nm)", "drive": "Tracción", "tires": "Neumáticos (delanteros-traseros)",
        "consumption_l_100km": "Consumo Combinado (EU96) (l/100km)", "fuel_tank_l": "Capacidad Depósito Combustible (litros)"}),
    "india": ("IN", "Database LAST", ["naming-make", "naming-model", "naming-version"], {
        "make": "naming-make", "model": "naming-model", "version": "naming-version", "body": "naming-bodystyle",
        "engine": "enginetransmission-engine", "engine_type": "enginetransmission-engine_type",
        "power": "enginetransmission-maxpower", "power_rpm": "enginetransmission-maxpowerRPM",
        "torque": "enginetransmission-maxtorque", "torque_rpm": "enginetransmission-maxtorqueRPM",
        "fuel_type": "enginetransmission-fueltype", "drive": "enginetransmission-drivetrain",
        "transmission": "enginetransmission-transmission", "length_mm": "dimensionsandweight-length",
        "width_mm": "dimensionsandweight-width", "height_mm": "dimensionsandweight-height",
        "wheelbase_mm": "dimensionsandweight-wheelbase", "ground_clearance_mm": "dimensionsandweight-groundclearance",
        "curb_weight_kg": "dimensionsandweight-kerbweight", "seats": "capacity-seating_capacity",
        "cargo_l": "capacity-bootspace", "fuel_tank_l": "capacity-fuel_tank_capacity",
        "front_suspension": "suspension_brakes_steeringandtyres-front_suspension",
        "rear_suspension": "suspension_brakes_steeringandtyres-rear_suspension",
        "front_brakes": "suspension_brakes_steeringandtyres-front_brake_type",
        "rear_brakes": "suspension_brakes_steeringandtyres-rear_brake_type",
        "steering": "suspension_brakes_steeringandtyres-steering_type",
        "tire_front": "suspension_brakes_steeringandtyres-front_tyres", "tire_rear": "suspension_brakes_steeringandtyres-rear_tyres"}),
}
FILE_OF = {"japan_goonet": "japan"}
HEADER_TOKENS = {"Make", "厂商", "brandName", "naming-make", "Marca", "Brand"}


def build_library() -> list[dict]:
    manifest_rows = []
    sha_of = {r["file"]: r["sha256"] for r in read_manifest()}
    for dataset, (market, sheet, required, fields) in DATASETS.items():
        path = unique_file(FILE_OF.get(dataset, dataset))
        # below the header: fill counters ("1.0", "339.0") and a second header row (Chinese labels,
        # the source's API keys "brandName") are not vehicles
        _, head, rows = read_table(path, sheet, required,
                                   valid=lambda d: not re.fullmatch(r"[\d.]+", str(d.get(required[0])).strip())
                                   and str(d.get(required[0])).strip() not in HEADER_TOKENS)
        records = []
        for r in rows:
            rec = {f: r.get(c) for f, c in fields.items() if r.get(c) not in (None, "", "-")}
            if not rec.get("model"):
                continue
            records.append({"market": market, "source": {"file": path.name, "sheet": sheet, "row": r["_row"]}, **rec})
        target = LIBRARY / market / "teoalida" / f"staging_specs{'' if dataset == FILE_OF.get(dataset, dataset) else '_goonet'}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"dataset": dataset, "market": market, "source_file": path.name, "sheet": sheet,
                                      "note": "library only (Appendix D); never written to the US records",
                                      "fields": list(fields), "records": records}, ensure_ascii=False, indent=1), encoding="utf-8")
        makes = sorted({str(r.get("make")) for r in records})
        manifest_rows.append({"make": ";".join(makes)[:300], "model": f"{len(records)} versions", "generation_or_years": "",
                              "market": market, "market_markers": json.dumps({"database": f"Teoalida {dataset}"}),
                              "source_url": "", "path": str(target.relative_to(WORK.parent)).replace("\\", "/"),
                              "sha256": sha_of.get(path.name, ""), "retrieved_at": "2026-10-03", "pages": len(records)})
        print(dataset, market, len(records), "->", target.relative_to(WORK.parent))
    # Chinese labels: the row under the English header of the China database
    path = unique_file("china")
    rows = sheet_rows(path, "Database")
    head_i = next(i for i, r in enumerate(rows) if r and "Manufacturer" in [str(c).strip() for c in r])
    pairs = {str(zh).strip(): str(en).strip() for en, zh in zip(rows[head_i], rows[head_i + 1])
             if zh not in (None, "") and en not in (None, "") and re.search(r"[一-鿿]", str(zh))}
    (LIBRARY / "CN" / "teoalida" / "dictionary_zh_en.json").write_text(json.dumps(pairs, ensure_ascii=False, indent=1), encoding="utf-8")
    print("zh->en labels", len(pairs))
    # Ravenol's other markets were written by teoalida_ravenol.py
    for market in ("EU", "CN", "RU", "BR", "TR", "UNSPECIFIED"):
        p = LIBRARY / market / "teoalida" / "ravenol.json"
        if p.exists():
            n = len(json.loads(p.read_text(encoding="utf-8"))["records"])
            manifest_rows.append({"make": "BMW", "model": f"{n} Ravenol rows", "generation_or_years": "", "market": market,
                                  "market_markers": json.dumps({"database": "Teoalida ravenol", "makeLabel": f"({market})"}),
                                  "source_url": "", "path": str(p.relative_to(WORK.parent)).replace("\\", "/"),
                                  "sha256": sha_of.get("Ravenol-SAMPLE.xlsx", ""), "retrieved_at": "2026-10-03", "pages": n})
    return manifest_rows


def register(manifest_rows: list[dict]) -> None:
    path = LIBRARY / "manifest.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        keep = [r for r in reader if "/teoalida/" not in r["path"]]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for r in keep + manifest_rows:
            writer.writerow({k: r.get(k, "") for k in fields})


def tuning() -> dict:
    """A.6: the dyno site's "standard" output against our official power/torque, where its
    generation code is one of our generations' platform codes and the engine names a
    designation of the line."""
    from teoalida_accuracy import Tally, designation_fits, load_line, model_label, tokens
    from teoalida_ymmt import make_slug
    from us_tech_lines import lines_for

    path = unique_file("tuning")
    _, head, rows = read_table(path, "Database", ["Make", "Model", "Generation", "Engine"])
    tally = Tally("teoalida/tuning")
    unmatched = defaultdict(int)
    for r in rows:
        make = make_slug(r["Make"])
        if make is None:
            unmatched["make not ours"] += 1
            continue
        gen_code = str(r.get("Generation") or "").split(" - ")[0].strip()
        designation = re.sub(r"\s*\d+\s*hp\s*$", "", str(r.get("Engine") or ""), flags=re.I).strip()
        hp = re.search(r"(\d+)\s*hp", str(r.get("BHP standard") or ""))
        nm = re.search(r"(\d+)\s*Nm", str(r.get("TORQUE standard") or ""))
        found = False
        for line in lines_for(make, include_done=True):
            st = load_line(make, line.slug)
            if not st:
                continue
            codes = {f["generation"]: str(f["value"]) for f in st["facts"] if f["key"] == "platform_code"}
            gens = [g for g in st["generations"] if g["code"] == gen_code or gen_code in [c.strip() for c in codes.get(g["code"], "").split(",")]]
            for g in gens:
                for f in st["facts"]:
                    if f["generation"] != g["code"] or f["display_level"] != "FACT":
                        continue
                    if not designation_fits(designation, model_label(f.get("applicability") or {}), tokens(line.name)):
                        continue
                    if f["key"] == "power_hp" and hp:
                        found = True
                        tally.add("power_hp (EU tuning 'standard' vs our official)", int(hp.group(1)), [(f["value"], f["primary_source"], "")],
                                  f"{make}/{line.slug} {g['code']} {designation}")
        if not found:
            unmatched["no generation/designation of ours with an official value"] += 1
    rep = tally.verdicts()
    out = {"source": "teoalida/tuning", "note": "comparison only (A.6); never written", "fields": rep,
           "unmatched": dict(unmatched), "rows": len(rows)}
    (OUT / "accuracy_tuning.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in rep.items():
        print(k, "compared", v["compared"], "agreed", v["agreed"], v["agreement"])
    print("unmatched", dict(unmatched))
    return out


if __name__ == "__main__":
    register(build_library())
    tuning()

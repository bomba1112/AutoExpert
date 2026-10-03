"""Teoalida "Ravenol" database (scrape of the Ravenol oil finder): fluid capacities, unit codes and
service intervals per vehicle type (next-stage prompt A.2).

Columns used: makeLabel, modelLabel, typeLabel, partName, partCode, capacities, useType, intervals.
productCode / productLabel (Ravenol's own oils) are never used; no viscosity or approval is taken
from product names.

- market from makeLabel: (USA), (USA / CAN) -> US; (EU) -> EU; (CHN) and Chinese joint ventures -> CN;
  (RUS), (BRA), (TUR) -> library; a label without a market -> library (UNSPECIFIED);
- typeLabel "320i xDrive, N20 (2012-2015)": designation, engine code, production years. Production
  years are matched to model years by overlap with the EPA years in which our configurations carry
  that designation; a year two types claim with different values is not assigned (logged);
- capacities "Capacity 8,5 litre" (decimal comma); ranges ("9-10 litre") and "Between min and max."
  are not values; "(Service fill)" / "(Initial fill)" kept as the fill condition;
- intervals + useType -> maintenance items: "Change 10000 miles/ 12 months" (miles -> km by the
  units module, whichever first), "Check … | Change …" two jobs, Normal / Severe conditions,
  "Flexible (max)" = the upper limit of the on-board system, "Flexible (on board maintenance
  system)" = the system with no number, "First change only" = first change only;
- partName qualifiers ("as of 03/2020", "up to production date …", "with differential lock") are
  kept as applicability conditions.

Output (no database writes here):
  data_work/_shared/teoalida/ravenol_us.json            US rows mapped to our lines and model years
  data_work/_library/<MARKET>/teoalida/ravenol.json     other markets (library, never written to the DB)
  data_work/_shared/teoalida/ravenol_unmapped.json      US rows with no line or year match, and ambiguities

  .venv/Scripts/python.exe scripts/teoalida_ravenol.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "backend"))
from app.services.tech_units import convert  # noqa: E402
from teoalida_common import OUT, read_table, row_text, unique_file  # noqa: E402
from us_tech_common import WORK  # noqa: E402
from us_tech_lines import MAKES, lines_for  # noqa: E402

COLUMNS = ["makeLabel", "modelLabel", "typeLabel", "partName", "partCode", "capacities", "useType", "intervals"]
MARKET = [  # (pattern on makeLabel, market)
    (re.compile(r"\((?:USA|USA\s*/\s*CAN|CAN\s*/\s*USA)\)"), "US"),
    (re.compile(r"\(EU\)"), "EU"),
    (re.compile(r"\(CHN\)|Brilliance|\bFAW\b|\bSAIC\b|Dongfeng|Changan|\bGAC\b|Beijing|Brilliance", re.I), "CN"),
    (re.compile(r"\(RUS\)"), "RU"),
    (re.compile(r"\(BRA\)"), "BR"),
    (re.compile(r"\(TUR\)"), "TR"),
]
YEARS = re.compile(r"\((\d{4})\s*-\s*(\d{4})?\s*\)\s*$")
CAPACITY = re.compile(r"^(?P<what>Capacity|Filter capacity)\s+(?P<num>\d+(?:,\d+)?)(?P<range>\s*-\s*\d+(?:,\d+)?)?\s*(?P<unit>litre|liter|l|kg|g)?\s*(?:\((?P<fill>[^)]*)\))?\s*$", re.I)
INTERVAL = re.compile(r"^(?P<action>Change|Check)\s*(?:(?P<dist>\d+)\s*(?P<unit>km|miles))?\s*/?\s*(?:(?P<months>\d+)\s*months)?\s*$", re.I)
BODY_WORDS = {"sedan", "sports", "wagon", "touring", "coupe", "convertible", "gran", "turismo", "gt", "cabrio", "cabriolet", "hatchback", "suv"}
DESIGNATION_NOISE = {"mild-hybrid"}
PART = [  # (pattern on partName, part kind)
    (re.compile(r"^Engine"), "engine"),
    (re.compile(r"^Transmission, automatic"), "transmission_automatic"),
    (re.compile(r"^Transmission, manual"), "transmission_manual"),
    (re.compile(r"^Transmission, semi-automatic"), "transmission_semi_automatic"),
    (re.compile(r"^Hydraulic actuation, gearbox"), "gearbox_hydraulics"),
    (re.compile(r"^Cooling system"), "cooling"),
    (re.compile(r"^Differential, front"), "differential_front"),
    (re.compile(r"^Differential, rear"), "differential_rear"),
    (re.compile(r"^Transfer(?:box|case)"), "transfer_case"),
    (re.compile(r"^Power steering"), "power_steering"),
    (re.compile(r"^Hydraulic (?:brake|clutch)"), "brake_clutch_hydraulics"),
]
# part kind -> (capacity fact key, unit code fact key, maintenance job)
PART_KEYS = {
    "engine": ("engine_oil_capacity_l", "engine_code", "engine_oil_and_filter"),
    "transmission_automatic": ("transmission_fluid_capacity_l", "transmission_code", "automatic_transmission_fluid"),
    "transmission_manual": ("manual_transmission_fluid_capacity_l", "transmission_code", "manual_transmission_fluid"),
    "transmission_semi_automatic": ("transmission_fluid_capacity_l", "transmission_code", "transmission_fluid"),
    "gearbox_hydraulics": (None, None, None),
    "cooling": ("coolant_capacity_l", None, "coolant"),
    "differential_front": ("front_differential_fluid_capacity_l", "front_differential_code", "front_differential_fluid"),
    "differential_rear": ("rear_differential_fluid_capacity_l", "rear_differential_code", "rear_differential_fluid"),
    "transfer_case": ("transfer_case_fluid_capacity_l", "transfer_case_code", "transfer_case_fluid"),
    "power_steering": ("power_steering_fluid_capacity_l", None, "power_steering_fluid"),
    "brake_clutch_hydraulics": (None, None, "brake_fluid"),
}


def market_of(label: str) -> str:
    return next((m for p, m in MARKET if p.search(label or "")), "UNSPECIFIED")


def brand_of(label: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", label or "").strip()


def years_of(label: str) -> tuple[int | None, int | None, str]:
    m = YEARS.search(label or "")
    if not m:
        return None, None, (label or "").strip()
    return int(m.group(1)), int(m.group(2)) if m.group(2) else None, label[:m.start()].strip()


def parse_type(label: str) -> dict:
    start, end, rest = years_of(label)
    engine = None
    if "," in rest:
        rest, engine = [x.strip() for x in rest.rsplit(",", 1)]
    return {"designation": rest, "engine_hint": engine, "production": [start, end]}


def parse_model(label: str) -> dict:
    start, end, rest = years_of(label)
    series, _, codes = rest.partition(",")
    return {"series": series.strip(), "chassis": [c.strip() for c in codes.split("/") if c.strip()],
            "production": [start, end]}


def part_kind(name: str) -> tuple[str | None, str | None]:
    name = (name or "").strip()
    for pattern, kind in PART:
        if pattern.search(name):
            qualifier = name.split(",", 2)[2].strip() if kind.startswith(("transmission", "differential")) and name.count(",") >= 2 \
                else name.split(",", 1)[1].strip() if "," in name and not kind.startswith(("transmission", "differential")) else None
            return kind, qualifier or None
    return None, None


def litres(num: str) -> Decimal:
    return Decimal(num.replace(",", "."))


def parse_capacities(text: str | None) -> tuple[list[dict], list[str]]:
    values, rejected = [], []
    for part in (text or "").split("|"):
        part = part.strip()
        if not part:
            continue
        m = CAPACITY.match(part)
        if not m:
            rejected.append(part)  # "Between min and max." and the like: no value
            continue
        if m.group("range"):
            rejected.append(part)  # a range is not one value
            continue
        unit = (m.group("unit") or "litre").lower()
        if unit in ("kg", "g"):
            rejected.append(part)  # refrigerant masses: not a fluid volume
            continue
        values.append({"what": m.group("what").lower(), "value": float(litres(m.group("num"))),
                       "fill": (m.group("fill") or "").strip().lower() or None, "text": part})
    return values, rejected


def parse_intervals(text: str | None, use: str | None) -> tuple[list[dict], list[str]]:
    """One item per "Change"/"Check" clause; miles converted to km by the units module."""
    use = (use or "").strip()
    base = {"condition": "SEVERE" if use.startswith("Severe") else "NORMAL",
            "occurrence": "FIRST" if use.startswith("First change only") else "EVERY",
            "schedule_system": "ON_BOARD_MONITOR" if use.startswith("Flexible") else "FIXED_INTERVAL",
            "use_type": use or None}
    use_qualifier = use.split(",", 1)[1].strip() if "," in use else None
    if use.startswith("Alternative"):
        return [], [f"{use}: alternative product line, not a schedule"]
    if not text or text == "None":
        if use.startswith("Flexible (on board"):
            return [{**base, "action": "REPLACE", "interval_km": None, "interval_months": None, "max": False,
                     "text": use, "use_qualifier": use_qualifier}], []
        return [], []
    items, rejected = [], []
    for clause in text.split("|"):
        clause = clause.strip()
        m = INTERVAL.match(clause)
        if not m or not (m.group("dist") or m.group("months")):
            rejected.append(clause)
            continue
        km = None
        if m.group("dist"):
            km = int(m.group("dist")) if m.group("unit").lower() == "km" else int(convert(m.group("dist"), "mi", "km").to_integral_value())
        items.append({**base, "action": "INSPECT" if m.group("action").lower() == "check" else "REPLACE",
                      "interval_km": km, "interval_months": int(m.group("months")) if m.group("months") else None,
                      "interval_miles_original": int(m.group("dist")) if m.group("dist") and m.group("unit").lower() == "miles" else None,
                      "max": use.startswith("Flexible (max)"), "text": clause, "use_qualifier": use_qualifier})
    return items, rejected


def tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[\s/]+", (text or "").lower()) if t}


def designation_matches(designation: str, epa_model: str) -> bool:
    d = tokens(designation) - DESIGNATION_NOISE
    e = tokens(epa_model)
    if d == e:
        return True
    return not (d & BODY_WORDS) and d <= e and (e - d) <= BODY_WORDS


def read_rows() -> list[dict]:
    path = unique_file("ravenol")
    _, _, rows = read_table(path, "Database", ["makeLabel", "modelLabel", "typeLabel"],
                            valid=lambda d: isinstance(d.get("makeLabel"), str) and isinstance(d.get("typeLabel"), str))
    seen, out = set(), []
    for r in rows:
        key = tuple(str(r.get(c)) for c in COLUMNS)
        if key in seen:
            continue  # the same vehicle part repeated once per Ravenol product
        seen.add(key)
        out.append(r)
    return out


def our_make(brand: str) -> str | None:
    b = brand.lower().replace("-", " ")
    for slug, meta in MAKES.items():
        if b in {slug.replace("-", " "), str(meta.get("epa", "")).lower().replace("-", " ")}:
            return slug
    return None


def epa_designations(make: str) -> dict:
    """line slug -> year -> list of (configuration_key, epa model names)."""
    out = defaultdict(lambda: defaultdict(list))
    for line in lines_for(make, include_done=True):
        path = WORK / make / "staging" / line.slug / "staging.json"
        if not path.exists():
            continue
        staging = json.loads(path.read_text(encoding="utf-8"))
        for cfg in staging.get("configurations", []):
            names = [v.get("epa_model") for v in cfg.get("epa_vehicles", []) if v.get("epa_model")]
            out[line.slug][cfg["year"]].append((cfg["configuration_key"], names))
    return out


def map_type(make: str, designation: str, production: list, epa: dict) -> dict:
    """{line: {year: [configuration keys]}} for the model years where our configurations carry the
    designation and the type was in production (overlap of production and model years)."""
    start, end = production
    out = defaultdict(dict)
    if start is None:
        return out
    end = end or 9999
    for line, years in epa.items():
        for year, cfgs in years.items():
            if not (start <= year <= end):
                continue
            keys = [k for k, names in cfgs if any(designation_matches(designation, n) for n in names)]
            if keys:
                out[line][year] = keys
    return out


def main() -> int:
    path = unique_file("ravenol")
    rows = read_rows()
    by_market = defaultdict(list)
    epa_cache = {}
    us_records, unmapped = [], []
    for r in rows:
        market = market_of(r["makeLabel"])
        brand = brand_of(r["makeLabel"])
        model, typ = parse_model(r["modelLabel"]), parse_type(r["typeLabel"])
        kind, qualifier = part_kind(r.get("partName"))
        caps, caps_rejected = parse_capacities(r.get("capacities"))
        items, items_rejected = parse_intervals(r.get("intervals"), r.get("useType"))
        rec = {"row": r["_row"], "market": market, "brand": brand, "model": model, "type": typ,
               "part": r.get("partName"), "part_kind": kind, "part_qualifier": qualifier,
               "part_code": (str(r["partCode"]).strip() if r.get("partCode") not in (None, "", "None") else None),
               "capacities": caps, "capacities_rejected": caps_rejected,
               "intervals": items, "intervals_rejected": items_rejected,
               "quote": row_text(r, COLUMNS)}
        if market != "US":
            by_market[market].append(rec)
            continue
        make = our_make(brand)
        if make is None:
            unmapped.append({**rec, "reason": "make not in our list"})
            continue
        if make not in epa_cache:
            epa_cache[make] = epa_designations(make)
        mapping = map_type(make, typ["designation"], typ["production"], epa_cache[make])
        if not mapping:
            unmapped.append({**rec, "make": make, "reason": "no line/model year of ours carries this designation in its production years"})
            continue
        us_records.append({**rec, "make": make, "lines": {line: years for line, years in mapping.items()}})
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {"source_file": path.name, "rows_read": len(rows)}
    (OUT / "ravenol_us.json").write_text(json.dumps({**meta, "records": us_records}, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "ravenol_unmapped.json").write_text(json.dumps({**meta, "records": unmapped}, ensure_ascii=False, indent=1), encoding="utf-8")
    for market, recs in by_market.items():
        target = WORK / "_library" / market / "teoalida" / "ravenol.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({**meta, "market": market, "note": "library only; never written to the US records",
                                      "records": recs}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("rows", len(rows), "US mapped", len(us_records), "US unmapped", len(unmapped),
          {m: len(v) for m, v in by_market.items()})
    return 0


ENGINE_CODE = re.compile(r"\b([BNSM]\d{2}[A-Z]?\d{0,2}[A-Z]?\d?[A-Z]?\d?)\b")
GEARS = re.compile(r"(\d{1,2})\s*/\s*\d\b|(\d{1,2})HP|(\d{1,2})[- ]speed|\(\w*?(\d{1,2})\)", re.I)


def official_engine_codes(staging: dict, year: int, designation: str) -> list:
    """Engine codes the official facts name for this model year and designation: the engine of
    ENGINE-level press facts, and codes written in engine descriptions."""
    from teoalida_accuracy import designation_fits, edition_fits, model_label

    out = []
    for f in staging["facts"]:
        if f["display_level"] != "FACT" or not (f["years"][0] <= year <= f["years"][1]):
            continue
        app = f.get("applicability") or {}
        if not designation_fits(designation, model_label(app)) or not edition_fits(designation, app.get("edition")):
            continue
        codes = []
        if f["level"] == "ENGINE" and f.get("engine"):
            codes.append(f["engine"])
        if f["key"] == "engine_description":
            codes += ENGINE_CODE.findall(str(f["value"]))
        out += [(c, f["primary_source"], (f.get("applicability") or {}).get("variant") or "") for c in codes]
    return out


def gears(text: str | None) -> int | None:
    m = GEARS.search(text or "")
    return int(next(g for g in m.groups() if g)) if m else None


def check() -> dict:
    """A.8 for Ravenol: capacities and unit codes against the official values of the same line,
    model year and designation; intervals against official maintenance items of the line."""
    from teoalida_accuracy import Tally, load_line, official_values, write_report

    data = json.loads((OUT / "ravenol_us.json").read_text(encoding="utf-8"))
    tally = Tally("teoalida/ravenol")
    done = set()
    staging_cache = {}
    for rec in data["records"]:
        kind = rec["part_kind"]
        if kind not in PART_KEYS:
            continue
        cap_key, code_key, job = PART_KEYS[kind]
        for line, years in rec["lines"].items():
            st = staging_cache.setdefault((rec["make"], line), load_line(rec["make"], line))
            cfg_by_key = {c["configuration_key"]: c for c in st["configurations"]}
            for year, cfg_keys in years.items():
                year = int(year)
                cfg = cfg_by_key.get(cfg_keys[0])
                where = f"{rec['make']}/{line} {year} {rec['type']['designation']}"
                for cap in rec["capacities"]:
                    if cap_key and cap["what"] == "capacity" and cap["fill"] in (None, "service fill"):
                        marker = (where, cap_key, cap["value"], rec["part"])
                        if marker not in done:
                            done.add(marker)
                            tally.add(cap_key, cap["value"], official_values(st, cap_key, year, rec["type"]["designation"], cfg), where)
                if kind == "engine" and rec["part_code"]:
                    marker = (where, "engine_code", rec["part_code"])
                    if marker not in done:
                        done.add(marker)
                        officials = [(c[:3], s, v) for c, s, v in official_engine_codes(st, year, rec["type"]["designation"])]
                        tally.add("engine_code (family, first 3 characters)", rec["part_code"][:3], officials, where)
                if kind.startswith("transmission_automatic") and rec["part_code"] and cfg:
                    marker = (where, "gears", rec["part_code"])
                    if marker not in done and gears(rec["part_code"]):
                        done.add(marker)
                        officials = [(gears(cfg.get("epa_trany")), "epa", cfg.get("epa_trany"))] if gears(cfg.get("epa_trany")) else []
                        tally.add("transmission_code (gear count vs EPA transmission)", gears(rec["part_code"]), officials, where)
                for item in rec["intervals"]:
                    if not job or item["interval_km"] is None and item["interval_months"] is None:
                        continue
                    marker = (where, job, item["action"], item["interval_km"], item["interval_months"], item["condition"])
                    if marker in done:
                        continue
                    done.add(marker)
                    officials = [((i.get("interval_km"), i.get("interval_months")), i.get("primary_source"), i.get("schedule_system"))
                                 for i in st.get("maintenance", [])
                                 if i["job"] == job and i["action"] == item["action"] and i["condition"] == item["condition"]
                                 and i["years"][0] <= year <= i["years"][1] and i.get("display_level") == "FACT"]
                    tally.add(f"interval {job} {item['action'].lower()}", (item["interval_km"], item["interval_months"]),
                              officials, where)
    return write_report("ravenol", tally, {"records": len(data["records"])})


# accuracy-report field -> what is written for it
WRITE_FIELDS = {
    "engine_code (family, first 3 characters)": "engine_code",
    "transmission_code (gear count vs EPA transmission)": "transmission_code",
}
PUBLISHER = "Teoalida - Ravenol oil-finder database (secondary; owner's sample)"


def stage() -> dict:
    """Facts for the fields that passed the accuracy check, as Teoalida documents per line,
    designation and value. A model year that two types of one designation give different values
    for is not assigned (the ambiguity is logged)."""
    from teoalida_common import clear_docs, row_quote, write_doc, write_pagetext

    report = json.loads((OUT / "accuracy_ravenol.json").read_text(encoding="utf-8"))
    allowed = {WRITE_FIELDS[k] for k, v in report["fields"].items() if v["write"] and k in WRITE_FIELDS}
    data = json.loads((OUT / "ravenol_us.json").read_text(encoding="utf-8"))
    path = unique_file("ravenol")
    sha = write_pagetext(path, "Database", ["makeLabel", "modelLabel", "typeLabel"])
    _, head, rows = read_table(path, "Database", ["makeLabel", "modelLabel", "typeLabel"])
    by_row = {r["_row"]: r for r in rows}
    claims = defaultdict(lambda: defaultdict(list))  # scope -> value -> [(record, year)]
    for rec in data["records"]:
        kind, code = rec["part_kind"], rec["part_code"]
        if not code:
            continue
        if kind == "engine" and "engine_code" in allowed:
            key, value = "engine_code", re.sub(r"\s*\(.*\)\s*$", "", code).strip()
            app = {"variant": rec["type"]["designation"]}
            note = re.search(r"\(([^)]*)\)", code)
            if note:
                app["engine_note"] = note.group(1)
        elif kind and kind.startswith("transmission_") and "transmission_code" in allowed:
            key, value = "transmission_code", code
            app = {"variant": rec["type"]["designation"], "transmission": kind.split("_", 1)[1].replace("_", "-")}
            if rec["part_qualifier"]:
                app["condition"] = rec["part_qualifier"]
        else:
            continue
        for line, years in rec["lines"].items():
            for year in years:
                scope = (rec["make"], line, key, json.dumps(app, sort_keys=True))
                claims[scope][value].append((rec, int(year)))
    ambiguous, groups = [], defaultdict(list)
    for scope, values in claims.items():
        by_year = defaultdict(set)
        for value, uses in values.items():
            for _, year in uses:
                by_year[year].add(value)
        for value, uses in values.items():
            for rec, year in uses:
                if len(by_year[year]) > 1:
                    ambiguous.append({"scope": list(scope), "year": year, "values": sorted(by_year[year]),
                                      "reason": "two Ravenol types of this designation give different values for this model year; not assigned"})
                    continue
                groups[(scope, value)].append((rec, year))
    removed = clear_docs("ravenol")
    written = 0
    for ((make, line, key, app_json), value), uses in sorted(groups.items()):
        app = json.loads(app_json)
        years = sorted({y for _, y in uses})
        rows_used = sorted({rec["row"] for rec, _ in uses})
        facts = []
        for row_no in rows_used:
            raw = by_row[row_no]
            facts.append({"key": key, "value": value, "unit": None, "page": row_no,
                          "quote": row_quote(raw, head, ["typeLabel", "partName", "partCode"]),
                          "row": f"Ravenol row {row_no}", "label": key.replace("_", " "), "engine_text": None,
                          "variant": app["variant"], **({"applicability_extra": {k: v for k, v in app.items() if k != "variant"}}
                                                       if len(app) > 1 else {})})
        digest = __import__("hashlib").sha1(f"{line}|{key}|{app_json}|{value}".encode()).hexdigest()[:10]
        write_doc(make, "ravenol", f"teoalida-ravenol-{digest}", [f"{make}/{line}"], years, facts, path, sha,
                  f"Teoalida Ravenol database: {app['variant']} — {key} {value}", PUBLISHER, "2026-10-03")
        written += 1
    out = {"allowed_fields": sorted(allowed), "documents": written, "removed_previous": removed, "ambiguous": ambiguous}
    (OUT / "ravenol_stage.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("staged documents", written, "ambiguous year claims", len(ambiguous), "fields", sorted(allowed))
    return out


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("parse", "all"):
        main()
    if step in ("check", "all"):
        report = check()
        for key, r in report["fields"].items():
            print(f"{key}: compared {r['compared']}, agreed {r['agreed']}, no official {r['no_official']} -> {r['verdict']}")
    if step in ("stage", "all"):
        stage()

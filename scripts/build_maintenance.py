"""Structured maintenance items (maintenance_schedule_items) from official schedules.

Source handled here: Mopar maintenance schedules (official JSON published for Jeep owners on
mopardocs.azureedge.net / vehicleinfo.mopar.com, downloaded by collect_official.py). Each plan
lists mileage points and, per service, the indexes of the points where it is due. One item
per job and action:
  - points d, 2d, 3d ... -> EVERY d miles;
  - first point f then a constant step s -> FIRST f + SUBSEQUENT every s;
  - a single point -> FIRST (the schedule lists it once within its mileage horizon);
  - a service text that states its own interval ("10 years or 150,000 miles (240,000 km)")
    is taken from the text (km as printed), the point list only noted;
  - oil changes "as indicated by the oil change indicator" -> OIL_LIFE_MONITOR, no interval.
Miles are converted with the fixed factor (KM_PER_MI) and kept in interval_miles_original.

Generation of a schedule: by its own model code when the title names one (MODEL_CODES: Grand
Cherokee "WK (2022 carryover WK2)" -> WK-2011 including MY2022, "Grand Cherokee L / Grand
Cherokee (WL)" -> US2022+ including MY2021), else by model year. When two schedules of
different editions (title without year/make: "Grand Cherokee", "Grand Cherokee SRT", "Grand
Cherokee 4xe", ...) cover one model year of a line, the items of that year carry
{"edition": <edition>}. Two schedules of one edition and year that give the same job different
intervals (2019 Cherokee 123.json / 124.json) are ambiguous: no item for that year, a gap.

Output: data_work/<make>/staging/<line>/maintenance.json (items + sources + gaps), merged by
build_us_batch_staging.py and written by load_us_tech_facts.py.

  .venv/Scripts/python.exe scripts/build_maintenance.py jeep
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, ROOT, WORK  # noqa: E402
from us_tech_lines import BY_KEY, lines_for  # noqa: E402

sys.path.insert(0, str(ROOT / "backend"))
from app.services.tech_units import convert  # noqa: E402

JOBS = [  # (job, pattern) on the service text
    ("engine_oil_and_filter", r"oil and (?:oil )?filter|change (?:the )?(?:engine )?oil"),
    ("engine_air_filter", r"engine air (?:cleaner )?filter|air cleaner (?:filter|element)"),
    ("cabin_air_filter", r"cabin air filter|air conditioning/cabin|a/c (?:cabin )?filter|air conditioning filter"),
    ("spark_plugs", r"spark plugs?"),
    ("engine_coolant", r"engine coolant|coolant"),
    ("brake_fluid", r"brake fluid"),
    ("manual_transmission_fluid", r"manual transmission fluid"),
    ("transmission_fluid", r"automatic transmission fluid|transmission fluid|transaxle fluid"),
    ("transfer_case_fluid", r"transfer case"),
    ("differential_fluid", r"axle fluid|differential|power transfer unit|\bPTU\b|rear drive module|rear drive assembly|\bRDA\b"),
    ("timing_belt", r"timing belt"),
    ("accessory_drive_belt", r"accessory drive belt|drive belt|serpentine"),
    ("tire_rotation", r"rotate the tires|tire rotation|rotate tires"),
    ("pcv_valve", r"\bPCV\b"),
    ("fuel_filter", r"fuel filter"),
    ("brakes", r"brake (?:linings|pads|shoes|rotors)|brake linings"),
    ("parking_brake", r"adjust the parking brake"),
    ("cv_joints", r"CV joints?"),
    ("front_suspension", r"suspension|tie rod|ball joints?"),
    ("exhaust_system", r"exhaust"),
    ("battery", r"battery"),
    ("cooling_system", r"cooling system"),
    ("diesel_exhaust_fluid", r"diesel exhaust fluid|\bDEF\b"),
]


def job_of(text: str) -> str | None:
    for job, pattern in JOBS:
        if re.search(pattern, text, re.I):
            return job
    return None


def action_of(text: str) -> str:
    t = text.lower()
    if re.match(r"\s*(inspect|check)", t):
        return "INSPECT"
    if re.search(r"\brotate\b", t):
        return "ROTATE"
    if re.search(r"\badjust\b", t):
        return "ADJUST"
    if re.search(r"\bclean\b", t) and not re.search(r"replace|change|flush", t):
        return "CLEAN"
    if re.search(r"replace|change|flush|drain and refill|\bdrain\b.*\brefill\b", t):  # "Drain the transfer case and refill."
        return "REPLACE"
    return "INSPECT"


def miles_to_km(miles: int) -> int:
    return int(convert(miles, "mi", "km"))


def stated_interval(text: str) -> dict | None:
    """'10 years or 150,000 miles (240,000 km) whichever comes first' as printed."""
    years = re.search(r"(\d+)\s*years?", text, re.I)
    months = re.search(r"(\d+)\s*months?", text, re.I)
    miles = re.search(r"([\d,]{4,})\s*miles", text, re.I)
    km = re.search(r"\(?([\d,]{4,})\s*km\)?", text, re.I)
    if not (miles or km or years or months):
        return None
    out = {}
    if miles:
        out["interval_miles_original"] = int(miles.group(1).replace(",", ""))
        out["interval_km"] = int(km.group(1).replace(",", "")) if km else miles_to_km(out["interval_miles_original"])
    elif km:
        out["interval_km"] = int(km.group(1).replace(",", ""))
    if years:
        out["interval_months"] = int(years.group(1)) * 12
    elif months:
        out["interval_months"] = int(months.group(1))
    out["rule"] = "WHICHEVER_FIRST" if re.search(r"whichever comes first|whichever occurs first", text, re.I) else None
    return out


def from_points(points: list[int]) -> list[dict] | None:
    points = sorted(set(points))
    if not points:
        return None
    if len(points) == 1:
        return [{"occurrence": "FIRST", "miles": points[0]}]
    steps = {b - a for a, b in zip(points, points[1:])}
    if len(steps) != 1:
        return None
    step = steps.pop()
    if points[0] == step:
        return [{"occurrence": "EVERY", "miles": step}]
    return [{"occurrence": "FIRST", "miles": points[0]}, {"occurrence": "SUBSEQUENT", "miles": step}]


def component_of(text: str) -> dict:
    """PTU and RDA fluids are both differential_fluid; the unit tells the two rows apart."""
    if re.search(r"power transfer unit|\bPTU\b", text):
        return {"component": "power transfer unit (PTU)"}
    if re.search(r"rear drive assembly|\bRDA\b", text):
        return {"component": "rear drive assembly (RDA)"}
    if re.search(r"rear drive module", text):
        return {"component": "rear drive module"}
    return {}


def engines_of(title: str) -> str | None:
    found = re.findall(r"\d\.\dL?", title)
    if found:
        return "/".join(f"{x.rstrip('L')}L" for x in found)
    if re.search(r"\bSRT\b", title):
        return "SRT"
    return None


def mopar_docs(make: str) -> list[dict]:
    path = WORK / "_shared" / "manifest_official" / "mopardocs.azureedge.net.csv"
    rows = []
    for host_manifest in (path, WORK / "_shared" / "manifest_official" / "vehicleinfo.mopar.com.csv"):
        if not host_manifest.exists():
            continue
        with host_manifest.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["make"] == make and row["status"] == "ok" and row["path"].endswith(".json"):
                    rows.append(row)
    return rows


MODEL_CODES = {  # line -> model code printed in the schedule title -> generation code of the line
    "jeep/grand-cherokee": {"WK": "WK-2011", "WL": "US2022+"},
}


def model_code(title: str) -> str | None:
    """'2022 Jeep Grand Cherokee WK (2022 carryover WK2)' -> WK; '... Grand Cherokee L / Grand
    Cherokee (WL)' -> WL; no code printed -> None."""
    m = re.search(r"\b(WK|WL)2?\b", title)
    return m.group(1) if m else None


def edition_of(title: str) -> str:
    """'2021 Jeep Grand Cherokee L / Grand Cherokee (WL) - Maintenance Schedule (also listed ...)'
    -> 'Grand Cherokee L / Grand Cherokee (WL)'."""
    name = re.sub(r"\s+-\s+Maintenance Schedule.*$", "", title)
    return re.sub(r"^\d{4}\s+\w+\s+", "", name).strip()


def generation_of(line_key: str, row: dict, year: int, gens: list[dict]) -> tuple[str | None, str]:
    code = model_code(row["title"])
    mapped = MODEL_CODES.get(line_key, {}).get(code) if code else None
    if mapped and any(g["code"] == mapped for g in gens):
        return mapped, f"model code {code} in the schedule title"
    return next((g["code"] for g in gens if g["start_year"] <= year <= g["end_year"]), None), "model year"


def build(make: str) -> int:
    by_line = defaultdict(list)
    for row in mopar_docs(make):
        for line in [f"{make}/{x}" if "/" not in x else x for x in row["lines"].split(";") if x]:
            by_line[line].append(row)
    for line_key, rows in by_line.items():
        line = BY_KEY.get(line_key)
        staging_path = WORK / make / "staging" / line.slug / "staging.json"
        if not staging_path.exists():
            continue
        gens = json.loads(staging_path.read_text(encoding="utf-8"))["generations"]
        sources, gaps = {}, []
        observed = defaultdict(lambda: defaultdict(list))  # scope -> year -> cites
        editions = defaultdict(set)  # model year -> editions of the schedules covering it
        for row in rows:
            for year in [int(y) for y in row["years"].split(";") if y]:
                editions[year].add(edition_of(row["title"]))
        for row in rows:
            plans = json.loads((RAW_ROOT / row["path"]).read_text(encoding="utf-8"))
            plans = plans if isinstance(plans, list) else [plans]
            source_key = "mopar-" + hashlib.sha1(row["url"].encode()).hexdigest()[:10]
            for year in [int(y) for y in row["years"].split(";") if y]:
                gen, _ = generation_of(line_key, row, year, gens)
                if gen is None:
                    continue
                shared = len(editions[year]) > 1
                for plan in plans:
                    engine = engines_of(plan.get("title", ""))
                    applicability = {"plan": plan.get("title", "").strip(), **({"engine": engine} if engine else {})}
                    if re.search(r"SRT", row["title"]) and "engine" not in applicability:
                        applicability["engine"] = "SRT"
                    if shared:
                        applicability["edition"] = edition_of(row["title"])
                    for anc in plan.get("ancillary", []):
                        if re.search(r"oil change indicator|oil change interval", anc.get("title", ""), re.I):
                            for service in anc.get("services", []):
                                if job_of(service) == "engine_oil_and_filter":
                                    item = {"job": "engine_oil_and_filter", "action": "REPLACE", "occurrence": "EVERY",
                                            "schedule_system": "OIL_LIFE_MONITOR", "condition": "NORMAL"}
                                    scope = json.dumps([gen, item, applicability], sort_keys=True)
                                    observed[scope][year].append({"source": source_key, "quote": f"{anc['title']} {service}",
                                                                  "locator": anc["title"][:200]})
                    points_table = []
                    for i in plan.get("maintenance", {}).get("intervals", []):
                        raw = str(i.get("distance") or "").replace(",", "").strip()
                        points_table.append(int(raw) if raw.isdigit() else None)  # e.g. "Axle ..." columns
                    for service in plan.get("maintenance", {}).get("services", []):
                        text = service.get("description", "")
                        job = job_of(text)
                        if not job or not service.get("intervals"):
                            continue
                        action = action_of(text)
                        points = [points_table[i] for i in service["intervals"] if i < len(points_table)]
                        if any(p is None for p in points):
                            gaps.append({"scope": f"{line_key} MY{year}", "field": f"maintenance {job}",
                                         "reason": "schedule column is not a mileage; not converted"})
                            continue
                        stated = stated_interval(text)
                        if stated and (stated.get("interval_km") or stated.get("interval_months")):
                            occurrence = "FIRST" if re.search(r"\bat\b|first", text, re.I) and not re.search(r"\bevery\b", text, re.I) else "EVERY"
                            entries = [{"occurrence": occurrence, **stated, "note": f"schedule lists it at {points} miles"}]
                        else:
                            shape = from_points(points)
                            if shape is None:
                                gaps.append({"scope": f"{line_key} MY{year}", "field": f"maintenance {job}",
                                             "reason": f"irregular points {points} in the official schedule; not converted"})
                                continue
                            entries = [{"occurrence": s["occurrence"], "interval_miles_original": s["miles"],
                                        "interval_km": miles_to_km(s["miles"]), "interval_months": None, "rule": None,
                                        "note": "single listing within the schedule's mileage horizon" if s["occurrence"] == "FIRST" and len(shape) == 1 else None}
                                       for s in shape]
                        condition = "SEVERE" if re.search(r"severe|police|taxi|fleet|towing|off-?road", text, re.I) else "NORMAL"
                        text_engine = engines_of(text)
                        service_applicability = {**applicability, **({"engine": text_engine} if text_engine else {}), **component_of(text)}
                        for entry in entries:
                            item = {"job": job, "action": action, "condition": condition, "schedule_system": "FIXED_INTERVAL",
                                    **{k: entry.get(k) for k in ("occurrence", "interval_km", "interval_months",
                                                                  "interval_miles_original", "rule")},
                                    "note": entry.get("note")}
                            scope = json.dumps([gen, item, service_applicability], sort_keys=True)
                            observed[scope][year].append({"source": source_key, "quote": text, "locator": f"service: {text[:150]}"})
            sources[source_key] = {
                "key": source_key, "kind": "json_file", "path": "rawstore:" + row["path"], "url": row["url"],
                "sha256": row["sha256"], "retrieved_at": row["retrieved_at"], "tier": "A",
                "source_type": "MAINTENANCE_SCHEDULE_OFFICIAL", "registry": f"factory-{make}-us",
                "title": row["title"], "publisher": "FCA US / Mopar (official maintenance schedule data)",
                "authenticity": "OFFICIAL_PUBLISHER", "edition": "US",
                "model_year": int(row["years"].split(";")[0]) if row["years"] else None,
            }
        drop_ambiguous(line_key, observed, sources, gaps)
        items = []
        for scope, by_year in observed.items():
            if not by_year:
                continue
            gen, item, applicability = json.loads(scope)
            years = sorted(by_year)
            runs, run = [], [years[0]]
            for y in years[1:]:
                if y == run[-1] + 1:
                    run.append(y)
                else:
                    runs.append(run)
                    run = [y]
            runs.append(run)
            for run in runs:
                cites = [c for y in run for c in by_year[y]]
                digest = hashlib.sha1(scope.encode()).hexdigest()[:8]
                items.append({
                    "id": f"{line.slug}-{gen}-mnt-{item['job']}-{digest}-{run[0]}",
                    "generation": gen, "years": [run[0], run[-1]], "engine": None, "applicability": applicability,
                    **item, "max_interval_km": None, "max_interval_months": None,
                    "cites": cites, "primary_source": cites[0]["source"], "display_level": "FACT", "confidence": "HIGH",
                })
        out = WORK / make / "staging" / line.slug / "maintenance.json"
        out.write_text(json.dumps({"sources": sources, "items": items, "gaps": gaps}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(line_key, "items", len(items), "sources", len(sources), "gaps", len(gaps))
    return 0


def drop_ambiguous(line_key: str, observed: dict, sources: dict, gaps: list) -> None:
    """One scope (generation, job, action, condition, occurrence, applicability) must have one
    interval per model year. When the schedules covering a year give it different intervals
    (and no edition or engine tells them apart) the year is not written for that scope: gap."""
    groups = defaultdict(list)  # (base scope, year) -> scopes
    for scope, by_year in observed.items():
        gen, item, applicability = json.loads(scope)
        base = {k: v for k, v in item.items() if k not in ("interval_km", "interval_months", "interval_miles_original", "rule", "note")}
        for year in by_year:
            groups[(json.dumps([gen, base, applicability], sort_keys=True), year)].append(scope)
    for (base, year), scopes in groups.items():
        intervals = {json.dumps([json.loads(s)[1].get(k) for k in ("interval_km", "interval_months")]) for s in scopes}
        if len(intervals) < 2:
            continue
        gen, item, applicability = json.loads(base)
        found = []
        for s in scopes:
            it = json.loads(s)[1]
            titles = sorted({sources[c["source"]]["title"] + f" ({sources[c['source']]['path'].rsplit('/', 1)[-1]})"
                             for c in observed[s][year]})
            found.append(f"{it.get('interval_miles_original') or it.get('interval_km')} mi / {it.get('interval_months')} mo in {'; '.join(titles)}")
            del observed[s][year]
        gaps.append({"scope": f"{line_key} MY{year}", "field": f"maintenance {item['job']} {item['condition']} {item['occurrence']}",
                     "reason": f"schedules of the same edition give different intervals ({' | '.join(found)}); ambiguous, not converted"})


if __name__ == "__main__":
    sys.exit(build(sys.argv[1]))

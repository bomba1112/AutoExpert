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
    ("cabin_air_filter", r"cabin air filter|air conditioning/cabin|a/c (?:cabin )?filter"),
    ("spark_plugs", r"spark plugs?"),
    ("engine_coolant", r"engine coolant|coolant"),
    ("brake_fluid", r"brake fluid"),
    ("transmission_fluid", r"automatic transmission fluid|transmission fluid|transaxle fluid"),
    ("transfer_case_fluid", r"transfer case"),
    ("differential_fluid", r"axle fluid|differential|power transfer unit|\bPTU\b|rear drive module"),
    ("timing_belt", r"timing belt"),
    ("accessory_drive_belt", r"accessory drive belt|drive belt|serpentine"),
    ("tire_rotation", r"rotate the tires|tire rotation|rotate tires"),
    ("pcv_valve", r"\bPCV\b"),
    ("fuel_filter", r"fuel filter"),
    ("brakes", r"brake (?:linings|pads|shoes|rotors)|brake linings"),
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
    if re.search(r"replace|change|flush|drain and refill", t):
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
        for row in rows:
            plans = json.loads((RAW_ROOT / row["path"]).read_text(encoding="utf-8"))
            plans = plans if isinstance(plans, list) else [plans]
            source_key = "mopar-" + hashlib.sha1(row["url"].encode()).hexdigest()[:10]
            for year in [int(y) for y in row["years"].split(";") if y]:
                gen = next((g["code"] for g in gens if g["start_year"] <= year <= g["end_year"]), None)
                if gen is None:
                    continue
                for plan in plans:
                    engine = engines_of(plan.get("title", ""))
                    applicability = {"plan": plan.get("title", "").strip(), **({"engine": engine} if engine else {})}
                    if re.search(r"SRT", row["title"]) and "engine" not in applicability:
                        applicability["engine"] = "SRT"
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
                        service_applicability = {**applicability, **({"engine": text_engine} if text_engine else {})}
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
        items = []
        for scope, by_year in observed.items():
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


if __name__ == "__main__":
    sys.exit(build(sys.argv[1]))

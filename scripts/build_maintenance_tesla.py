"""Tesla maintenance intervals from the factory owner's manuals, section "Maintenance >
Service Intervals" (copies hosted by carmans.net; tesla.com refuses scripted clients, see
manifest_official/www.tesla.com.csv, status skipped).

Tesla prints a short list: "Your vehicle should generally be serviced on an as-needed basis.
However, Tesla recommends the following maintenance items and intervals ...":
  • Brake fluid health check every 2 years (replace if necessary) [or, if the vehicle is used
    for towing, replace the brake fluid every 2 years]      -> INSPECT 24 mo [+ SEVERE REPLACE]
  • A/C desiccant bag replacement every N years             -> REPLACE
  • Cabin air filter replacement every N years [(or 3 years for HEPA filter, if equipped)]
  • HEPA filter(s) [and carbon filters] replacement every 3 years -> cabin filter, {"filter": ...}
  • Clean and lubricate brake calipers every year or 12,500 miles (20,000 km) if in an area
    where roads are salted during winter                    -> SEVERE CLEAN, operating condition
  • Rotate tires every 6,250 miles (10,000 km) or if tread depth difference is 2/32 in (1.5 mm)
    or greater                                               -> ROTATE (2020 manuals print a range
    "every 10,000-12,000 miles (16,000-20,000 km)": the lower bound is written, the range is in
    the note)
"Battery coolant does not need to be replaced for the life of your vehicle" gives no interval
(gap). Electric drive: no engine oil, no OIL_LIFE_MONITOR.

Edition: the carmans copies carry no quarts/gallons (no engine), so the generic edition check of
extract_manual_facts.py leaves them UNKNOWN; a copy is used only when its cover reads
"North America" and it prints the US "Reporting Safety Defects" text (NHTSA). The
mycarusermanual.com Tesla editions are not used: edition_markets.json classifies none of them US
(model-3 2017-2023 UNKNOWN, model-y 2023 GENERAL). Pass --strict-market to use only documents
whose extracted edition_market is US (then no Tesla document qualifies).

Output: data_work/tesla/staging/<line>/maintenance_owner_manual.json (maintenance_common).

  .venv/Scripts/python.exe scripts/build_maintenance_tesla.py [--strict-market]
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maintenance_common import (  # noqa: E402
    gen_for, generations_of, item, merge_years, norm, our_lines, page_text, pdf_source, write,
)
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

MAKE = "tesla"
REGISTRY = "factory-tesla-us"
NAME = "owner_manual"
CARMANS_MANIFEST = WORK / "_shared" / "manifest_carmans.csv"
MARKETS = WORK / "_mcum" / "edition_markets.json"
NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
N = r"(\d{1,2}|one|two|three|four|five|six)"
DIST = re.compile(r"(?P<mi>\d{1,3}(?:,\d{3})+|\d{4,6})(?:-(?P<mi2>\d{1,3}(?:,\d{3})+|\d{4,6}))? miles\s*\("
                  r"(?P<km>\d{1,3}(?:,\d{3})+|\d{4,6})(?:-(?P<km2>\d{1,3}(?:,\d{3})+|\d{4,6}))? km\)")


def months(n: str, unit: str = "years") -> int:
    v = int(n) if n.isdigit() else NUMBERS[n.lower()]
    return v * 12 if unit.startswith("year") else v


def number(text: str) -> int:
    return int(text.replace(",", ""))


def documents(strict: bool) -> list[dict]:
    docs = []
    with CARMANS_MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if row["make"] != MAKE or row["kind"] != "pdf" or row["status"] != "ok":
            continue
        extracted = WORK / MAKE / "extracted" / f"carmans-{row['post']}.json"
        info = json.loads(extracted.read_text(encoding="utf-8")) if extracted.exists() else {}
        docs.append({"key": f"carmans-{row['post']}-maintenance", "line": row["line"].split("/")[-1], "years": [int(row["year"])],
                     "title": f"{row['year']} Tesla {row['line'].split('/')[-1].replace('-', ' ').title()} owner's manual "
                              f"(copy of the factory manual, carmans.net)",
                     "path": RAW_ROOT / row["path"], "url": row["url"], "sha256": row["sha256"], "retrieved_at": row["retrieved_at"],
                     "market": info.get("edition_market"), "strict": strict})
    return docs


def us_edition(flat: list[str]) -> tuple[bool, str]:
    cover = " ".join(flat[:3])
    na = "North America" in cover
    nhtsa = any(re.search(r"Reporting Safety Defects", t) and re.search(r"National Highway Traffic Safety Administration|NHTSA", t)
                for t in flat)
    return na and nhtsa, f"cover 'North America': {na}; US 'Reporting Safety Defects' (NHTSA) text: {nhtsa}"


def bullets_of(page: str) -> list[str]:
    """The bullets of the Service Intervals list (each joined over its lines)."""
    lines = [ln.strip() for ln in page.splitlines()]
    start = next((i for i, ln in enumerate(lines) if ln.startswith("Service Intervals")), None)
    if start is None:
        return []
    out, cur = [], None
    for ln in lines[start + 1:]:
        if re.match(r"^(NOTE|Note):|^Schedule Service|^Daily Checks", ln):
            break
        if ln.startswith("•"):
            if cur:
                out.append(norm(cur))
            cur = ln[1:].strip()
        elif cur is not None:
            cur += " " + ln
    if cur:
        out.append(norm(cur))
    return out


def entries_of(bullets: list[str]) -> tuple[list[dict], list[str]]:
    out, unparsed = [], []
    for b in bullets:
        e = None
        if m := re.match(r"Brake fluid health check every " + N + r" years?", b, re.I):
            out.append({"job": "brake_fluid", "action": "INSPECT", "condition": "NORMAL", "app": {}, "months": months(m.group(1)),
                        "dist": None, "note": "replace if necessary (as printed)", "quote": b})
            if t := re.search(r"if the vehicle is used for towing, replace the brake fluid every " + N + r" years?", b, re.I):
                out.append({"job": "brake_fluid", "action": "REPLACE", "condition": "SEVERE",
                            "app": {"operating_condition": "vehicle used for towing"}, "months": months(t.group(1)), "dist": None,
                            "note": None, "quote": b})
            continue
        if m := re.match(r"A/C desiccant bag replacement every " + N + r" years?", b, re.I):
            e = {"job": "ac_desiccant", "action": "REPLACE", "condition": "NORMAL", "app": {}, "months": months(m.group(1))}
        elif m := re.match(r"Cabin air filter replacement every " + N + r" years?", b, re.I):
            out.append({"job": "cabin_air_filter", "action": "REPLACE", "condition": "NORMAL", "app": {}, "months": months(m.group(1)),
                        "dist": None, "note": None, "quote": b})
            if h := re.search(r"or " + N + r" years? for (HEPA filter)(, if equipped)?", b, re.I):
                out.append({"job": "cabin_air_filter", "action": "REPLACE", "condition": "NORMAL",
                            "app": {"filter": h.group(2) + (" (if equipped)" if h.group(3) else "")}, "months": months(h.group(1)),
                            "dist": None, "note": None, "quote": b})
            continue
        elif m := re.match(r"(HEPA filters?(?: and carbon filters)?) replacement every " + N + r" years?", b, re.I):
            e = {"job": "cabin_air_filter", "action": "REPLACE", "condition": "NORMAL", "app": {"filter": m.group(1)},
                 "months": months(m.group(2))}
        elif m := re.match(r"Clean and lubricate brake calipers every (year|" + N[1:-1] + r" years?) or ", b, re.I):
            d = DIST.search(b)
            mo = 12 if m.group(1).lower() == "year" else months(m.group(1).split()[0])
            cond = re.search(r"if in an area where roads are salted during winter", b, re.I)
            e = {"job": "brakes", "action": "CLEAN", "condition": "SEVERE" if cond else "NORMAL",
                 "app": {"operating_condition": "roads salted during winter"} if cond else {}, "months": mo,
                 "dist": (number(d.group("mi")), number(d.group("km"))) if d else None}
        elif re.match(r"Rotate tires every ", b, re.I):
            d = DIST.search(b)
            if d:
                note = "or if tread depth difference is 2/32 in (1.5 mm) or greater (as printed)" if "tread depth" in b else None
                if d.group("mi2"):
                    note = (f"printed as a range: every {d.group('mi')}-{d.group('mi2')} miles ({d.group('km')}-{d.group('km2')} km);"
                            f" the lower bound is written") + ("; " + note if note else "")
                e = {"job": "tire_rotation", "action": "ROTATE", "condition": "NORMAL", "app": {}, "months": None,
                     "dist": (number(d.group("mi")), number(d.group("km"))), "note": note}
        if e is None:
            unparsed.append(b)
            continue
        e.setdefault("dist", None)
        e.setdefault("note", None)
        e["quote"] = b
        out.append(e)
    return out, unparsed


def build(strict: bool) -> int:
    lines = our_lines(MAKE)
    per_line = defaultdict(lambda: {"sources": {}, "items": [], "gaps": []})
    for doc in documents(strict):
        ln = doc["line"]
        if ln not in lines:
            continue
        line = lines[ln]
        years = [y for y in doc["years"] if line.years[0] <= y <= line.years[1]]
        scope = f"{MAKE}/{ln} MY{'-'.join(map(str, years))} ({doc['key']})"
        pages = page_text(doc["sha256"])
        flat = [norm(p) for p in pages]
        ok, evidence = us_edition(flat)
        if strict and doc["market"] != "US":
            per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:schedule",
                                         "reason": f"edition market {doc['market']} (strict mode); {evidence}"})
            continue
        if not ok:
            per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:schedule",
                                         "reason": f"not a North American (US) edition: {evidence}; not used"})
            continue
        index = next((i for i, t in enumerate(pages) if re.search(r"^Service Intervals\s*$", t, re.M)
                      and re.search(r"as\W?needed basis", norm(t))), None)
        if index is None:
            per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:schedule", "reason": "Service Intervals list not found"})
            continue
        found, unparsed = entries_of(bullets_of(pages[index]))
        for b in unparsed:
            per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:" + b[:50], "reason": f"p.{index + 1}: bullet not converted"})
        coolant = re.search(r"Your Battery coolant does not need to be replaced for the life of your vehicle under most circumstances\.",
                            " ".join(flat[index:index + 2]))
        if coolant:
            per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:battery_coolant",
                                         "reason": "no replacement interval: 'does not need to be replaced for the life of your vehicle under most circumstances'"})
        used = {index + 1}
        per_line[ln]["sources"][doc["key"]] = pdf_source(
            doc["key"], doc["path"], doc["sha256"], doc["url"], doc["title"], "factory owner's manual, copy hosted by carmans.net",
            REGISTRY, years, used, doc["retrieved_at"], source_type="OWNER_MANUAL_COPY", tier="B", authenticity="REVIEWED_MIRROR")
        gens = generations_of(MAKE, ln)
        for year in years:
            gen = gen_for(gens, year)
            if gen is None:
                per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:schedule", "reason": f"no generation for MY{year}"})
                continue
            for e in found:
                d = e["dist"]
                interval = {"interval_km": d[1] if d else None, "interval_miles_original": d[0] if d else None,
                            "interval_months": e["months"], "rule": None}
                per_line[ln]["items"].append(item(
                    ln, gen, year, e["job"], e["action"], condition=e["condition"], occurrence="EVERY", system="FIXED_INTERVAL",
                    interval=interval, applicability=e["app"], note=e["note"], source=doc["key"], quote=e["quote"], page=index + 1,
                    locator="Maintenance: Service Intervals", display_level="SECONDARY_NOTE", confidence="MEDIUM"))
    markets = json.loads(MARKETS.read_text(encoding="utf-8"))
    for key, info in sorted(markets.items()):
        if key.startswith("tesla/"):
            model = key.split("/")[1]
            if model in lines and info.get("market") != "US":
                per_line[model]["gaps"].append({"scope": f"{MAKE}/{model} ({key}, mycarusermanual.com)", "field": "maintenance:schedule",
                                                "reason": f"mycarusermanual edition market {info.get('market')}, not US; not used"})
    for ln in sorted(lines):
        data = per_line[ln]
        items = merge_years(data["items"])
        if not data["items"]:
            data["gaps"].append({"scope": f"{MAKE}/{ln}", "field": "maintenance:schedule",
                                 "reason": "no US-edition owner's manual with a Service Intervals list on disk for this line"})
        gaps, seen = [], set()
        for g in data["gaps"]:
            k = json.dumps(g, sort_keys=True)
            if k not in seen:
                seen.add(k)
                gaps.append(g)
        out = write(MAKE, ln, NAME, data["sources"], items, gaps)
        yrs = sorted({y for i in items for y in range(i["years"][0], i["years"][1] + 1)})
        print(f"{MAKE}/{ln}: items {len(items)}, years {yrs[0] if yrs else '-'}-{yrs[-1] if yrs else '-'}, "
              f"systems {sorted({i['schedule_system'] for i in items})}, sources {len(data['sources'])}, gaps {len(gaps)} "
              f"-> {out.relative_to(WORK.parent)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(build("--strict-market" in sys.argv))

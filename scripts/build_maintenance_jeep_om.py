"""Jeep maintenance schedules MY2014-2016 from the official US owner's manuals
(vehicleinfo.mopar.com, chapter "Maintenance Schedules"). MY2017+ is read from the Mopar
schedule JSON by build_maintenance.py (maintenance.json); this builder writes the years before.

The manuals print a mileage grid ("Maintenance Chart"):
  * Grand Cherokee / Cherokee / Compass: header "Mileage or time passed (whichever comes first)"
    with one column per point 20,000 ... 150,000 miles, an "Or Years: 2 3 ... 15" row and an
    "Or Kilometers: 32,000 ..." row; an "X" per due service;
  * Grand Cherokee SRT: "SRT - MAINTENANCE CHART", "Miles: 6,000 ... 150,000", "Or Months: 6 ...
    150", "Or Kilometers: 10,000 ... 250,000".
The page text loses the columns, so the X positions are read from the PDF content stream
(pdf_geometry.page_runs) and matched to the nearest column heading; the rows are the bands
between the table's horizontal rules (page_hrules). Per row, the miles, kilometres and years /
months of the marked columns, all as printed in the headings, must each form the same pattern:
  marks at d, 2d, 3d ...        -> EVERY d
  first f, then a constant step -> FIRST f + SUBSEQUENT step
  a single mark                 -> FIRST (listed once within the chart's horizon)
  anything else                 -> gap
A row whose text states its interval ("Flush and replace the engine coolant at 10 years or
150,000 miles (240,000 km) whichever comes first") takes the stated interval; rows marked "**"
("The spark plug change interval is mileage based only, yearly intervals do not apply") get no
time limit. Rows that name severe use ("police, taxi, fleet ...", "off-road") are SEVERE, as in
build_maintenance.py, whose job / action rules are used so that the jobs match MY2017+.

Oil: "At Every Oil Change Interval As Indicated By Oil Change Indicator System: Change oil and
filter" -> OIL_LIFE_MONITOR with the printed maximum ("Under no circumstances should oil change
intervals exceed 10,000 miles (16,000 km) or twelve months"); "Severe Duty All Models: Change
Engine Oil at 4000 miles (6,500 km) if ... dusty and off road" -> SEVERE every 4,000 mi. The SRT
chart lists the oil change in the grid itself. Tire rotation at every indicated oil change has no
fixed interval (gap).

Editions: when two owner's manuals of one line and model year exist in the manifest (Grand
Cherokee and Grand Cherokee SRT, 2014-2016), the items carry {"edition": ...} (same names as
build_maintenance.py). A manual of the manifest that is not on disk is a gap.

Output: data_work/jeep/staging/<line>/maintenance_owner_manual.json (maintenance_common.write).

  .venv/Scripts/python.exe scripts/build_maintenance_jeep_om.py
"""

from __future__ import annotations

import csv
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_maintenance import action_of, component_of, engines_of, from_points, job_of, stated_interval  # noqa: E402
from maintenance_common import gen_for, generations_of, item, merge_years, norm, our_lines, page_text, pdf_source, write  # noqa: E402
from pdf_geometry import page_hrules, page_runs  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

MAKE = "jeep"
NAME = "owner_manual"
REGISTRY = "factory-jeep-us"
YEARS = (2014, 2016)
MANIFEST = WORK / "_shared" / "manifest_official" / "vehicleinfo.mopar.com.csv"
SEVERE = re.compile(r"severe|police|taxi|fleet|towing|off-?road", re.I)  # build_maintenance.py
NUMBER = re.compile(r"^\d{1,3}(?:,\d{3})+$")
MARK = "X"


def edition_name(title: str) -> str:
    """'2016 Jeep Grand Cherokee SRT - SRT Owner Manual' -> 'Grand Cherokee SRT'."""
    model = re.sub(r"^\d{4}\s+Jeep\s+", "", title)
    model = re.sub(r"\s+-\s+.*$", "", model).replace(" SRT", "").strip()
    return f"{model} SRT" if re.search(r"\bSRT\b", title) else model


def documents() -> tuple[list[dict], dict, list[dict]]:
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["make"] == MAKE and r["doc_type"] == "owners_manual"]
    docs, editions, missing, seen = [], defaultdict(set), [], set()
    for r in rows:
        lines = [x for x in r["lines"].split(";") if x]
        years = [int(y) for y in r["years"].split(";") if y]
        years = [y for y in years if YEARS[0] <= y <= YEARS[1]]
        if not years:
            continue
        for ln in lines:
            for y in years:
                editions[(ln, y)].add(edition_name(r["title"]))
        if r["status"] != "ok":
            missing.append({"lines": lines, "years": years, "title": r["title"], "status": r["status"]})
            continue
        if r["sha256"] in seen:  # the same file listed twice (2016 SRT)
            continue
        seen.add(r["sha256"])
        key = f"jeep-{'-'.join(lines)}-{'-'.join(map(str, years))}-{'srt-' if 'SRT' in r['title'] else ''}owner-manual"
        docs.append({"key": key, "lines": lines, "years": years, "title": r["title"], "path": RAW_ROOT / r["path"],
                     "url": r["url"], "sha256": r["sha256"], "retrieved_at": r["retrieved_at"],
                     "edition": edition_name(r["title"])})
    return docs, editions, missing


# ---------------------------------------------------------------- page text spans
def compact_index(text: str) -> tuple[str, list[int]]:
    chars, pos = [], []
    for i, ch in enumerate(text):
        if ch.isalnum():
            chars.append(ch.lower())
            pos.append(i)
    return "".join(chars), pos


def find_span(flat: str, label: str, start: int = 0) -> tuple[int, int] | None:
    """Span of the page text (normalised) whose letters and digits are those of the label read
    from the glyphs (hyphenation, dashes and spacing may differ)."""
    key = "".join(ch.lower() for ch in label if ch.isalnum())
    if not key:
        return None
    comp, pos = compact_index(flat)
    at = comp.find(key, sum(1 for p in pos if p < start))
    if at < 0:
        return None
    end = pos[at + len(key) - 1] + 1
    while end < len(flat) and flat[end] in ").,;:!?]":  # closing punctuation of the row text: "(CVT only)"
        end += 1
    return pos[at], end


# ---------------------------------------------------------------- grid geometry
def tokens(runs: list[dict]) -> list[tuple[str, float]]:
    """Number tokens (text, centre x) of the glyphs of non-rotated runs. Digits set apart by
    kerning instead of spaces ("23456789101112131415", 2014 Compass) are split where the gap
    between two glyph centres exceeds 0.8 x the font size."""
    out = []
    for r in runs:
        cur, xs = "", []
        for ch, cx, _ in r["glyphs"] + [(" ", 0, 0)]:
            if (ch.isdigit() or (ch == "," and cur)) and not (xs and cx - xs[-1] > 0.8 * r["size"]):
                cur += ch
                xs.append(cx)
            elif ch.isdigit():
                if cur.strip(","):
                    out.append((cur.strip(","), sum(xs) / len(xs)))
                cur, xs = ch, [cx]
            else:
                if cur and cur.strip(","):
                    out.append((cur.strip(","), sum(xs) / len(xs)))
                cur, xs = "", []
    return out


def grid(reader: PdfReader, index: int) -> dict:
    runs = page_runs(reader, index, cid_unicode=True)
    time_run = next((r for r in runs if not r["rotated"] and re.match(r"Or (Years|Months):", r["text"].strip())), None)
    km_label = next((r for r in runs if not r["rotated"] and r["text"].strip().startswith("Or Kilometers")), None)
    if not time_run or not km_label:
        return {"error": "column headings (Or Years / Or Months, Or Kilometers) not found"}
    unit = "years" if "Years" in time_run["text"] else "months"
    numeric = [r for r in runs if r["rotated"] and NUMBER.match(r["text"].strip())]
    miles_runs = sorted((r for r in numeric if r["cy"] > time_run["cy"]), key=lambda r: r["cx"])
    km_runs = [r for r in numeric if r["cy"] < km_label["cy"] + 1]
    time_tokens = [t for t in tokens([r for r in runs if not r["rotated"] and abs(r["y"] - time_run["y"]) < 1])]
    if len(miles_runs) < 5:
        return {"error": "mileage column headings not found"}
    pitch = statistics.median(b["cx"] - a["cx"] for a, b in zip(miles_runs, miles_runs[1:]))
    columns = []
    for m in miles_runs:
        k = min(km_runs, key=lambda r: abs(r["cx"] - m["cx"]), default=None)
        t = min(time_tokens, key=lambda x: abs(x[1] - m["cx"]), default=None)
        if not k or not t or abs(k["cx"] - m["cx"]) > 0.4 * pitch or abs(t[1] - m["cx"]) > 0.5 * pitch:
            return {"error": f"column {m['text']} without a km / {unit} heading"}
        n = int(t[0].replace(",", ""))
        columns.append({"miles": int(m["text"].replace(",", "")), "km": int(k["text"].strip().replace(",", "")),
                        "months": n * 12 if unit == "years" else n, "time": t[0], "cx": m["cx"]})
    if [c["miles"] for c in columns] != sorted({c["miles"] for c in columns}):
        return {"error": "mileage headings not increasing"}
    head_bottom = min(r["y"] for r in km_runs) - 1
    left = columns[0]["cx"] - 0.6 * (columns[1]["cx"] - columns[0]["cx"])
    right = columns[-1]["cx"] + 0.6 * (columns[-1]["cx"] - columns[-2]["cx"])  # beyond: the chapter tab ("8")
    rules = sorted({round(y, 1) for x0, x1, y in page_hrules(reader, index) if x1 - x0 > 200 and y < head_bottom}, reverse=True)
    if len(rules) < 2:
        return {"error": "row rules of the chart not found"}
    bands = [(lo, hi) for hi, lo in zip(rules, rules[1:])]
    rows = [{"band": b, "lines": [], "marks": [], "problems": []} for b in bands]

    def band_of(y: float):
        return next((row for row in rows if row["band"][0] < y < row["band"][1]), None)

    for r in runs:
        if r["rotated"] or r["y"] >= head_bottom:
            continue
        label = "".join(ch for ch, cx, _ in r["glyphs"] if cx < left)
        for ch, cx, cy in r["glyphs"]:
            if cx > right:
                continue
            if cx >= left and ch == MARK:
                row = band_of(cy)
                if row is None:
                    continue
                col = min(range(len(columns)), key=lambda i: abs(columns[i]["cx"] - cx))
                near = columns[max(col - 1, 0):col + 2]
                local = statistics.median(b["cx"] - a["cx"] for a, b in zip(near, near[1:])) if len(near) > 1 else pitch
                if abs(columns[col]["cx"] - cx) > 0.35 * local:
                    row["problems"].append(f"mark at x={cx:.1f} between columns")
                else:
                    row["marks"].append(col)
            elif cx >= left and ch.strip():
                row = band_of(cy)
                if row is not None:
                    row["problems"].append(f"text '{ch}' in the mark area")
        if label.strip():
            row = band_of(r["cy"])
            if row is not None:
                row["lines"].append((r["y"], r["x"], label))
    for row in rows:
        row["lines"].sort(key=lambda t: (-round(t[0], 0), t[1]))
        row["label"] = " ".join(t[2].strip() for t in row["lines"])
        row["label"] = row["label"].encode("latin-1", errors="ignore").decode("cp1252", errors="ignore")
    end = next((n for n, row in enumerate(rows) if re.match(r"\s*(?:\*\*|WARNING|CAUTION)", row["label"])), len(rows))
    rows = rows[:end]  # the chart ends at its "**" footnote / the WARNING box below it
    return {"columns": columns, "rows": rows, "unit": unit, "time_text": time_run["text"].strip()}


# ---------------------------------------------------------------- items of one manual
def applicability(text: str) -> dict:
    """Engine / transmission / equipment qualifiers as printed in the row."""
    app = {}
    engine = engines_of(re.sub(r"\d{1,3},\d{3}|\(\d[\d,]* km\)", "", text))
    if engine:
        app["engine"] = engine
    m = re.search(r"\((CVT|six-?\s?speed) only\)", text, re.I)  # "(six-speed only)" (page text: "sixspeed")
    if m:
        app["transmission"] = "CVT" if m.group(1).upper() == "CVT" else "six-speed"
    if re.search(r"vehicles equipped with four wheel disc brakes", text, re.I):
        app["equipment"] = "four wheel disc brakes"
    return {**app, **component_of(text)}


def miles_list(cols: list[dict], marked: list[int]) -> str:
    return ", ".join(f"{cols[c]['miles']:,}" for c in marked)


def occurrences(shape: list[dict] | None) -> list[str] | None:
    return [s["occurrence"] for s in shape] if shape else None


def chart_items(doc: dict, pages: list[str], flat: list[str], grid_pages: list[int], entries: list, gaps: list):
    reader = PdfReader(str(doc["path"]))
    for index in grid_pages:
        page = index + 1
        g = grid(reader, index)
        if "error" in g:
            gaps.append({"field": "maintenance:schedule", "reason": f"p.{page}: {g['error']}"})
            continue
        cols = g["columns"]
        mileage_only_note = re.search(r"\*\* The spark plug change interval is mileage based only, yearly intervals do not apply\.",
                                      " ".join(flat[index:index + 2]))
        time_quote = next((q for q in (g["time_text"],) if norm(q) in flat[index]), None)
        whichever = "whichever comes first" in flat[index].lower()
        cursor = 0
        for row in g["rows"]:
            label = row["label"].strip()
            if not label:
                continue
            span = find_span(flat[index], label, cursor)
            if span is None:
                if row["marks"]:
                    gaps.append({"field": "maintenance:" + label[:50], "reason": f"p.{page}: row text not found in the page text"})
                continue
            cursor = span[1]
            text = flat[index][span[0]:span[1]]
            marks_text = re.match(r"\s*((?:X\s?)+)", flat[index][span[1]:])
            quote = text + (" " + marks_text.group(1).strip() if marks_text and marks_text.group(1).count("X") == len(row["marks"]) else "")
            job = job_of(text)
            if job is None:
                if row["marks"]:
                    gaps.append({"field": "maintenance:" + text[:60], "reason": f"p.{page}: chart row not mapped to a maintenance job"})
                continue
            if row["problems"]:
                gaps.append({"field": f"maintenance:{job}", "reason": f"p.{page} '{text[:60]}': {'; '.join(row['problems'])}; not converted"})
                continue
            condition = "SEVERE" if SEVERE.search(text) else "NORMAL"
            action = action_of(text)
            app = applicability(text)
            locator = f"Maintenance Chart p.{page}, row '{text[:80]}'"
            marked = sorted(set(row["marks"]))
            stated = stated_interval(text) if re.search(r"\d+\s*(?:years|months)|[\d,]{4,}\s*miles", text, re.I) else None
            if stated and (stated.get("interval_km") or stated.get("interval_months")):
                occurrence = "FIRST" if re.search(r"\bat\b|first", text, re.I) and not re.search(r"\bevery\b", text, re.I) else "EVERY"
                entries.append({"job": job, "action": action, "condition": condition, "occurrence": occurrence,
                                "interval": {k: stated.get(k) for k in ("interval_km", "interval_miles_original", "interval_months", "rule")},
                                "applicability": app,
                                "note": f"interval as stated in the row; the chart marks it at {miles_list(cols, marked) or 'no column'} miles",
                                "cites": [(quote, page, locator)]})
                continue
            if not marked:
                gaps.append({"field": f"maintenance:{job}", "reason": f"p.{page} '{text[:60]}': no mark and no stated interval"})
                continue
            miles = from_points([cols[c]["miles"] for c in marked])
            kms = from_points([cols[c]["km"] for c in marked])
            months = from_points([cols[c]["months"] for c in marked])
            if not miles or occurrences(miles) != occurrences(kms) or occurrences(miles) != occurrences(months):
                gaps.append({"field": f"maintenance:{job}",
                             "reason": f"p.{page} '{text[:60]}': marks at {[cols[c]['miles'] for c in marked]} miles do not form a regular interval; not converted"})
                continue
            mileage_only = "**" in row["label"]  # "Replace spark plugs ** " (the span ends at the last letter)
            for n, s in enumerate(miles):
                mo = None if mileage_only else months[n]["miles"]
                interval = {"interval_km": kms[n]["miles"], "interval_miles_original": s["miles"], "interval_months": mo,
                            "rule": "WHICHEVER_FIRST" if mo and whichever else None}
                parts = [f"chart marks at {miles_list(cols, marked)} miles"]
                if len(marked) == 1:
                    parts.append("listed once within the chart's horizon")
                if mileage_only:
                    parts.append("mileage based only (** footnote)")
                cites = [(quote, page, locator)]
                if mo and time_quote:
                    cites.append((time_quote, page, f"Maintenance Chart p.{page}, column headings ({g['unit']})"))
                if mileage_only and mileage_only_note:
                    note_page = index + 1 if mileage_only_note.group(0) in flat[index] else index + 2
                    cites.append((mileage_only_note.group(0), note_page, "Maintenance Chart footnote **"))
                entries.append({"job": job, "action": action, "condition": condition, "occurrence": s["occurrence"],
                                "interval": interval, "applicability": app, "note": "; ".join(parts), "cites": cites})


OIL_INDICATOR = re.compile(r"At Every Oil Change Interval As Indicated By Oil Change Indicator System: • Change oil and filter\.?")
OIL_MAX = re.compile(r"Under no circumstances should oil change intervals exceed (?P<mi>[\d,]+) miles \((?P<km>[\d,]+) km\)"
                     r"(?:,| or) (?P<n>twelve|six) months(?P<rest>[^.]*)\.")
SEVERE_OIL = re.compile(r"Change Engine Oil at (?P<mi>[\d,]+) miles \((?P<km>[\d,]+) km\) if the vehicle is operated in a dusty and off road environment")
TIRES = re.compile(r"At Every Oil Change Interval As Indicated By Oil Change Indicator System: (?:• [^•]*?)?• Rotate the tires")


def oil_items(flat: list[str], first: int, entries: list, gaps: list):
    found = None
    for index in range(max(first - 4, 0), first + 1):
        m = OIL_INDICATOR.search(flat[index])
        if m:
            found = (m.group(0), index + 1)
    cap = None
    for index in range(max(first - 4, 0), first + 1):
        text = flat[index].replace("inter- vals", "intervals").replace("which- ever", "whichever")
        m = OIL_MAX.search(text)
        if m and m.group(0) in flat[index]:
            cap = (m, index + 1)
        sev = SEVERE_OIL.search(flat[index])
        if sev:
            mi, km = int(sev.group("mi").replace(",", "")), int(sev.group("km").replace(",", ""))
            entries.append({"job": "engine_oil_and_filter", "action": "REPLACE", "condition": "SEVERE", "occurrence": "EVERY",
                            "interval": {"interval_km": km, "interval_miles_original": mi, "interval_months": None, "rule": None},
                            "applicability": {"operation": "dusty and off road environment"},
                            "note": "Severe Duty All Models: change engine oil at this mileage (as printed)",
                            "cites": [(sev.group(0), index + 1, "Maintenance Schedule: Severe Duty All Models")]})
    if TIRES.search(" ".join(flat[max(first - 4, 0):first + 1])):
        gaps.append({"field": "maintenance:tire_rotation",
                     "reason": "rotate the tires at every oil change indicated by the oil change indicator system; no fixed interval printed"})
    if not found:
        return
    if cap is None:
        gaps.append({"field": "maintenance:engine_oil_and_filter", "reason": "oil change indicator item without a printed maximum"})
        return
    m, page = cap
    months = {"twelve": 12, "six": 6}[m.group("n")]
    note = "oil change indicator system: change oil and filter when the indicator shows; maximum as printed"
    if m.group("rest").strip():
        note += f" ({m.group('rest').strip()})"
    entries.append({"job": "engine_oil_and_filter", "action": "REPLACE", "condition": "NORMAL", "occurrence": "EVERY",
                    "system": "OIL_LIFE_MONITOR", "interval": None,
                    "max_interval": {"interval_km": int(m.group("km").replace(",", "")), "interval_months": months},
                    "applicability": {}, "note": note,
                    "cites": [(found[0], found[1], "Maintenance Chart: At Every Oil Change Interval"),
                              (m.group(0), page, "Maintenance Schedule: NOTE")]})


def build() -> int:
    lines = our_lines(MAKE)
    docs, editions, missing = documents()
    per_line = defaultdict(lambda: {"sources": {}, "items": [], "gaps": []})
    for miss in missing:
        for ln in miss["lines"]:
            if ln in lines:
                per_line[ln]["gaps"].append({"scope": f"{MAKE}/{ln} MY{'-'.join(map(str, miss['years']))}", "field": "maintenance:schedule",
                                             "reason": f"'{miss['title']}' listed in the manifest but not on disk (status {miss['status']})"})
    for doc in docs:
        targets = [ln for ln in doc["lines"] if ln in lines]
        try:
            pages = page_text(doc["sha256"])
        except FileNotFoundError:
            for ln in targets:
                per_line[ln]["gaps"].append({"scope": f"{MAKE}/{ln} MY{doc['years']} ({doc['key']})", "field": "maintenance:schedule",
                                             "reason": "page text of the PDF not in the pagetext store"})
            continue
        flat = [norm(p) for p in pages]
        grid_pages = [i for i, t in enumerate(flat) if "Or Kilometers:" in t and re.search(r"Or (?:Years|Months):", t)]
        entries, gaps = [], []
        if not grid_pages:
            gaps.append({"field": "maintenance:schedule", "reason": "no Maintenance Chart found"})
        else:
            chart_items(doc, pages, flat, grid_pages, entries, gaps)
            oil_items(flat, grid_pages[0], entries, gaps)
        used_pages = {c[1] for e in entries for c in e["cites"]}
        for ln in targets:
            gens = generations_of(MAKE, ln)
            scope = f"{MAKE}/{ln} MY{'-'.join(map(str, doc['years']))} ({doc['key']})"
            for g in gaps:
                per_line[ln]["gaps"].append({"scope": scope, **g})
            if not entries:
                continue
            per_line[ln]["sources"][doc["key"]] = pdf_source(
                doc["key"], doc["path"], doc["sha256"], doc["url"], doc["title"], "FCA US LLC (owner's manual, vehicleinfo.mopar.com)",
                REGISTRY, doc["years"], used_pages, doc["retrieved_at"])
            for year in doc["years"]:
                gen = gen_for(gens, year)
                if gen is None:
                    per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:schedule", "reason": f"no generation for MY{year}"})
                    continue
                shared = len(editions[(ln, year)]) > 1
                for e in entries:
                    app = dict(e["applicability"])
                    if shared:
                        app["edition"] = doc["edition"]
                    quote, page, locator = e["cites"][0]
                    it = item(ln, gen, year, e["job"], e["action"], condition=e["condition"], occurrence=e["occurrence"],
                              system=e.get("system", "FIXED_INTERVAL"), interval=e["interval"], applicability=app,
                              note=e["note"], max_interval=e.get("max_interval"), source=doc["key"], quote=quote, page=page,
                              locator=locator)
                    for q, p, loc in e["cites"][1:]:
                        it["cites"].append({"source": doc["key"], "quote": norm(q), "pages": [p], "locator": loc})
                    per_line[ln]["items"].append(it)
    for ln in sorted(lines):
        data = per_line[ln]
        items = merge_years(data["items"])
        gaps, seen = [], set()
        for g in data["gaps"]:
            k = json.dumps(g, sort_keys=True)
            if k not in seen:
                seen.add(k)
                gaps.append(g)
        out = write(MAKE, ln, NAME, data["sources"], items, gaps)
        years = sorted({y for i in items for y in range(i["years"][0], i["years"][1] + 1)})
        print(f"{MAKE}/{ln}: items {len(items)}, years {years[0] if years else '-'}-{years[-1] if years else '-'}, "
              f"sources {len(data['sources'])}, gaps {len(gaps)} -> {out.relative_to(WORK.parent)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(build())

"""Chevrolet maintenance schedules from the official GM US owner's manuals
(contentdelivery.ext.gm.com, chapter "Service and Maintenance" > "Maintenance Schedule").

Two layouts are printed:
  A. 2014-2022: "Maintenance Schedule Additional Required Services - Normal" and "- Severe":
     a grid with one column per mileage point (12 000 km/7,500 mi ... 240 000 km/150,000 mi)
     and a mark glyph per due service; footnotes on the following page give the time limit
     ("(2) Or every two years, whichever comes first.") or the whole interval of a row without
     marks ("(5) Replace brake fluid every five years."). The page text loses the columns, so
     the mark positions are read from the PDF content stream (pdf_geometry.py) and each mark
     is matched to the nearest column heading.
       marks at d, 2d, 3d ...        -> EVERY d (km and miles as printed in the column heading)
       first f, then a constant step -> FIRST f + SUBSEQUENT step
       a single mark                 -> FIRST (the chart lists it once within its 150,000 mi
                                        horizon; same reading as build_maintenance.py)
       irregular marks               -> not converted (gap)
  B. 2023+: text blocks "Additional Required Services — Normal Service / Severe Service",
     "Every 36 000 km (22,500 mi)" headings with bullet items, and "Owner Checks and Services /
     Every Five Years".
Both layouts print the Oil Life System paragraph ("When the CHANGE ENGINE OIL SOON message
displays ... The engine oil and filter must be changed at least once a year"): one
OIL_LIFE_MONITOR item with the stated maximum (12 months) and no invented distance. Engine air
filters governed by the Engine Air Filter Life System and rows without a printed interval are
gaps. Severe items are the rows of the severe chart (layout A) or the severe section (layout B)
only, as printed.

Documents: every official owner's manual of our Chevrolet lines (manifest_official
contentdelivery.ext.gm.com.csv, doc_type owners_manual). The warranty booklets of the same
manifest print no schedule and are not used. A model year without an official manual (Trax
2023) is read from the carmans.net copy of the factory manual (tier B, SECONDARY_NOTE) when its
extracted edition is US. "Limited" manuals (2016 Cruze Limited, 2016 Malibu Limited) carry
{"edition": "<title name>"} in the applicability.

Output: data_work/chevrolet/staging/<line>/maintenance_owner_manual.json (maintenance_common).

  .venv/Scripts/python.exe scripts/build_maintenance_gm.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maintenance_common import (  # noqa: E402
    JOBS, action_of, gen_for, generations_of, item, merge_years, norm, our_lines, page_text, pdf_source, write,
)
from pdf_geometry import page_runs  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

MAKE = "chevrolet"
REGISTRY = "factory-chevrolet-us"
NAME = "owner_manual"
GM_MANIFEST = WORK / "_shared" / "manifest_official" / "contentdelivery.ext.gm.com.csv"
CARMANS_MANIFEST = WORK / "_shared" / "manifest_carmans.csv"
MARK = "@"
# running page header of the GM manuals (title, print code, date, page number, "Black plate")
PAGE_HEAD = re.compile(r"Owner Manual \(GMNA|^\d+ Service and Maintenance$|^Service and Maintenance \d+$|Black plate"
                       r"|\b(?:CRC|crc)\b|^\d{5,}\)|^\d+-\d+ Service and Maintenance$|^Service and Maintenance \d+-\d+$")

GM_JOBS = [  # tried before maintenance_common.JOBS
    ("tire_rotation", r"^\W*Rotate tires"),
    ("engine_coolant", r"engine cooling system"),
    ("cabin_air_filter", r"passenger compartment air filter"),
    ("evap_system", r"evaporative control system|evaporative \(EVAP\)"),
    ("gas_struts", r"gas struts?"),
    ("manual_transmission_fluid", r"manual transmission fluid"),
    ("brake_fluid", r"brake/clutch fluid"),
    ("clutch_fluid", r"clutch fluid"),
    ("differential_fluid", r"rear axle fluid"),
    ("timing_belt", r"timing belt"),
]
NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
           "ten": 10, "twelve": 12, "fifteen": 15}
TIME = re.compile(r"\b(?:every\s+)?(?P<n>\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|twelve|fifteen)\s+(?P<u>years?|months?)\b", re.I)
HEADER = re.compile(r"^(?P<km>\d{1,3}(?:\d{3})+)km/(?P<mi>\d{1,3}(?:,\d{3})*)mi$")
GRID_TITLE = re.compile(r"Maintenance\s+Schedule\s+Additional\s+Required\s+Services\s*-\s*(Normal|Severe)", re.I)
FOOT_TITLE = re.compile(r"Footnotes\s*[—–-]+\s*Maintenance\s+Schedule\s+Additional\s+Required\s+Services\s*-\s*(Normal|Severe)", re.I)
FOOT_STOP = re.compile(r"Special Application Services|Additional Maintenance and Care|Footnotes\s*[—–-]|Maintenance Schedule Additional Required")
AIR_LIFE = re.compile(r"air filter life (?:percentage|system)|REPLACE ENGINE AIR FILTER SOON|vehicle messages indicate", re.I)


def gm_job(text: str) -> str | None:
    for job, pattern in GM_JOBS + JOBS:
        if re.search(pattern, text, re.I):
            return job
    return None


def months_in(text: str) -> int | None:
    m = TIME.search(text)
    if not m:
        return None
    n = m.group("n").lower()
    n = int(n) if n.isdigit() else NUMBERS[n]
    return n * 12 if m.group("u").lower().startswith("year") else n


def engines(text: str) -> str:
    return "/".join(x.strip() for x in re.split(r"\s+and\s+", text))


def gm_applicability(label: str) -> dict:
    """Engine / drive / transmission qualifiers exactly as the row or bullet prints them."""
    app = {}
    eng = r"(\d\.\dL(?:\s+and\s+\d\.\dL)?(?:\s+(?:Turbo|Diesel|Hybrid))?)"
    m = re.search(r"\bExcept\s+(?:with\s+)?" + eng, label, re.I)
    if m:
        app["engine_except"] = engines(m.group(1))
    elif re.search(r"\bExcept with eAssist", label, re.I):
        app["powertrain_except"] = "eAssist"
    else:
        m = (re.search(eng + r"(?:\s+Engines?)?(?:\s+Vehicles)?\s+Only\b", label, re.I)
             or re.search(r"\(" + eng + r"(?:\s+Engine)?\)", label, re.I))
        if m:
            app["engine"] = engines(m.group(1))
        elif re.search(r"\bDiesel(?: Engine)? Only\b", label, re.I):
            app["engine"] = "Diesel"
    if re.search(r"Vehicles with eAssist", label, re.I):
        app["powertrain"] = "eAssist"
    if re.search(r"if equipped with AWD", label, re.I):
        app["drive"] = "AWD"
    m = re.search(r"If equipped with (?:an? )?(manual|automatic) transmission", label, re.I)
    if m:
        app["transmission"] = m.group(1).lower()
    m = re.search(r"(\d+ Speed Transmission|Continuously Variable Ratio \(CVT\) Transmission)\s*$", label)
    if m:
        app["transmission"] = m.group(1)
    if re.search(r"not equipped with the engine air filter life system", label, re.I):
        app["equipment"] = "without engine air filter life system"
    elif re.search(r"\(If equipped\)", label, re.I):
        app["equipment"] = "if equipped"
    return app


# ---------------------------------------------------------------- documents
def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def documents() -> list[dict]:
    docs, official = [], set()
    for row in read_csv(GM_MANIFEST):
        if row["make"] != MAKE or row["status"] != "ok" or row["doc_type"] != "owners_manual":
            continue
        lines = [x for x in row["lines"].split(";") if x]
        years = [int(y) for y in row["years"].split(";") if y]
        limited = re.search(r"Chevrolet (\w+ Limited) Owner", row["title"])
        key = f"chevrolet-{'-'.join(lines)}-{'-'.join(map(str, years))}{'-limited' if limited else ''}-owner-manual"
        docs.append({"key": key, "lines": lines, "years": years, "title": row["title"], "path": RAW_ROOT / row["path"],
                     "url": row["url"], "sha256": row["sha256"], "retrieved_at": row["retrieved_at"], "tier": "A",
                     "edition": limited.group(1) if limited else None,
                     "publisher": "General Motors (owner's manual, contentdelivery.ext.gm.com)"})
        if not limited:
            official |= {(ln, y) for ln in lines for y in years}
    for row in read_csv(CARMANS_MANIFEST):
        if row["make"] != MAKE or row["kind"] != "pdf" or row["status"] != "ok":
            continue
        line, year = row["line"].split("/")[-1], int(row["year"])
        if (line, year) in official:
            continue
        extracted = WORK / MAKE / "extracted" / f"carmans-{row['post']}.json"
        info = json.loads(extracted.read_text(encoding="utf-8")) if extracted.exists() else {}
        if info.get("status") != "ok" or info.get("edition_market") != "US":
            continue
        docs.append({"key": f"carmans-{row['post']}-maintenance", "lines": [line], "years": [year],
                     "title": f"{year} Chevrolet {line.title()} owner's manual (copy of the factory manual, carmans.net)",
                     "path": RAW_ROOT / row["path"], "url": row["url"], "sha256": row["sha256"],
                     "retrieved_at": row["retrieved_at"], "tier": "B", "edition": None,
                     "publisher": "factory owner's manual, copy hosted by carmans.net"})
    return docs


# ---------------------------------------------------------------- layout A (grid)
def footnotes(pages: list[str], flat: list[str], start: int, condition: str) -> dict:
    """{n: (text, page)} of the footnotes block of the chart (normal / severe)."""
    for j in range(start, min(start + 3, len(pages))):
        m = next((x for x in FOOT_TITLE.finditer(flat[j]) if x.group(1).lower() == condition.lower()), None)
        if m:
            break
    else:
        return {}
    out, page, text = {}, j, flat[j][m.end():]
    while True:
        stop = FOOT_STOP.search(text)
        body = text[:stop.start()] if stop else text
        for f in re.finditer(r"\((\d{1,2})\)\s+(.*?)(?=\s\(\d{1,2}\)\s|$)", body):
            out.setdefault(int(f.group(1)), (f.group(2).strip(), page + 1))
        if stop or page + 1 >= len(pages):
            break
        page += 1
        text = norm(" ".join(body_lines(pages[page])))  # page header (manual title, page number) skipped
        if not re.match(r"\(\d{1,2}\)\s", text):
            break
    return out


def clean_note(text: str) -> str:
    """Footnote remainder without page references ("See Cooling System 0 238.", "on page 10-16")."""
    text = re.sub(r"\s*See [^.]*(?:\.|$)", "", text)
    text = re.sub(r"^[\s,.;]+", "", text)
    return norm(text)


def first_sentence(text: str) -> str:
    m = re.match(r"(.+?\.)(?:\s|$)", text)
    return m.group(1) if m else text


def shape(cols: list[int]) -> list[tuple[str, int]] | None:
    cols = sorted(set(cols))
    if len(cols) == 1:
        return [("FIRST", cols[0])]
    steps = {b - a for a, b in zip(cols, cols[1:])}
    if len(steps) != 1:
        return None
    step = steps.pop()
    if cols[0] == step:
        return [("EVERY", step)]
    return [("FIRST", cols[0]), ("SUBSEQUENT", step)]


def grid_rows(reader: PdfReader, index: int, page_lines: list[str]) -> dict:
    """Column headings and the rows (label, mark columns) of the chart drawn on a page."""
    runs = page_runs(reader, index)
    headers = []
    for r in runs:
        m = HEADER.match(r["text"].replace(" ", ""))
        if m:
            headers.append({"km": int(m.group("km")), "mi": int(m.group("mi").replace(",", "")), "cx": r["cx"], "y": r["y"]})
    headers.sort(key=lambda h: h["cx"])
    if len(headers) < 5:
        return {"error": "column headings not found"}
    pitch = statistics.median(b["cx"] - a["cx"] for a, b in zip(headers, headers[1:]))
    top = min(h["y"] for h in headers) - 1
    foot = [r["y"] for r in runs if r["text"].replace(" ", "").startswith("Footnotes") and r["y"] < top]
    bottom = max(foot) if foot else -1e9
    left = headers[0]["cx"] - 0.6 * pitch
    marks = [(g[1], g[2]) for r in runs for g in r["glyphs"] if g[0] == MARK and bottom < g[2] < top]
    labels = [r for r in runs if not r["rotated"] and MARK not in r["text"] and r["text"].strip()
              and r["x"] < left and bottom < r["y"] < top and not GRID_TITLE.search(r["text"])]
    labels.sort(key=lambda r: -r["y"])
    rows = []
    for r in labels:
        if rows and rows[-1]["lines"][-1]["y"] - r["y"] <= 1.5 * r["size"]:
            rows[-1]["lines"].append(r)
        else:
            rows.append({"lines": [r], "marks": []})
    problems = []
    for cx, cy in marks:
        best, dist = None, None
        for row in rows:
            ys = [ln["cy"] for ln in row["lines"]]
            d = 0 if min(ys) - 1 <= cy <= max(ys) + 1 else min(abs(cy - min(ys)), abs(cy - max(ys)))
            if dist is None or d < dist:
                best, dist = row, d
        col = min(range(len(headers)), key=lambda i: abs(headers[i]["cx"] - cx))
        if best is None or dist > 6 or abs(headers[col]["cx"] - cx) > 0.35 * pitch:
            problems.append(f"mark at x={cx:.1f} y={cy:.1f} not placed")
            continue
        best["marks"].append(col + 1)
    compact = {}
    for ln in page_lines:
        compact.setdefault(re.sub(r"\s+", "", ln), ln)
    for row in rows:
        row["label"] = norm(" ".join(compact.get(re.sub(r"\s+", "", ln["text"]), ln["text"]) for ln in row["lines"]))
    linear = all(h["km"] == (i + 1) * headers[0]["km"] and h["mi"] == (i + 1) * headers[0]["mi"] for i, h in enumerate(headers))
    return {"headers": headers, "rows": rows, "problems": problems, "linear": linear}


def head_text(h: dict) -> str:
    km = f"{h['km']:,}".replace(",", " ")
    return f"{km} km/{h['mi']:,} mi"


HEAD_TEXT = re.compile(r"\b\d{1,3} 000 km/\d{1,3}(?:,\d{3})* mi")


def chart_condition(text: str) -> str | None:
    """NORMAL / SEVERE of the chart title on a page (not a footnotes title, not a reference)."""
    for m in GRID_TITLE.finditer(text):
        before, after = text[max(0, m.start() - 15):m.start()], text[m.end():m.end() + 8]
        if "Footnotes" in before or re.match(r"\s*(?:chart|Service)\b", after):
            continue
        return m.group(1).upper()
    return None


def layout_a(doc: dict, pages: list[str], flat: list[str], grid_pages: list[int], entries: list, gaps: list):
    reader = PdfReader(str(doc["path"]))
    for index in grid_pages:
        cond = chart_condition(flat[index])
        grid = grid_rows(reader, index, pages[index].splitlines())
        page = index + 1
        if "error" in grid:
            gaps.append({"field": "maintenance:schedule", "reason": f"p.{page}: {grid['error']}"})
            continue
        for p in grid["problems"]:
            gaps.append({"field": "maintenance:schedule", "reason": f"p.{page}: {p}"})
        notes = footnotes(pages, flat, index, cond)
        headers = grid["headers"]
        chart = f"Maintenance Schedule Additional Required Services - {cond.title()}"
        for row in grid["rows"]:
            label = row["label"]
            if AIR_LIFE.search(label) and not re.search(r"Rotate tires|not equipped with the engine air filter life system", label):
                gaps.append({"field": "maintenance:engine_air_filter",
                             "reason": f"p.{page} {cond.lower()}: replaced when the Engine Air Filter Life System indicates; no fixed interval printed"})
                continue
            job = gm_job(label)
            if job is None:
                if row["marks"] or re.search(r"\(\d\)", label):
                    gaps.append({"field": "maintenance:" + label[:60], "reason": f"p.{page}: chart row not mapped to a maintenance job"})
                continue
            if job == "tire_rotation" and AIR_LIFE.search(label):
                gaps.append({"field": "maintenance:engine_air_filter",
                             "reason": f"p.{page} {cond.lower()}: replaced when the Engine Air Filter Life System indicates; no fixed interval printed"})
            action = "ROTATE" if job == "tire_rotation" else action_of(label)
            app = gm_applicability(label) if job != "tire_rotation" else {}
            refs = [int(x) for x in re.findall(r"\((\d{1,2})\)", label)]
            # row 1 (tire rotation and Required Services) carries the air-filter footnote: not its interval
            foot = next((notes[r] for r in refs if r in notes), None) if job != "tire_rotation" else None
            months = months_in(foot[0]) if foot and (foot[0].lower().startswith("or ") or "every" in foot[0].lower()) else None
            foot_quote, note_parts = None, []
            if foot:
                sentence = first_sentence(foot[0])
                if months and months_in(sentence) is None:
                    sentence = foot[0][:TIME.search(foot[0]).end()]
                foot_quote = f"({refs[0]}) {sentence}" if f"({refs[0]}) {sentence}" in flat[foot[1] - 1] else sentence
                rest = clean_note(foot[0][len(sentence):] if months else foot[0])
                if rest:
                    note_parts.append(f"footnote: {rest}")
            whichever = bool(foot and re.search(r"whichever", foot[0], re.I))
            mark_text = " ".join([MARK] * len(row["marks"]))
            quote = f"{label} {mark_text}".strip() if norm(f"{label} {mark_text}") in flat[index] else label
            if refs and not foot and job != "tire_rotation":
                gaps.append({"field": f"maintenance:{job}", "reason": f"p.{page}: footnote {refs} of the chart not found"})
            if row["marks"]:
                found = shape(row["marks"])
                if found is None or not grid["linear"]:
                    gaps.append({"field": f"maintenance:{job}",
                                 "reason": f"p.{page} {cond.lower()}: irregular marks at {[head_text(headers[c - 1]) for c in sorted(row['marks'])]}; not converted"})
                    continue
                cols = ", ".join(head_text(headers[c - 1]) for c in sorted(row["marks"]))
                for occurrence, col in found:
                    h = headers[col - 1]
                    interval = {"interval_km": h["km"], "interval_miles_original": h["mi"], "interval_months": months,
                                "rule": "WHICHEVER_FIRST" if months and whichever else None}
                    parts = list(note_parts)
                    if len(row["marks"]) == 1:
                        parts.append(f"the chart marks this service once, at {head_text(h)}, within its {head_text(headers[-1])} horizon")
                    cites = [(quote, page, f"{chart}, row '{label[:90]}', marks at {cols}")]
                    if months and foot:
                        cites.append((foot_quote, foot[1], f"{chart}, footnote ({refs[0]})"))
                    entries.append({"job": job, "action": action, "condition": cond, "occurrence": occurrence,
                                    "interval": interval, "applicability": app, "note": "; ".join(parts) or None,
                                    "cites": cites})
            elif months:
                # "(7) Replace brake fluid every five years for DOT 3 fluid or every three years for DOT 4 fluid."
                per_fluid = re.search(r"every (\w+) years? for (DOT \d) fluid or every (\w+) years? for (DOT \d) fluid", foot[0], re.I)
                variants = [(months, {}, foot_quote)]
                if per_fluid:
                    whole = first_sentence(foot[0])
                    whole = f"({refs[0]}) {whole}" if f"({refs[0]}) {whole}" in flat[foot[1] - 1] else whole
                    variants = [(months_in(f"{per_fluid.group(1)} years"), {"brake_fluid_type": per_fluid.group(2)}, whole),
                                (months_in(f"{per_fluid.group(3)} years"), {"brake_fluid_type": per_fluid.group(4)}, whole)]
                for m_, extra, fq in variants:
                    cites = [(fq, foot[1], f"{chart}, footnote ({refs[0]})"),
                             (label, page, f"{chart}, row '{label[:90]}' (no mileage mark)")]
                    entries.append({"job": job, "action": action, "condition": cond, "occurrence": "EVERY",
                                    "interval": {"interval_km": None, "interval_miles_original": None, "interval_months": m_, "rule": None},
                                    "applicability": {**app, **extra}, "note": "; ".join(note_parts) or None, "cites": cites})
            else:
                gaps.append({"field": f"maintenance:{job}", "reason": f"p.{page} {cond.lower()}: chart row without mileage marks or a printed interval"})


# ---------------------------------------------------------------- layout B (text)
EVENTS = re.compile(
    r"(?P<tire>Tire Rotation and Required Services Every (?P<tkm>\d{1,3}(?: \d{3})+) km \((?P<tmi>\d{1,3}(?:,\d{3})*) mi\))"
    r"|(?P<sec>Additional Required Services\s*[—–-]+\s*(?P<cond>Normal|Severe) Service)"
    r"|(?P<owner>Owner Checks and Services)"
    r"|(?P<desc>Severe Conditions Requiring More Frequent Maintenance)"
    r"|(?P<km>Every (?P<ekm>\d{1,3}(?: \d{3})+) km \((?P<emi>\d{1,3}(?:,\d{3})*) mi\))"
    r"|(?P<years>Every (?P<n>One|Two|Three|Four|Five|Six|Seven|Eight|Ten|\d{1,2}) Years)"
    r"|(?P<stop>Multi-Point Vehicle Inspection \(MPVI\) A Multi|Special Application Services)"
    r"|(?P<bullet>\n• )")


def body_lines(page: str) -> list[str]:
    lines = [ln.strip() for ln in page.splitlines()]
    while lines and (not lines[0] or PAGE_HEAD.search(lines[0])):
        lines.pop(0)
    return lines


def stream(pages: list[str], start: int, count: int) -> tuple[str, list[tuple[int, int]]]:
    """Text of the schedule pages, bullets as "\\n• ", with (offset, page) marks."""
    text, marks = "", []
    for index in range(start, min(start + count, len(pages))):
        marks.append((len(text), index + 1))
        for ln in body_lines(pages[index]):
            if not ln:
                continue
            m = re.match(r"^[•.]\s+(.*)$", ln)
            text += ("\n• " + m.group(1)) if m else (" " + ln)
    return text, marks


def page_at(marks: list[tuple[int, int]], offset: int) -> int:
    return [p for o, p in marks if o <= offset][-1]


def layout_b(doc: dict, pages: list[str], flat: list[str], entries: list, gaps: list):
    start = next((i for i, t in enumerate(flat) if re.search(r"Maintenance Schedule Tire Rotation and Required Services Every", t)), None)
    if start is None:
        gaps.append({"field": "maintenance:schedule", "reason": "no Maintenance Schedule chart or text section found"})
        return
    text, marks = stream(pages, start, 4)
    section, interval, bullets = None, None, []
    events = list(EVENTS.finditer(text))
    for n, ev in enumerate(events):
        end = events[n + 1].start() if n + 1 < len(events) else len(text)
        page = page_at(marks, ev.start())
        if ev.group("stop") and section:
            break
        if ev.group("tire"):
            section = "TIRE"
            entries.append({"job": "tire_rotation", "action": "ROTATE", "condition": "NORMAL", "occurrence": "EVERY",
                            "interval": {"interval_km": int(ev.group("tkm").replace(" ", "")),
                                         "interval_miles_original": int(ev.group("tmi").replace(",", "")),
                                         "interval_months": None, "rule": None},
                            "applicability": {}, "note": None,
                            "cites": [(ev.group("tire"), page, "Maintenance Schedule: Tire Rotation and Required Services")]})
        elif ev.group("sec"):
            section, interval = ev.group("cond").upper(), None
        elif ev.group("owner"):
            section, interval = "OWNER", None
        elif ev.group("desc"):
            section, interval = "DESC", None
        elif ev.group("km"):
            interval = {"km": int(ev.group("ekm").replace(" ", "")), "mi": int(ev.group("emi").replace(",", "")), "months": None,
                        "head": ev.group("km"), "page": page}
        elif ev.group("years"):
            n_ = ev.group("n").lower()
            interval = {"km": None, "mi": None, "months": (int(n_) if n_.isdigit() else NUMBERS[n_]) * 12,
                        "head": ev.group("years"), "page": page}
        elif ev.group("bullet") and section in ("NORMAL", "SEVERE", "OWNER"):
            bullets.append({"section": section, "interval": interval, "text": norm(text[ev.end():end]), "page": page})
    for b in bullets:
        text_b, page, iv = b["text"], b["page"], b["interval"]
        if re.search(r"oil life", text_b, re.I):
            continue  # the Oil Life System paragraph: OIL_LIFE_MONITOR item (common part)
        if AIR_LIFE.search(text_b):
            gaps.append({"field": "maintenance:engine_air_filter",
                         "reason": f"p.{page}: replaced when the Engine Air Filter Life System indicates; no fixed interval printed"})
            continue
        job = gm_job(text_b)
        if job is None:
            continue  # Multi-Point Vehicle Inspection, body lubrication: no maintenance job
        if iv is None:
            gaps.append({"field": f"maintenance:{job}", "reason": f"p.{page}: item without an interval heading"})
            continue
        months = iv["months"] or months_in(text_b)
        cond = "SEVERE" if b["section"] == "SEVERE" else "NORMAL"
        sentences = re.findall(r".+?\.(?=\s|$)", text_b) or [text_b]
        quote = sentences[0]
        for s in sentences[1:]:
            if months and not iv["months"] and months_in(quote) is None:
                quote += " " + s
        app = gm_applicability(text_b)
        if "transmission" in app and app["transmission"] in text_b:
            quote = text_b[: text_b.index(app["transmission"]) + len(app["transmission"])]
        if norm(quote) not in flat[page - 1]:
            quote = sentences[0]
        section_name = {"NORMAL": "Additional Required Services — Normal Service", "SEVERE": "Additional Required Services — Severe Service",
                        "OWNER": "Owner Checks and Services"}[b["section"]]
        cites = [(quote, page, f"{section_name}, {iv['head']}"), (iv["head"], iv["page"], f"{section_name}: interval heading")]
        entries.append({"job": job, "action": action_of(text_b), "condition": cond, "occurrence": "EVERY",
                        "interval": {"interval_km": iv["km"], "interval_miles_original": iv["mi"], "interval_months": months,
                                     "rule": "WHICHEVER_FIRST" if iv["km"] and months and re.search(r"whichever", text_b, re.I) else None},
                        "applicability": app, "note": None, "cites": cites})


# ---------------------------------------------------------------- common part
OIL_SENTENCE = re.compile(r"The engine oil and filter must be changed at least once a year")


def oil_life(pages: list[str], flat: list[str], first: int, entries: list, gaps: list):
    """The Engine Oil Change paragraph of the Maintenance Schedule (it may run over a page break)."""
    for index in range(max(first - 3, 0), min(first + 6, len(flat))):
        nxt = norm(" ".join(body_lines(pages[index + 1]))) if index + 1 < len(pages) else ""
        joined = flat[index] + " " + nxt
        m = OIL_SENTENCE.search(joined)
        if not m or m.start() >= len(flat[index]):
            continue
        if m.end() <= len(flat[index]):
            cites = [(m.group(0), index + 1, "Maintenance Schedule: Engine Oil Change (Oil Life System)")]
        else:
            cites = [(flat[index][m.start():].strip(), index + 1, "Maintenance Schedule: Engine Oil Change (Oil Life System)"),
                     (joined[len(flat[index]) + 1:m.end()].strip(), index + 2, "Maintenance Schedule: Engine Oil Change (continued)")]
        soon = re.search(r"have the engine oil and filter changed within the next ([\d ]+) km ?[/(] ?([\d,]+) mi", joined)
        note = ("Oil Life System: change the engine oil and filter when the change-oil message displays"
                + (f" (within the next {soon.group(1).strip()} km / {soon.group(2)} mi)" if soon else "")
                + "; at least once a year (as printed)")
        entries.append({"job": "engine_oil_and_filter", "action": "REPLACE", "condition": "NORMAL", "occurrence": "EVERY",
                        "system": "OIL_LIFE_MONITOR", "interval": None, "max_interval": {"interval_km": None, "interval_months": 12},
                        "applicability": {}, "note": note, "cites": cites})
        return
    gaps.append({"field": "maintenance:engine_oil_and_filter", "reason": "Oil Life System paragraph with a stated limit not found"})


def build() -> int:
    lines = our_lines(MAKE)
    per_line = defaultdict(lambda: {"sources": {}, "items": [], "gaps": []})
    for doc in documents():
        targets = [ln for ln in doc["lines"] if ln in lines]
        if not targets:
            continue
        try:
            pages = page_text(doc["sha256"])
        except FileNotFoundError:
            for ln in targets:
                per_line[ln]["gaps"].append({"scope": f"{MAKE}/{ln} MY{doc['years']} ({doc['key']})", "field": "maintenance:schedule",
                                             "reason": "page text of the PDF not in the pagetext store"})
            continue
        flat = [norm(p) for p in pages]
        entries, gaps = [], []
        grid_pages = [i for i, t in enumerate(flat) if MARK in t and len(HEAD_TEXT.findall(t)) >= 10 and chart_condition(t)]
        if grid_pages:
            layout_a(doc, pages, flat, grid_pages, entries, gaps)
            first = grid_pages[0]
        else:
            layout_b(doc, pages, flat, entries, gaps)
            first = next((i for i, t in enumerate(flat) if "Maintenance Schedule Tire Rotation" in t), 0)
        oil_life(pages, flat, first, entries, gaps)
        official = doc["tier"] == "A"
        used_pages = {c[1] for e in entries for c in e["cites"]}
        for ln in targets:
            line = lines[ln]
            gens = generations_of(MAKE, ln)
            years = [y for y in doc["years"] if line.years[0] <= y <= line.years[1]]
            scope = f"{MAKE}/{ln} MY{'-'.join(map(str, years))} ({doc['key']})"
            for g in gaps:
                per_line[ln]["gaps"].append({"scope": scope, **g})
            if not entries:
                continue
            per_line[ln]["sources"][doc["key"]] = pdf_source(
                doc["key"], doc["path"], doc["sha256"], doc["url"], doc["title"], doc["publisher"], REGISTRY, years,
                used_pages, doc["retrieved_at"],
                source_type="MAINTENANCE_SCHEDULE_OFFICIAL" if official else "OWNER_MANUAL_COPY",
                tier=doc["tier"], authenticity="OFFICIAL_PUBLISHER" if official else "REVIEWED_MIRROR")
            for year in years:
                gen = gen_for(gens, year)
                if gen is None:
                    per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:schedule", "reason": f"no generation for MY{year}"})
                    continue
                for e in entries:
                    app = dict(e["applicability"])
                    if doc["edition"]:
                        app["edition"] = doc["edition"]
                    quote, page, locator = e["cites"][0]
                    it = item(ln, gen, year, e["job"], e["action"], condition=e["condition"], occurrence=e["occurrence"],
                              system=e.get("system", "FIXED_INTERVAL"), interval=e["interval"], applicability=app,
                              note=e["note"], max_interval=e.get("max_interval"), source=doc["key"], quote=quote, page=page,
                              locator=locator, display_level="FACT" if official else "SECONDARY_NOTE",
                              confidence="HIGH" if official else "MEDIUM")
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
        systems = sorted({i["schedule_system"] for i in items})
        years = sorted({y for i in items for y in range(i["years"][0], i["years"][1] + 1)})
        print(f"{MAKE}/{ln}: items {len(items)}, years {years[0] if years else '-'}-{years[-1] if years else '-'}, "
              f"systems {systems}, sources {len(data['sources'])}, gaps {len(gaps)} -> {out.relative_to(WORK.parent)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(build())

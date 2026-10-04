"""Structured maintenance items from Hyundai and Kia US owner's manuals (schedule tables).

Every value is read from the PDF of the manual (page geometry with pdfplumber); every quote is a
substring of the page-text store of the same file (RAW_ROOT/pagetext/<sha256>.json.gz, compared
after maintenance_common.norm), so that check_maintenance_quotes.py / recheck_maintenance.py
find it again. Formats:

1. Grid ("Normal Maintenance Schedule"): one column per interval point (Months / Miles x 1,000 /
   Km x 1,000, whichever comes first) and one row per item with R (replace) / I (inspect) marks,
   or a merged text cell that states the interval. Newer Hyundai manuals print the grid rotated
   by 90 degrees; its geometry is turned back (logical frame) before it is read.
     - a character belongs to the cell that contains its centre (glyph boxes of a banner such as
       "Number of months or driving distance, whichever comes first" overlap the header cells and
       used to spoil the interval points of the rotated grids);
     - a mark belongs to the column whose header cell it overlaps (geometry, not the cell index);
     - a row split into sub-rows by an engine cell ("TGDI" / "EXCEPT TGDI", "(Gasoline engine)
       2.0 MPI") keeps the item label of the merged cell and carries the engine.
   Marks -> intervals:
     R (or I) at d, 2d, 3d ...                 -> EVERY d (miles, km as printed, months)
     first f, then a constant step s           -> FIRST f + SUBSEQUENT s
     irregular marks, months / miles / km that do not give the same pattern, an unknown mark, a
     label whose verb contradicts the mark ("Rotate tires" marked I) -> not converted (gap)
   Evidence: quote = row label + its marks as printed in the page text; locator = page, grid
   orientation, row and the interval points (column headers) of the marks.
2. Text (a grid text cell, a severe-table interval, a list-format bullet): clause by clause,
     "every X miles (Y km) or Z months"                   -> EVERY
     "At first, ... at X ... After that / thereafter ... every Y", "First, X ... after every Y"
                                                          -> FIRST X + SUBSEQUENT Y
     an interval with neither "every" nor "first"          -> not converted (gap)
   The cell is located in the page text (a cell cut at its ruling, "Every 3,750 MILES (6,000 ",
   is completed from the page text) and the values are parsed from that page text; the quote is
   the clause that carries the numbers (the whole first + after text for FIRST / SUBSEQUENT).
3. "Maintenance Under Severe Usage Conditions": item / (engine) / operation R-I / interval /
   driving conditions; recognised by its header cells, not by the page heading.
4. List format (older Kia): mileage blocks "7,500 miles (12,000 km) or 6 months" each followed by
   bullets "Inspect ..." / "Replace ...". Read in visual order (left column, right column, next
   page), so that a block continued in the next column or on the next page keeps its header.
   A bullet with its own interval text ("(Every ...)", "(First, ... after every ...)") is read
   as text; the other bullets give the interval by the blocks they are listed under.

Engine applicability: the table heading "(Smartstream G1.6 T-GDi)", "- Non Turbo Models", the
row's engine cell, or "(2.4 GDI)" / "- Turbo GDI" in a list bullet; "EXCEPT X" -> engine_except.
An engine footnote of a list page ("*6 : Engine oil (2.0 TGDI) Replace every 6,500 miles ..." or
"*3 Engine oil (1.6 TGDI/2.0 TGDI) At first, replace at 3,000 miles ..., after that, every ...") is an
item of that engine; a bullet that carries the mark ("Replace engine oil and filter *6 (Every 7,500
miles ...)") and names no engine of its own is then for the other engines (engine_except).
Drive applicability: a drive mark in the row label / bullet ("Rear differential oil (AWD)", "Transfer
case oil (4WD)") -> drive; a label naming two parts with the mark on one of them ("Front (AWD) / rear
differential oil") gives no single scope for the row -> not converted (gap).
Jobs of a row: a hybrid's coolant rows name the circuit ("Coolant (Inverter)", "Inverter coolant" ->
inverter_coolant; "Engine coolant / Inverter coolant", "Coolant (Engine/Inverter)" -> one interval for
both, engine_coolant and inverter_coolant).
Only miles-first schedules are read (km-first copies are not converted, as before).
An official (tier A) manual wins over a copy (tier B); two documents of the same rank that give
different intervals for one item and year: nothing is written, the conflict is logged.

Output: data_work/<make>/staging/<line>/maintenance.json (same format as build_maintenance.py).

  uv run --no-project --with pdfplumber --with pypdfium2 python scripts/build_maintenance_hmc.py hyundai|kia [--out DIR]
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_maintenance import JOBS, from_points, miles_to_km  # noqa: E402
from extract_manual_facts import documents  # noqa: E402
from maintenance_common import norm  # noqa: E402  (the normalisation of the quote checks)
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import BY_KEY  # noqa: E402

SETTINGS = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
EXTRA_JOBS = [
    ("engine_oil_and_filter", r"engine oil and (?:engine )?(?:oil )?filter"),
    ("dct_fluid", r"dual clutch transmission|\bDCT\b"),
    ("manual_transmission_fluid", r"manual transaxle"),  # "MANUAL TRANSAXLE FLUID" is not the automatic one
    ("tire_rotation", r"rotate tire"),
    ("cabin_air_filter", r"climate control air filter|air conditioning filter"),
]
SCHEDULE_PAGE = re.compile(r"maintenance schedule|severe usage|severe (?:driving )?conditions", re.I)
HEADING = re.compile(
    r"(Normal Maintenance Schedule|Maintenance Under Severe Usage Conditions|Severe Maintenance Schedule)"
    r"(?:\s*\((?P<engine>[^()]*\d\.\d[^()]*)\)"
    r"|\s*[-–]\s*(?P<engine2>(?:Non[- ])?Turbo(?: GDI)? Model|[A-Za-z ]{0,20}\d\.\d\s?L?\s?(?:T-?GDI|GDI|MPI|T-?GDi|GDi|MPi)?))?",
    re.I,
)
VERBS = {"inspect": "INSPECT", "lnspect": "INSPECT", "replace": "REPLACE", "change": "REPLACE", "rotate": "ROTATE"}  # "lnspect": a typo printed in the 2022+ Elantra N grids


def edition_of(doc: dict, make: str) -> str:
    """The manual's edition within the line ("elantra hybrid", "elantra n", "kona electric"):
    hybrid/EV/performance editions print their own schedules."""
    title = doc.get("title") or ""
    found = re.match(r"\d{4}\s+(.+?)\s+Owner", title)
    if found:
        name = found.group(1)
    else:
        name = re.sub(r"^carmans-\d{4}-", "", doc["key"]).replace(f"{make}-", "", 1)
    return " ".join(name.lower().replace("-", " ").split())


def job_of(text: str) -> str | None:
    for job, pattern in EXTRA_JOBS + JOBS:
        if re.search(pattern, text, re.I):
            return job
    return None


def jobs_of(text: str | None) -> list[str]:
    """Jobs a row label / bullet names. A coolant row of a hybrid names the circuit: 'Coolant
    (Inverter)', 'Inverter coolant' -> inverter_coolant; 'Engine coolant / Inverter coolant', 'Coolant
    (Engine/Inverter)' -> one interval for both circuits -> engine_coolant and inverter_coolant."""
    if not text:
        return []
    job = job_of(text)
    if re.search(r"\binverter\b", text, re.I) and job in ("engine_coolant", "cooling_system"):
        return ["engine_coolant", "inverter_coolant"] if re.search(r"\bengine\b", text, re.I) else ["inverter_coolant"]
    return [job] if job else []


def compact_engine(text: str | None) -> str:
    """Comparable engine name: '2.0 TGDI' = '2.0 T-GDI' = '2.0T-GDI'."""
    return re.sub(r"[\s\-]", "", (text or "").lower())


def number(text: str) -> float | None:
    t = (text or "").replace(",", "").strip()
    return float(t) if re.fullmatch(r"\d+(?:\.\d+)?", t) else None


def thousands(value: float) -> str:
    """7.5 (x 1,000 as printed in the header) -> '7,500'."""
    return f"{int(round(value * 1000)):,}"


def plain(value: float) -> str:
    return f"{value:g}"


# ---- geometry -------------------------------------------------------------------------------

def logical(box, rotated: bool, height: float) -> tuple:
    """Box (x0, top, x1, bottom) in the reading frame of the table: a rotated table reads bottom
    to top (its lines follow each other left to right)."""
    x0, top, x1, bottom = box
    return (height - bottom, x0, height - top, x1) if rotated else (x0, top, x1, bottom)


def char_box(c: dict) -> tuple:
    return c["x0"], c["top"], c["x1"], c["bottom"]


def text_of(chars: list[dict], rotated: bool, height: float) -> str:
    """Text of the characters in reading order (lines by the across-line position, characters by
    the along-line position, a space where the gap is wider than a quarter of the glyph height)."""
    boxes = sorted(((logical(char_box(c), rotated, height), c["text"]) for c in chars),
                   key=lambda bt: (bt[0][1] + bt[0][3]) / 2)
    lines: list[list] = []
    for box, t in boxes:
        cy, size = (box[1] + box[3]) / 2, max(box[3] - box[1], 1.0)
        if lines and abs(cy - lines[-1][0]) <= 0.5 * size:
            lines[-1][1].append((box, t))
        else:
            lines.append([cy, [(box, t)]])
    out = []
    for _, items in lines:
        parts, prev = [], None
        for box, t in sorted(items, key=lambda bt: bt[0][0]):
            if prev is not None and t.strip() and parts and parts[-1] != " " and box[0] - prev[2] > 0.25 * (box[3] - box[1]):
                parts.append(" ")
            parts.append(t)
            prev = box
        out.append(" ".join("".join(parts).split()))
    text = ""
    for line in out:  # a word broken at the line end: "Smart-" + "stream", "con-" + "nections"
        if text.endswith("-") and line[:1].islower():
            text = text[:-1] + line
        elif text.endswith("-"):
            text += line
        else:
            text = f"{text} {line}" if text else line
    return " ".join(text.split())


def overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def table_cells(page, table) -> tuple[list[dict], bool]:
    """Cells of a ruled table with their text (characters assigned by their centre) and logical
    boxes; whether the table is printed rotated."""
    bx0, btop, bx1, bbottom = table.bbox
    chars = [c for c in page.chars if c["text"]
             and bx0 <= (c["x0"] + c["x1"]) / 2 <= bx1 and btop <= (c["top"] + c["bottom"]) / 2 <= bbottom]
    glyphs = [c for c in chars if c["text"].strip()]
    rotated = sum(1 for c in glyphs if not c.get("upright", True)) > len(glyphs) / 2
    height = float(page.height)
    cells = [{"bbox": tuple(b), "box": logical(tuple(b), rotated, height), "chars": []} for b in table.cells]
    for c in chars:
        cx, cy = (c["x0"] + c["x1"]) / 2, (c["top"] + c["bottom"]) / 2
        for cell in cells:
            x0, top, x1, bottom = cell["bbox"]
            if x0 <= cx <= x1 and top <= cy <= bottom:
                cell["chars"].append(c)
                break
    for cell in cells:
        cell["text"] = text_of(cell["chars"], rotated, height)
    return cells, rotated


# ---- page text ------------------------------------------------------------------------------

def flex(text: str) -> str:
    """Regex of a text as printed, whatever the spacing or hyphenation (line-break hyphens) of the
    extraction."""
    return r"[\s\-­]*".join(re.escape(ch) for ch in text if not ch.isspace() and ch not in "-­")


# Case-sensitive with explicit spellings: the extraction glues words ("or 120 monthsAfter that"),
# so a word ends where a lower-case letter does not follow, and starts after a non-letter or at a
# lower-to-upper case join.
B = r"(?:(?<![A-Za-z])|(?<=[a-z])(?=[A-Z]))"
DIST = (r"(?P<miles>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(?:[Mm]iles?|MILES?|mi\.)(?![a-z])"
        r"(?:\s*\(\s*(?P<km>\d{1,3}(?:,\d{3})+|\d+)\s*(?:k\s?m|KM|Km)\s*\))?")
TIME = r"(?:\s*,?\s*(?:or|OR|Or)\s*(?P<time>\d+)\s*(?P<unit>[Mm]onths?|MONTHS?|[Yy]ears?|YEARS?)(?![a-z]))?"
PHRASE = re.compile(DIST + TIME)
TIME_ONLY = re.compile(B + r"(?:every|Every|EVERY)\s+(?P<time>\d+)\s*(?P<unit>[Mm]onths?|MONTHS?|[Yy]ears?|YEARS?)(?![a-z])")


def locate(text: str, page: str, start: int = 0, min_share: float = 0.6) -> tuple[int, int] | None:
    """Span of `text` in the normalised page text (searched from `start`, then from the top). A
    cell cut at its ruling is matched by its longest prefix (at least `min_share` of its words)
    and completed from the page text: the cut word, and an interval phrase cut in the middle."""
    words = text.split()
    if not words:
        return None
    low = max(1, min(len(words), int(len(words) * min_share + 0.999)))
    # every number of the cell must be in the matched prefix (a number cut at the ruling, "(120,0",
    # matches the start of the printed one and is completed below)
    numbered = [i for i, w in enumerate(words) if re.search(r"\d", w)]
    if numbered:
        low = max(low, numbered[-1] + 1)
    for n in range(len(words), low - 1, -1):
        pattern = re.compile(flex(" ".join(words[:n])))
        found = pattern.search(page, start) or (pattern.search(page) if start else None)
        if not found:
            continue
        s, e = found.span()
        while e < len(page) and page[e - 1].isalnum() and page[e].isalnum():
            e += 1
        for m in PHRASE.finditer(page, max(s, e - 60), min(len(page), e + 80)):
            if m.start() < e < m.end():
                e = m.end()
        if page[e - 1].isdigit():
            tail = re.match(r"\s*(?:months?|years?)\b", page[e:], re.I)
            if tail:
                e += tail.end()
        return s, e
    return None


# ---- interval text ----------------------------------------------------------------------------

FIRST_WORD = re.compile(B + r"(?:(?:at|At|AT)\s+)?(?:first|First|FIRST)(?![a-z])")
AFTER_WORD = re.compile(B + r"(?:after that|After that|After That|AFTER THAT|thereafter|Thereafter|THEREAFTER|after|After|AFTER)(?![a-z])")
EVERY_WORD = re.compile(B + r"(?:every|Every|EVERY)(?![a-z])")
VERB = re.compile(B + r"(inspect|Inspect|INSPECT|lnspect|replace|Replace|REPLACE|change|Change|CHANGE|rotate|Rotate|ROTATE|add|Add|ADD)(?![a-z])")


def clauses(text: str, default_action: str | None) -> tuple[list[dict], list[str]]:
    """Stated intervals of an interval text, in order: [{occurrence, action, miles, km, months,
    quote}] and the problems (an interval without "every" / "first", no action)."""
    found = [m for m in PHRASE.finditer(text)]
    spans = [m.span() for m in found]
    found += [m for m in TIME_ONLY.finditer(text) if not any(overlap(m.start(), m.end(), a, b) for a, b in spans)]
    found.sort(key=lambda m: m.start())
    out, problems, prev_end, prev = [], [], 0, None
    km_first = [m for m in found if re.search(r"km\s*\(\s*$", text[:m.start()], re.I)]
    if km_first:
        # "every 12,000 km (7,500 miles)": a km-first schedule, not read (as before); a text that
        # mixes it with miles-first clauses is not read either (its first / after parts would split)
        m = km_first[0]
        return [], [f"km-first interval (miles in parentheses); not converted: {text[max(0, m.start() - 30):m.end() + 1]}"]
    for m in found:
        before = text[prev_end:m.start()]
        verbs = list(VERB.finditer(before))
        first = FIRST_WORD.search(before)
        after = AFTER_WORD.search(before)
        if first:
            occurrence, start = "FIRST", prev_end + first.start()
        elif after and prev is not None and prev["occurrence"] == "FIRST":
            occurrence, start = "SUBSEQUENT", prev_end + after.start()
        elif after:
            problems.append(f"'after' interval without a first one: {text[max(prev_end, m.start() - 30):m.end()]}")
            prev_end = m.end()
            continue
        elif "miles" not in m.groupdict() or re.search(EVERY_WORD.pattern + r"\s*$", before):
            every = list(EVERY_WORD.finditer(before))
            occurrence = "EVERY"
            start = prev_end + (verbs[-1].start() if verbs else every[-1].start() if every else 0)
            if m.re is TIME_ONLY:
                start = m.start() if not verbs else prev_end + verbs[-1].start()
        else:
            problems.append(f"interval without 'every' or 'first': {text[max(prev_end, m.start() - 30):m.end()]}")
            prev_end = m.end()
            continue
        if verbs:
            word = verbs[-1].group(1).lower()
            action = VERBS.get(word)
            if word == "add":
                prev_end = m.end()
                continue  # fuel additives: not a service item of the schedule
        elif prev is not None and occurrence == "SUBSEQUENT":
            action = prev["action"]
        else:
            action = default_action
        if action is None:
            problems.append(f"action not stated: {text[max(prev_end, m.start() - 30):m.end()]}")
            prev_end = m.end()
            continue
        g = m.groupdict()
        months = None
        if g.get("time"):
            months = int(g["time"]) * (12 if g["unit"].lower().startswith("year") else 1)
        miles = float(g["miles"].replace(",", "")) if g.get("miles") else None
        entry = {"occurrence": occurrence, "action": action, "miles": miles,
                 "km": int(g["km"].replace(",", "")) if g.get("km") else None, "months": months,
                 "start": start, "end": m.end()}
        out.append(entry)
        prev, prev_end = entry, m.end()
    for n, e in enumerate(out):  # FIRST + SUBSEQUENT quote the whole first ... after ... text
        if e["occurrence"] == "FIRST" and n + 1 < len(out) and out[n + 1]["occurrence"] == "SUBSEQUENT":
            e["end"] = out[n + 1]["end"]
            out[n + 1]["start"] = e["start"]
            if e["action"] != out[n + 1]["action"]:
                # "At first, inspect at 6,000 miles ... After that, replace every 48,000 miles ...": the
                # first and the following intervals name different operations -> ambiguous, not read
                problems.append(f"first / after clauses name different operations: {text[e['start']:out[n + 1]['end']]}")
                e["drop"] = out[n + 1]["drop"] = True
    out = [e for e in out if not e.get("drop")]
    for e in out:
        e["quote"] = text[e.pop("start"):e.pop("end")].strip(" ,;:")
    return out, problems


# ---- grid ---------------------------------------------------------------------------------------

HEAD_MONTHS = re.compile(r"months?", re.I)
HEAD_MILES = re.compile(r"miles(?P<x>\s*[×x]\s*1,?000)?", re.I)  # 2020 Sonata Hybrid prints "Miles 7.5 15 ..." without "x 1,000"
HEAD_KM = re.compile(r"km(?P<x>\s*[×x]\s*1,?000)?", re.I)
MARK = re.compile(r"[RI]|[-–]")


def grid(page, table) -> dict | None:
    """Interval points (columns) and rows of a normal-schedule grid, or None when the table has
    no Months / Miles header. {"rotated", "columns": [{months, miles, km}], "rows": [{label, sub,
    text, marks {column: mark}, problems}], "problem"}."""
    cells, rotated = table_cells(page, table)
    heads = {}
    for name, pattern in (("months", HEAD_MONTHS), ("miles", HEAD_MILES), ("km", HEAD_KM)):
        heads[name] = next((c for c in cells if c["text"] and pattern.fullmatch(c["text"])), None)
    if not heads["months"] or not heads["miles"]:
        return None

    def values(head):
        hx0, hy0, hx1, hy1 = head["box"]
        row = [c for c in cells if number(c["text"]) is not None and c["box"][0] >= hx1 - 1
               and overlap(hy0, hy1, c["box"][1], c["box"][3]) >= 0.6 * min(hy1 - hy0, c["box"][3] - c["box"][1])]
        return sorted(row, key=lambda c: c["box"][0])

    rows_of = {name: values(head) for name, head in heads.items() if head}
    columns = []
    for mc in rows_of["months"]:
        col = {"lx0": mc["box"][0], "lx1": mc["box"][2], "months": number(mc["text"]), "miles": None, "km": None}
        width = mc["box"][2] - mc["box"][0]
        for name in ("miles", "km"):
            hit = [c for c in rows_of.get(name, []) if overlap(c["box"][0], c["box"][2], col["lx0"], col["lx1"]) >= 0.5 * width]
            if len(hit) == 1:
                col[name] = number(hit[0]["text"])
        columns.append(col)
    implied = not HEAD_MILES.fullmatch(heads["miles"]["text"]).group("x")
    out = {"rotated": rotated, "columns": columns, "rows": [], "problem": None, "implied": implied}
    if not columns or any(c["miles"] is None for c in columns) or (heads["km"] and any(c["km"] is None for c in columns)):
        out["problem"] = "header points: months / miles / km columns do not line up"
        return out
    if implied and (not heads["km"] or HEAD_KM.fullmatch(heads["km"]["text"]).group("x")
                    or not all(1.5 <= c["km"] / c["miles"] <= 1.7 for c in columns)):
        # "Miles 7.5 15 ..." / "Km 12 24 ...": thousands only when both rows agree (km / miles about 1.6)
        out["problem"] = "header points: 'Miles' without 'x 1,000' and no matching 'Km' row"
        return out
    for name in ("months", "miles", "km"):
        seq = [c[name] for c in columns if c[name] is not None]
        if any(b <= a for a, b in zip(seq, seq[1:])):
            out["problem"] = f"header points: {name} not increasing {seq}"
            return out
    head_bottom = max(c["box"][3] for name in rows_of for c in [heads[name]] + rows_of[name])
    data_x0 = min(c["lx0"] for c in columns)
    body = [c for c in cells if c["box"][1] >= head_bottom - 1]
    labels = [c for c in body if c["box"][2] <= data_x0 + 2]
    data = [c for c in body if c["box"][0] >= data_x0 - 2]
    bands = sorted({(round(c["box"][1], 1), round(c["box"][3], 1)) for c in data})
    for y0, y1 in bands:
        # label cells beside the band: the item label (several when one merged interval cell serves
        # stacked items) and, further right, the engine cell of a sub-row
        cover = [c for c in labels if c["text"] and overlap(y0, y1, c["box"][1], c["box"][3]) >= 0.5 * min(y1 - y0, c["box"][3] - c["box"][1])]
        if not cover:
            continue
        x_main = min(c["box"][0] for c in cover)
        mains = sorted((c for c in cover if c["box"][0] <= x_main + 2), key=lambda c: c["box"][1])
        subs = sorted((c for c in cover if c["box"][0] > x_main + 2), key=lambda c: c["box"][1])
        row = {"label": None, "sub": None, "text": None, "marks": {}, "problems": [], "band": (y0, y1)}
        spans = []
        for c in sorted((c for c in data if (round(c["box"][1], 1), round(c["box"][3], 1)) == (y0, y1)), key=lambda c: c["box"][0]):
            if not c["text"]:
                continue
            cols = [k for k, col in enumerate(columns)
                    if overlap(c["box"][0], c["box"][2], col["lx0"], col["lx1"]) >= 0.5 * (col["lx1"] - col["lx0"])]
            if len(cols) == 1 and MARK.fullmatch(c["text"]):
                row["marks"][cols[0]] = c["text"]
            elif len(c["text"]) > 3:
                spans.append(c["text"])
            else:
                row["problems"].append(f"unrecognised mark {c['text']!r} over {len(cols)} column(s)")
        if spans:
            row["text"] = " ".join(spans)
            if any(m in ("R", "I") for m in row["marks"].values()):
                row["problems"].append("row mixes marks and interval text")
        for main in mains:
            for sub in subs or [None]:
                out["rows"].append({**row, "label": main["text"], "sub": sub["text"] if sub else None,
                                    "marks": dict(row["marks"]), "problems": list(row["problems"])})
    return out


def grid_quote(row: dict, page: str) -> str | None:
    """The row as printed in the page text: label [engine cell] marks (the dash of an empty cell
    and the spacing may differ). None when the marks are not printed in column order there."""
    marks = [m for _, m in sorted(row["marks"].items()) if m in ("R", "I")]
    tail = r"(?![\s\-–]*[RI](?![A-Za-z:])(?!\s+:))"  # no further mark (the legend "I : Inspect" may follow)
    pattern = flex(row["label"])
    if row["sub"]:
        pattern += r"[\s\S]{0,120}?" + flex(row["sub"])
    pattern += r"[\s\-–]*" + r"[\s\-–]*".join(marks) + tail
    found = re.search(pattern, page)
    if found and len(found.group(0)) <= 400:
        return found.group(0)
    return None


def engine_of_cell(text: str | None) -> dict:
    """Engine cell of a row: 'TGDI' -> engine, 'EXCEPT TGDI' -> engine_except; the fuel note
    '(Gasoline engine)' in front of the engine name is dropped."""
    if not text:
        return {}
    t = re.sub(r"^\((?:gaso-?\s*line)(?:\s+engine)?\)\s*", "", norm(text), flags=re.I)
    t = re.sub(r"\s*\*\s?\d+$", "", t)  # footnote marker: "HEV*4"
    except_ = re.fullmatch(r"except\s+(.+)", t, re.I)
    return {"engine_except": except_.group(1)} if except_ else {"engine": t}


DRIVE_MARK = re.compile(r"\(\s*(AWD|4WD|2WD|FWD|RWD)(?:\s+(?:only|models?))?\s*\)", re.I)


def drive_applic(label: str | None) -> dict | None:
    """Drive scope printed in the row label / bullet: 'Rear differential oil (AWD)', 'Transfer case oil
    (4WD)', 'Differential oil (rear) (AWD)' -> {'drive': 'AWD'}; no mark -> {}. A label that names two
    parts and restricts only one of them ('Front (AWD) / rear differential oil', 'Front differential oil
    (AWD) / Rear differential oil') does not give one scope for the row -> None (not converted)."""
    t = norm(label or "")
    marks = DRIVE_MARK.findall(t)
    if not marks:
        return {}
    drives = {m.upper() for m in marks}
    if len(drives) > 1:
        return None
    parts = [p for p in re.split(r"\s/\s|/(?=\s*[A-Za-z]{3})", t) if re.search(r"[A-Za-z]{3}", p)]
    if len(parts) > 1 and not all(DRIVE_MARK.search(p) for p in parts):
        return None
    return {"drive": drives.pop()}


def mark_entries(row: dict, columns: list[dict], where: str) -> tuple[list[dict], list[str]]:
    """Intervals of a row of marks; the problems of the marks that are not converted."""
    out, problems = [], []
    verb = re.match(r"\s*(rotate|replace|inspect)\b", row["label"], re.I)
    for letter, action in (("R", "REPLACE"), ("I", "INSPECT")):
        idx = sorted(k for k, m in row["marks"].items() if m == letter)
        if not idx:
            continue
        pts = [columns[k] for k in idx]
        listing = "/".join(thousands(p["miles"]) for p in pts)
        if verb and VERBS[verb.group(1).lower()] != action:
            problems.append(f"row '{row['label']}' marked {letter}: the label names another operation; not converted")
            continue
        months = from_points([int(round(p["months"])) for p in pts])
        miles = from_points([int(round(p["miles"] * 10)) for p in pts])
        km = from_points([int(round(p["km"] * 10)) for p in pts]) if all(p["km"] is not None for p in pts) else None
        shapes = [s for s in (months, miles, km) if s is not None]
        if months is None or miles is None or (km is None and any(p["km"] is not None for p in pts)) \
                or len({tuple(x["occurrence"] for x in s) for s in shapes}) != 1:
            problems.append(f"irregular {letter} marks at {listing} miles; not converted")
            continue
        locator = (f"{where}: {letter} at {listing} miles; months {'/'.join(plain(p['months']) for p in pts)}"
                   + (f"; km {'/'.join(thousands(p['km']) for p in pts)}" if km else ""))
        for n, step in enumerate(miles):
            out.append({"occurrence": step["occurrence"], "action": action, "miles": step["miles"] * 100,
                        "km": km[n]["miles"] * 100 if km else None, "months": months[n]["miles"],
                        "locator": locator})
    return out, problems


# ---- severe table -------------------------------------------------------------------------------

def severe_rows(page, table) -> list[dict] | None:
    """Rows of a "Maintenance Under Severe Usage Conditions" table: label, engine cell, operation,
    interval text; None when the table is not one."""
    cells, rotated = table_cells(page, table)
    head = {}
    for c in cells:
        t = c["text"].lower()
        if re.fullmatch(r"maintenance\s+item", t):
            head["item"] = c
        elif re.fullmatch(r"maintenance\s+operation", t):
            head["op"] = c
        elif re.fullmatch(r"maintenance\s+intervals?", t):
            head["interval"] = c
    if not {"item", "op", "interval"} <= set(head):
        return None
    bottom = max(h["box"][3] for h in head.values())
    body = [c for c in cells if c["box"][1] >= bottom - 1]
    item_x1 = head["op"]["box"][0]

    def in_col(c, h):
        return overlap(c["box"][0], c["box"][2], h["box"][0], h["box"][2]) >= 0.5 * (c["box"][2] - c["box"][0])

    rows = []
    for y0, y1 in sorted({(round(c["box"][1], 1), round(c["box"][3], 1)) for c in body if in_col(c, head["interval"]) and c["text"]}):
        def covers(c):
            return overlap(y0, y1, c["box"][1], c["box"][3]) >= 0.5 * min(y1 - y0, c["box"][3] - c["box"][1])

        interval = next((c for c in body if in_col(c, head["interval"]) and c["text"]
                         and (round(c["box"][1], 1), round(c["box"][3], 1)) == (y0, y1)), None)
        op = next((c["text"] for c in body if in_col(c, head["op"]) and c["text"] and covers(c)), None)
        names = [c for c in body if c["box"][2] <= item_x1 + 2 and c["text"] and covers(c)]
        if not names or interval is None:
            continue
        # the item label (several when one merged interval cell serves stacked items) and, further
        # right, the engine cell of a sub-row
        x_main = min(c["box"][0] for c in names)
        mains = sorted((c for c in names if c["box"][0] <= x_main + 2), key=lambda c: c["box"][1])
        subs = sorted((c for c in names if c["box"][0] > x_main + 2), key=lambda c: c["box"][1])
        for main in mains:
            for sub in subs or [None]:
                rows.append({"label": main["text"], "sub": sub["text"] if sub else None, "operation": op, "text": interval["text"]})
    return rows


# ---- list format (older Kia) ----------------------------------------------------------------------

POINT_LINE = re.compile(r"(?P<miles>\d{1,3}(?:,\d{3})+|\d+(?:\.\d)?)\s*miles\s*\((?P<km>\d{1,3}(?:,\d{3})*)\s*km\)\s*or\s*(?P<months>\d+)\s*months")
NO_SERVICE = re.compile(r"no check,?\s*no service required", re.I)
ITEM_ENGINE = re.compile(r"\((\d\.\d[^()]*?)\)")
LABEL_ENGINE = re.compile(r"\(([^()]*\d\.\d[^()]*|[^()]*\b(?:T-?GDI|GDI|MPI|T-?GDi|GDi|MPi|Turbo)\b[^()]*)\)")  # "ENGINE OIL AND FILTER (MPI/GDI)"
# '*4 Engine oil (1.6 TGDI) Replace every 6,500 miles ...', '*6 : Engine oil (2.0 TGDI) Replace every ...',
# '*3 Engine oil (1.6 TGDI/2.0 TGDI) At first, replace at 3,000 miles ..., after that, every 5,000 miles ...'
FOOTNOTE = re.compile(
    r"\*(?P<n>\d+)\s*:?\s*(?P<label>[A-Za-z][A-Za-z ,/&]{3,40}?)\s*\((?P<engine>\d\.\d[^()]*)\)\s*"
    r"(?P<text>(?:(?:Replace|Inspect|Change)\s+every\s+|At\s+first\b)[^*❈]+?)(?=\*\d|❈|$)", re.I
)


def footnote_sentence(text: str) -> str:
    """The footnote's own interval sentence (bullets of the next block may follow it in the text): up to
    its first interval phrase, or its second one for 'At first, ... after that, every ...'."""
    phrases = list(PHRASE.finditer(text))
    if not phrases:
        return text
    k = 2 if re.match(r"at\s+first", text, re.I) and len(phrases) >= 2 else 1
    return text[:phrases[k - 1].end()]
BULLET = "❑"


def list_lines(page) -> list[list[dict]]:
    """Text lines of a list-format page, left column then right column, each top to bottom."""
    mid = float(page.width) / 2
    out = []
    for right in (False, True):
        side = page.filter(lambda o, right=right: o.get("object_type") != "char" or (((o["x0"] + o["x1"]) / 2) >= mid) == right)
        out.append(sorted(side.extract_text_lines(strip=True), key=lambda ln: ln["top"]))
    return out


def top_parens(text: str) -> list[tuple[int, int]]:
    """Spans of the top-level parenthesised groups of a text."""
    spans, depth, start = [], 0, None
    for i, ch in enumerate(text):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
            if depth == 0:
                spans.append((start, i + 1))
    return spans


def split_own(part: str) -> tuple[str, str | None]:
    """'Replace coolant (First, 60,000 miles ...)' / 'MPI/GDI Engine : Every 7,500 miles ...' ->
    (head, own interval text)."""
    colon = re.search(r"\s*:\s*(?=(?:every|at first|first)\b)", part, re.I)
    if colon:
        return part[:colon.start()], part[colon.end():]
    parens = [p for p in top_parens(part) if re.search(r"\bmiles\b", part[p[0]:p[1]], re.I)]
    if parens:
        s, e = parens[-1]
        return part[:s] + part[e:], part[s + 1:e - 1]
    return part, None


def parse_bullet(text: str) -> dict | None:
    """'Replace coolant (First, 60,000 miles ... after every ...)' -> verb, label, own interval
    text, engine; '- Turbo GDI (Every ...)' / '- MPI/GDI Engine : Every ...' variants of the bullet."""
    verb = re.match(r"(Inspect|Replace|Rotate|Change|Add)\b", text, re.I)
    if not verb:
        return None
    variants = []
    base = text
    sub = re.search(r"\s-\s*(?=[A-Z])", text)
    if sub:
        base, rest = text[:sub.start()], text[sub.end():]
        for part in re.split(r"\s-\s*(?=[A-Z])", rest):
            head, own = split_own(part)
            variants.append({"engine": norm(head).strip(" :;"), "own": norm(own) if own else None})
    label, own = split_own(base)
    engine = ITEM_ENGINE.search(label)
    return {"action": VERBS.get(verb.group(1).lower()), "verb": verb.group(1).lower(), "label": norm(label),
            "own": norm(own) if own else None, "engine": norm(engine.group(1)) if engine else None,
            "variants": variants, "text": norm(text)}


def page_text(sha: str) -> list[str]:
    with gzip.open(RAW_ROOT / "pagetext" / f"{sha}.json.gz", "rt", encoding="utf-8") as handle:
        return json.load(handle)["pages"]


# ---- build ----------------------------------------------------------------------------------------

def build(make: str, out_root: Path | None = None) -> int:
    docs = []
    for doc in documents(make):
        extracted = WORK / make / "extracted" / f"{doc['key']}.json"
        if not extracted.exists():
            continue
        info = json.loads(extracted.read_text(encoding="utf-8"))
        if info.get("status") == "ok" and info.get("edition_market") == "US":
            docs.append(doc)
    by_line = defaultdict(list)
    for doc in docs:
        for line in doc["lines"]:
            by_line[line].append(doc)
    for line_key, line_docs in sorted(by_line.items()):
        line = BY_KEY[line_key]
        staging_path = WORK / make / "staging" / line.slug / "staging.json"
        if not staging_path.exists():
            continue
        gens = json.loads(staging_path.read_text(encoding="utf-8"))["generations"]
        sources, gaps, conflicts = {}, [], []
        observed = defaultdict(lambda: defaultdict(list))  # (gen, job, action, condition, occurrence, applic) -> year -> [(entry, cite, tier)]
        for doc in line_docs:
            try:
                texts = page_text(doc["sha256"])
            except FileNotFoundError:
                continue
            flat_pages = [norm(t) for t in texts]
            candidates = [i for i, t in enumerate(texts) if SCHEDULE_PAGE.search(t) and re.search(r"miles", t, re.I)]
            used_pages = set()

            def gap(index, job, reason):
                gaps.append({"scope": f"{line_key} {doc['key']}" + (f" p.{index + 1}" if index is not None else ""),
                             "field": f"maintenance {job}", "reason": reason})

            def record(job, applic, entry, condition, index, quote, locator):
                quote = norm(quote)
                if not quote or quote not in flat_pages[index]:
                    gap(index, job, f"quote not found in the page text; not used: {quote[:80]}")
                    return
                applicability = {"edition": edition_of(doc, make), **applic}
                km = entry["km"] or (miles_to_km(int(entry["miles"])) if entry["miles"] else None)
                item = {"job": job, "action": entry["action"], "condition": condition,
                        "schedule_system": "FIXED_INTERVAL", "occurrence": entry["occurrence"],
                        "interval_km": km, "interval_months": entry["months"],
                        "interval_miles_original": int(entry["miles"]) if entry["miles"] else None,
                        "rule": "WHICHEVER_FIRST" if entry["months"] and entry["miles"] else None, "note": None}
                cite = {"source": doc["key"], "quote": quote, "pages": [index + 1], "locator": locator}
                for year in doc["years"]:
                    gen = next((g["code"] for g in gens if g["start_year"] <= year <= g["end_year"]), None)
                    if gen is None or not (line.years[0] <= year <= line.years[1]):
                        continue
                    scope = json.dumps([gen, job, entry["action"], condition, entry["occurrence"], applicability], sort_keys=True)
                    observed[scope][year].append((item, cite, doc["tier"]))
                    used_pages.add(index + 1)

            def engine_applic(row_engine: dict, label: str | None, engine_head: str | None) -> dict:
                """The row's engine cell, else an engine named in the label, else the table heading's."""
                in_label = LABEL_ENGINE.search(label or "")
                return row_engine or ({"engine": norm(in_label.group(1))} if in_label else {}) \
                    or ({"engine": engine_head} if engine_head else {})

            def text_entries(text, default, index, hint, job, where):
                """Clauses of an interval text located in the page text (values from the page text)."""
                span = locate(text, flat_pages[index], hint)
                if span is None:
                    gap(index, job, f"interval text not found in the page text: {text[:100]}")
                    return []
                found, problems = clauses(flat_pages[index][span[0]:span[1]], default)
                for p in problems:
                    gap(index, job, f"{where}: {p}")
                return found

            last_engine = None
            list_pages = []
            page_footnotes = {}  # page index -> footnote mark -> (job, engine) of an engine footnote
            with pdfplumber.open(doc["path"]) as pdf:
                for index in candidates:
                    page = pdf.pages[index]
                    page_norm = flat_pages[index]
                    heads = list(HEADING.finditer(page_norm))
                    named = {norm(h.group("engine") or h.group("engine2") or "") for h in heads}
                    if heads:
                        engine_names = {n for n in named if n}
                        if len(engine_names) > 1:
                            last_engine = "AMBIGUOUS"
                        else:
                            last_engine = next(iter(engine_names), None)
                    engine_head = last_engine
                    try:
                        tables = page.find_tables(SETTINGS)
                    except Exception:  # noqa: BLE001 - a damaged page must not stop the document
                        continue
                    tables_used = False
                    for table in tables:
                        g = grid(page, table)
                        if g is not None:
                            tables_used = True
                            if g["problem"]:
                                gap(index, "schedule grid", g["problem"])
                                continue
                            where_grid = f"page {index + 1} grid" + (" (rotated)" if g["rotated"] else "") \
                                + (" (header 'Miles' / 'Km' without 'x 1,000': thousands)" if g["implied"] else "")
                            for row in g["rows"]:
                                for job in jobs_of(row["label"]) or jobs_of(row["sub"]):
                                    if engine_head == "AMBIGUOUS":
                                        gap(index, job, "two engine headings on the page; not converted")
                                        continue
                                    for p in row["problems"]:
                                        gap(index, job, f"row '{row['label']}': {p}")
                                    if row["problems"]:
                                        continue
                                    applic = engine_applic(engine_of_cell(row["sub"]), row["label"], engine_head)
                                    where = f"{where_grid} row '{row['label']}'" + (f" / '{row['sub']}'" if row["sub"] else "")
                                    drive = drive_applic(row["label"])
                                    if drive is None:
                                        gap(index, job, f"{where}: the drive mark restricts only one part of the row; not converted")
                                        continue
                                    applic = {**applic, **drive}
                                    if row["text"]:
                                        hint = page_norm.find(norm(row["label"])[:20])
                                        for c in text_entries(row["text"], None, index, max(hint, 0), job, where):
                                            record(job, applic, c, "NORMAL", index, c["quote"], f"{where}: text cell")
                                        continue
                                    found, problems = mark_entries(row, g["columns"], where)
                                    for p in problems:
                                        gap(index, job, p)
                                    if not found:
                                        continue
                                    quote = grid_quote(row, page_norm)
                                    if quote is None:
                                        gap(index, job, f"{where}: marks not found in column order in the page text; not used")
                                        continue
                                    for c in found:
                                        record(job, applic, c, "NORMAL", index, quote, c["locator"])
                            continue
                        severe = severe_rows(page, table)
                        if severe is None:
                            continue
                        tables_used = True
                        for row in severe:
                            for job in jobs_of(row["label"] or "") or jobs_of(row["sub"]):
                                if engine_head == "AMBIGUOUS":
                                    gap(index, job, "two engine headings on the page; not converted")
                                    continue
                                default = {"R": "REPLACE", "I": "INSPECT"}.get((row["operation"] or "").strip())
                                applic = engine_applic(engine_of_cell(row["sub"]), row["label"], engine_head)
                                where = f"page {index + 1} severe table row '{row['label']}'" + (f" / '{row['sub']}'" if row["sub"] else "")
                                drive = drive_applic(row["label"])
                                if drive is None:
                                    gap(index, job, f"{where}: the drive mark restricts only one part of the row; not converted")
                                    continue
                                applic = {**applic, **drive}
                                hint = page_norm.find(norm(row["label"])[:20])
                                for c in text_entries(row["text"], default, index, max(hint, 0), job, where):
                                    if default and c["action"] in ("REPLACE", "INSPECT") and c["action"] != default:
                                        gap(index, job, f"{where}: operation {row['operation']} but the text says {c['action'].lower()}; not used")
                                        continue
                                    record(job, applic, c, "SEVERE", index, c["quote"], f"{where}: operation {row['operation']}")
                    if not tables_used and BULLET in texts[index]:
                        list_pages.append((index, engine_head))
                    if not tables_used and BULLET in texts[index]:
                        for f in FOOTNOTE.finditer(page_norm):
                            # the job of the footnote's label, else of the bullet that carries its mark and
                            # names the label ('Replace engine oil and filter *6' for '*6 : Engine oil (2.0 TGDI) ...')
                            job = job_of(f.group("label"))
                            if not job:
                                carriers = [m.group(1) for m in re.finditer(rf"{BULLET}\s*([^{BULLET}❈*]{{3,90}}?)\s*\*\s?{f.group('n')}(?!\d)", page_norm)
                                            if compact_engine(f.group("label")) in compact_engine(m.group(1))]
                                jobs = {job_of(x) for x in carriers} - {None}
                                job = jobs.pop() if len(jobs) == 1 else None
                            if not job:
                                continue
                            # a bullet that carries this mark gives its interval to the other engines
                            page_footnotes.setdefault(index, {})[f.group("n")] = (job, norm(f.group("engine")))
                            found, problems = clauses(footnote_sentence(f.group("text")), None)
                            for p in problems:
                                gap(index, job, f"footnote: {p}")
                            drive = drive_applic(f.group("label"))
                            if drive is None:
                                gap(index, job, "footnote: the drive mark restricts only one part of the label; not converted")
                                continue
                            for c in found:
                                record(job, {"engine": norm(f.group("engine")), **drive}, c, "NORMAL", index, c["quote"],
                                       f"page {index + 1} footnote '{norm(f.group('label'))} ({norm(f.group('engine'))})'")
                # list format: blocks in visual order across columns and pages
                bullets, block, last_index = [], None, None
                for index, engine_head in list_pages:
                    if last_index is not None and index != last_index + 1:
                        block = None
                    last_index = index
                    for column in list_lines(pdf.pages[index]):
                        cur = None
                        for ln in column:
                            t = ln["text"].strip()
                            head = POINT_LINE.fullmatch(t)
                            if head:
                                block = {"miles": float(head.group("miles").replace(",", "")), "km": int(head.group("km").replace(",", "")),
                                         "months": int(head.group("months")), "page": index, "text": t}
                                cur = None
                            elif NO_SERVICE.search(t):
                                block, cur = None, None
                            elif t.startswith(BULLET):
                                cur = {"block": block, "lines": [t[1:].strip()], "x0": ln["x0"], "bottom": ln["bottom"],
                                       "page": index, "engine_head": engine_head}
                                bullets.append(cur)
                            elif cur and ln["x0"] > cur["x0"] + 2 and ln["top"] - cur["bottom"] < 0.9 * (ln["bottom"] - ln["top"]) \
                                    and not re.match(r"\(Continued\)|\*\d|❈", t):
                                cur["lines"].append(t)
                                cur["bottom"] = ln["bottom"]
                            else:
                                cur = None
            grouped = defaultdict(list)
            for b in bullets:
                info = parse_bullet(" ".join(b["lines"]))
                if not info or info["action"] is None:
                    continue
                for job in jobs_of(info["label"]):
                    index, page_norm = b["page"], flat_pages[b["page"]]
                    if b["engine_head"] == "AMBIGUOUS" and not info["engine"]:
                        gap(index, job, "two engine headings on the page; not converted")
                        continue
                    engine = info["engine"] or b["engine_head"]
                    where = f"page {index + 1} list bullet '{info['label']}'"
                    # 'Replace engine oil and filter *6 (Every 7,500 miles ...)' + '*6 : Engine oil (2.0 TGDI) Replace
                    # every 6,500 miles ...': the footnote gives that engine its own interval, the bullet's is for the others
                    foot_engines = sorted({e for n in re.findall(r"\*\s?(\d+)", info["label"])
                                           for j, e in [page_footnotes.get(index, {}).get(n, (None, None))] if j == job and e})
                    variants = []
                    if not info["variants"]:
                        if foot_engines and engine is None:
                            variants.append((info["own"], {"engine_except": " / ".join(foot_engines)}))
                        elif foot_engines and any(compact_engine(e) == compact_engine(engine) for e in foot_engines):
                            gap(index, job, f"{where}: the bullet's engine has its own interval in the footnote; not converted")
                        else:
                            variants.append((info["own"], {} if engine is None else {"engine": engine}))
                    elif info["own"]:
                        # the bullet's own interval and '- Turbo GDI (...)': the own one is for the other engines
                        variants.append((info["own"], {"engine": engine} if engine else {"engine_except": " / ".join(v["engine"] for v in info["variants"])}))
                    # an engine variant with its own interval ("- MPI/GDI Engine : Every ...") is read as text;
                    # one without ("Replace spark plugs - Turbo GDI") takes the blocks it is listed under. The
                    # bullet itself, without an interval of its own, gives nothing besides its variants.
                    variants += [(v["own"], {"engine": v["engine"]}) for v in info["variants"]]
                    drive = drive_applic(info["label"])
                    if drive is None:
                        gap(index, job, f"{where}: the drive mark restricts only one part of the bullet; not converted")
                        continue
                    variants = [(own, {**applic, **drive}) for own, applic in variants]
                    bullet_span = locate(info["text"], page_norm, min_share=1.0)
                    for own, applic in variants:
                        if own and POINT_LINE.fullmatch(own) is None:
                            # the interval text inside this bullet (the same words can belong to another
                            # bullet of the page: "- Turbo GDI (Every 7,500 miles (12,000 km) or 12 months)")
                            inside = re.compile(flex(own)).search(page_norm, *bullet_span) if bullet_span else None
                            if inside is None:
                                gap(index, job, f"{where}: bullet text not found in the page text: {info['text'][:100]}")
                                continue
                            found, problems = clauses(inside.group(0), info["action"])
                            for p in problems:
                                gap(index, job, f"{where}: {p}")
                            for c in found:
                                record(job, applic, c, "NORMAL", index, c["quote"], f"{where}: own interval text")
                            continue
                        if own:  # the bullet's own point "(7,500 miles (12,000 km) or 12 months)"
                            head = POINT_LINE.fullmatch(own)
                            point = {"miles": float(head.group("miles").replace(",", "")), "km": int(head.group("km").replace(",", "")),
                                     "months": int(head.group("months")), "page": index, "text": own}
                        elif b["block"] is not None:
                            point = b["block"]
                        else:
                            continue
                        grouped[(job, info["action"], json.dumps(applic, sort_keys=True))].append((point, b, info))
            for (job, action, applic_json), rows in grouped.items():
                applic = json.loads(applic_json)
                points = sorted({(p["miles"], p["km"], p["months"]): (p, b, info) for p, b, info in rows}.items())
                first_p, first_b, first_info = points[0][1]
                listing = "; ".join(f"{p['text']} (p.{p['page'] + 1})" for _, (p, _, _) in points)
                miles = from_points([int(round(pt[0])) for pt, _ in points])
                months = from_points([pt[2] for pt, _ in points])
                km = from_points([pt[1] for pt, _ in points])
                if miles is None or months is None or km is None or \
                        len({tuple(s["occurrence"] for s in x) for x in (miles, months, km)}) != 1:
                    gap(first_b["page"], job, f"irregular list points of '{first_info['label']}': {listing}; not converted")
                    continue
                index = first_b["page"]
                span = locate(first_info["text"], flat_pages[index]) or locate(first_info["label"], flat_pages[index])
                if span is None:
                    gap(index, job, f"list bullet not found in the page text: {first_info['text'][:80]}")
                    continue
                quote = flat_pages[index][span[0]:span[1]]
                locator = f"page {index + 1} list schedule: '{first_info['label']}' listed under {listing}"
                for n, step in enumerate(miles):
                    record(job, applic, {"occurrence": step["occurrence"], "action": action, "miles": float(step["miles"]),
                                         "km": int(km[n]["miles"]), "months": int(months[n]["miles"])},
                           "NORMAL", index, quote, locator)
            if used_pages:
                extract = {"pdf_sha256": doc["sha256"], "url": doc["url"],
                           "pages": {str(p): texts[p - 1] for p in sorted(used_pages)}}
                sources[doc["key"]] = {
                    "key": doc["key"], "kind": "pdf_pages", "path": "rawstore:" + Path(doc["path"]).relative_to(RAW_ROOT).as_posix(),
                    "url": doc["url"], "page_url": doc.get("page_url"), "sha256": doc["sha256"], "retrieved_at": doc["retrieved_at"],
                    "tier": doc["tier"], "source_type": doc["source_type"], "registry": f"factory-{make}-us",
                    "title": doc.get("title") or f"{make} owner's manual {doc['years']} ({doc['key']})",
                    "publisher": doc["publisher"], "authenticity": doc["authenticity"], "edition": "US",
                    "model_year": doc["years"][0] if doc["years"] else None,
                    "extract": json.dumps(extract, ensure_ascii=False),
                }
        # one interval per item and year: official before copy; same rank disagreeing -> not written
        chosen = defaultdict(dict)  # scope -> year -> (item, cites)
        for scope, by_year in observed.items():
            for year, rows in by_year.items():
                variants = defaultdict(list)
                for item, cite, tier in rows:
                    variants[json.dumps(item, sort_keys=True)].append((cite, tier))
                if len(variants) == 1:
                    item_json, cites = next(iter(variants.items()))
                    chosen[scope][year] = (item_json, dedupe([c for c, _ in cites]))
                    continue
                ranked = sorted(variants.items(), key=lambda kv: (min(t for _, t in kv[1]), -len(kv[1])))
                best = min(t for _, t in ranked[0][1])
                leaders = [kv for kv in ranked if min(t for _, t in kv[1]) == best]
                gen, job, action, condition, occurrence, applicability = json.loads(scope)
                if len(leaders) == 1:
                    chosen[scope][year] = (ranked[0][0], dedupe([c for c, _ in ranked[0][1]]))
                    resolution = "official manual kept over the copy"
                elif len({c["source"] for _, cs in leaders for c, _ in cs}) == 1:
                    # '*6 : Engine oil (2.0 TGDI) Replace every 6,500 miles (10,000 km) or 12 months' on most
                    # pages, '... or 6 months' on two pages of the same manual
                    resolution = "the document prints different values for the item on different pages; item not written"
                else:
                    resolution = "documents of the same rank disagree; item not written"
                conflicts.append({"scope": f"{line_key} {gen} MY{year}", "key": f"maintenance {job} {action} {condition} {occurrence}",
                                  "applicability": applicability,
                                  "values": [{k: json.loads(v)[k] for k in ("interval_km", "interval_months", "interval_miles_original")}
                                             for v, _ in ranked],
                                  "sources": [sorted({c["source"] for c, _ in cs}) for _, cs in ranked],
                                  "evidence": [sorted({f"{c['source']} p.{c['pages'][0]}: {c['locator']}" for c, _ in cs}) for _, cs in ranked],
                                  "resolution": resolution})
        items = []
        for scope, by_year in chosen.items():
            gen, job, action, condition, occurrence, applicability = json.loads(scope)
            runs = []
            for year in sorted(by_year):
                item_json, cites = by_year[year]
                if runs and runs[-1]["item"] == item_json and runs[-1]["years"][-1] == year - 1:
                    runs[-1]["years"].append(year)
                    runs[-1]["cites"] = dedupe(runs[-1]["cites"] + cites)
                else:
                    runs.append({"item": item_json, "years": [year], "cites": list(cites)})
            for run in runs:
                item = json.loads(run["item"])
                tiers = {sources[c["source"]]["tier"] for c in run["cites"] if c["source"] in sources}
                digest = hashlib.sha1((scope + run["item"]).encode()).hexdigest()[:8]
                primary = sorted(run["cites"], key=lambda c: (sources[c["source"]]["tier"], c["source"]))[0]["source"]
                items.append({
                    "id": f"{line.slug}-{gen}-mnt-{job}-{digest}-{run['years'][0]}",
                    "generation": gen, "years": [run["years"][0], run["years"][-1]], "engine": None,
                    "applicability": applicability, **item, "max_interval_km": None, "max_interval_months": None,
                    "cites": run["cites"], "primary_source": primary,
                    "display_level": "FACT" if "A" in tiers else "SECONDARY_NOTE",
                    "confidence": "HIGH" if "A" in tiers else "MEDIUM",
                })
        # one gap per document, item and reason (the list format repeats a bullet on every page)
        seen, unique = set(), []
        for g in gaps:
            key = (g["scope"].split(" p.")[0], g["field"], re.sub(r"\bpage \d+ |\(p\.\d+\)", "", g["reason"]))
            if key not in seen:
                seen.add(key)
                unique.append(g)
        gaps = unique
        root = out_root / make / line.slug if out_root else WORK / make / "staging" / line.slug
        root.mkdir(parents=True, exist_ok=True)
        (root / "maintenance.json").write_text(json.dumps({"sources": sources, "items": items, "gaps": gaps, "conflicts": conflicts},
                                                          ensure_ascii=False, indent=1), encoding="utf-8")
        print(line_key, "items", len(items), "sources", len(sources), "gaps", len(gaps), "conflicts", len(conflicts), flush=True)
    return 0


def dedupe(cites: list[dict]) -> list[dict]:
    out = []
    for c in cites:
        if c not in out:
            out.append(c)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    out_dir = Path(args[args.index("--out") + 1]) if "--out" in args else None
    sys.exit(build(args[0], out_dir))

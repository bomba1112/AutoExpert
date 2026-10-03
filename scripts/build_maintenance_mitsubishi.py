"""Mitsubishi maintenance schedules from the official US "Warranty & Maintenance Manual"
booklets (www.mitsubishicars.com; manifest data_work/_shared/manifest_official/
www.mitsubishicars.com.csv, 15 booklets, page text from the pagetext store).

Two layouts are printed:
  * 2014 (passenger cars and SUVs): point lists "Regular maintenance schedule" / "Severe
    maintenance schedule": headings "● 22,500 Miles (36,000 km) or at 18 months" (or "● 12
    Months") followed by the tasks; the interval of a task is derived from the points where it is
    listed (EVERY d, FIRST f + SUBSEQUENT s, a single point -> FIRST); a footnote that states the
    interval ("* Change at first 120,000 Miles (192,000 km) or at 96 months, thereafter every
    90,000 Miles (144,000 km) or 72 months") wins over the points.
  * 2015-2023: grids "Schedule 1" (severe: "Use Schedule 1 if you primarily operate your vehicle
    under any of these conditions") and "Schedule 2" (normal), one column per point ("miles x
    1,000 / km x 1,000 / months"), an X per due service, printed turned by 90 degrees. The text
    layer loses the columns, so the X positions are read from the content stream
    (pdf_geometry.page_runs) and matched to the column headings; the rows are the bands between
    the row rules (pdf_geometry.page_vrules; a parent cell with sub-rows, e.g. "Inspect and adjust
    valve clearance" / "4J1 engine and 6B3 engine", gives one row per sub-row). Marks at d, 2d ...
    -> EVERY; first f then a constant step -> FIRST + SUBSEQUENT; one mark -> FIRST; anything
    else -> gap. A text cell states the interval ("Every 105,000 miles (168,000 km)", "First
    change at ... thereafter every ..."); a footnote that states an interval wins over the marks
    ("*3: After 40,000 miles (64,000 km) or 48 months, inspect every 10,000 miles (16,000 km) or
    12 months"); a footnote that makes the interval conditional ("*10: If towing a trailer ...
    change (not just inspect) oil at every 20,000 miles ...") adds a SEVERE item with the printed
    condition as "operation"; "Periodic maintenance is not required" rows are gaps.

The booklets cover several models. Only rows for our lines (Outlander, Outlander Sport) are kept:
a row whose except-clause names the line ("Change brake fluid (except Lancer, Lancer Sportback,
Outlander Sport)") or that is printed for another model only ("Lancer 2.4L with 18" wheels") is
not written for it. Engine codes ("4J1 engine and 6B3 engine"), "(if so equipped)", "(except
vehicles with timing chain)" etc. go to the applicability as printed. Outlander PHEV booklets
carry {"edition": "Outlander PHEV"}; a gasoline booklet carries {"edition": "Outlander"} in a model
year that also has a PHEV booklet in the manifests. Model years without a booklet on disk are
gaps (the 2017, 2018, 2024, 2025 booklets are listed in mmna-ssb.my.salesforce.com.csv, whose
robots.txt disallows them).

Output: data_work/mitsubishi/staging/<line>/maintenance_official.json (maintenance_common.write).

  .venv/Scripts/python.exe scripts/build_maintenance_mitsubishi.py
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
from build_maintenance import from_points  # noqa: E402
from maintenance_common import (  # noqa: E402
    JOBS, action_of, gen_for, generations_of, item, merge_years, norm, our_lines, page_text, pdf_source, write,
)
from pdf_geometry import page_hrules, page_runs, page_vrules  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

MAKE = "mitsubishi"
NAME = "official"
REGISTRY = "factory-mitsubishi-us"
MANIFEST = WORK / "_shared" / "manifest_official" / "www.mitsubishicars.com.csv"
SKIPPED = WORK / "_shared" / "manifest_official" / "mmna-ssb.my.salesforce.com.csv"
PUBLISHER = "Mitsubishi Motors North America (Warranty & Maintenance Manual, mitsubishicars.com)"
MODELS = {"outlander": r"\bOutlander(?! Sport)(?! PHEV)", "outlander-sport": r"\bOutlander Sport\b"}
OTHER_MODELS = r"\b(?:Lancer|Mirage|Eclipse Cross|i-MiEV)\b"

MITSU_JOBS = [  # tried before maintenance_common.JOBS
    ("engine_oil_and_filter", r"change engine oil|engine oil filter|replace oil filter"),
    ("cabin_air_filter", r"air purifier filter"),
    ("engine_air_filter", r"air cleaner filter"),
    ("valve_clearance", r"valve clear\s?ance"),
    ("fuel_system", r"fuel system for leaks"),
    ("fuel_lines", r"fuel hoses|fuel lines"),
    ("fuel_filter", r"fuel filter"),
    ("evap_system", r"evaporative emission"),
    ("accessory_drive_belt", r"drive belts?"),
    ("exhaust_system", r"exhaust system"),
    ("cooling_system_hoses", r"coolant hoses"),
    ("motor_coolant", r"motor coolant"),
    ("motor_cooling_oil", r"motor cooling oil"),
    ("manual_transmission_fluid", r"manual transaxle/transmission oil"),
    ("transmission_fluid", r"automatic transaxle/transmission|CVT fluid|transaxle oil"),
    ("transfer_case_fluid", r"transfer oil|transfer fluid"),
    ("differential_fluid", r"rear axle oil|differential gear oil"),
    ("brake_lines", r"brake hoses|brake lines"),
    ("brakes", r"brake pads|drum brake linings"),
    ("steering_linkage", r"steering linkage|steering gear"),
    ("suspension", r"suspension system"),
    ("driveshaft_boots", r"drive ?shaft boots"),
    ("high_voltage_wiring", r"high voltage wire"),
    ("key_fob_battery", r"transmitter battery"),
    ("tire_rotation", r"^\W*rotate tires"),
]
COMPONENTS = [  # parts that share a job: the component as printed tells the rows apart
    (r"disc brake pads and rotors|brake pads & rotors", "disc brake pads and rotors"),
    (r"rear drum brake linings", "rear drum brake linings and wheel cylinders"),
    (r"front transaxle oil", "front transaxle"),
    (r"rear transaxle oil", "rear transaxle"),
    (r"front motor", "front motor"),
    (r"rear motor", "rear motor"),
    (r"transfer fluid & differential gear oil", "transfer fluid & differential gear oil"),
]
MILES_KM = r"([\d,]+) miles \(([\d,]+) km\)"


def num(text: str) -> int:
    return int(str(text).replace(",", ""))


def job_of(text: str) -> str | None:
    for job, pattern in MITSU_JOBS + JOBS:
        if re.search(pattern, text, re.I):
            return job
    for job, pattern in MITSU_JOBS:  # words printed without spaces ("Checkevaporativeemissioncontrolsystem")
        if re.search(pattern.replace(" ", r"\s*"), text, re.I):
            return job
    return None


def mitsu_action(text: str) -> str:
    t = text.lower()
    if re.match(r"\W*(check|inspect)\b", t) and not re.search(r"\badjust\b", t):
        return "INSPECT"
    return action_of(text)


# ---------------------------------------------------------------- documents and editions
def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [r for r in csv.DictReader(handle) if r["make"] == MAKE]


def is_phev(title: str) -> bool:
    return bool(re.search(r"PHEV|Plug-In Hybrid", title, re.I))


def documents() -> tuple[list[dict], list[dict]]:
    docs = []
    for r in read_csv(MANIFEST):
        if r["status"] != "ok" or r["doc_type"] != "warranty_maintenance":
            continue
        lines = [x for x in r["lines"].split(";") if x]
        years = [int(y) for y in r["years"].split(";") if y]
        stem = re.sub(r"[^a-z0-9]+", "-", Path(r["path"]).stem.lower()).strip("-")
        docs.append({"key": f"mitsubishi-wm-{years[0]}-{stem}"[:90], "lines": lines, "years": years, "title": r["title"],
                     "path": RAW_ROOT / r["path"], "url": r["url"], "sha256": r["sha256"], "retrieved_at": r["retrieved_at"],
                     "phev": is_phev(r["title"])})
    skipped = [r for r in read_csv(SKIPPED) if r["status"] != "ok"]
    return docs, skipped


# ---------------------------------------------------------------- applicability and scoping
def excluded_for(line: str, text: str) -> str | None:
    """Reason why a row printed for several models is not for this line, else None."""
    for clause in re.findall(r"\(except ([^)]*)\)|\bExcept ([^.;)]*)", text, re.I):
        clause = " ".join(clause)
        if re.search(MODELS[line], clause):
            return f"the row excludes {('Outlander Sport' if line == 'outlander-sport' else 'Outlander')} ('except {clause.strip()}')"
    positive = re.sub(r"\(except [^)]*\)|\bExcept [^.;)]*", "", text, flags=re.I)
    named_other = re.search(OTHER_MODELS, positive)
    if named_other and not re.search(MODELS["outlander"] + "|" + MODELS["outlander-sport"], positive):
        return f"the row is printed for {named_other.group(0)} only"
    return None


def applicability(text: str) -> dict:
    app = {}
    codes = re.findall(r"\b(\d[A-Z]\d{1,2})\s+engine", text)
    if codes:
        app["engine"] = "/".join(dict.fromkeys(codes))
    if re.search(r"\(intake side\)", text):
        app["side"] = "intake"
    if re.search(r"\(if so equipped\)", text, re.I):
        app["equipment"] = "if so equipped"
    m = re.search(r"\(except (vehicles with [^)]*)\)", text, re.I)
    if m:
        app["equipment_except"] = norm(m.group(1))
    for pattern, name in COMPONENTS:
        if re.search(pattern, text, re.I):
            app["component"] = name
            break
    return app


def footnote_note(text: str) -> str | None:
    t = norm(text)
    return t if t else None


# ---------------------------------------------------------------- page text spans
def find_span(flat: str, label: str, start: int = 0) -> tuple[int, int] | None:
    key = "".join(ch.lower() for ch in label if ch.isalnum())
    if not key:
        return None
    chars, pos = [], []
    for i, ch in enumerate(flat):
        if ch.isalnum():
            chars.append(ch.lower())
            pos.append(i)
    comp = "".join(chars)
    at = comp.find(key, sum(1 for p in pos if p < start))
    if at < 0:
        return None
    end = pos[at + len(key) - 1] + 1
    while end < len(flat) and flat[end] in ").,;:]":
        end += 1
    return pos[at], end


# ---------------------------------------------------------------- grids (2015-2023)
HEADS = {"miles": "miles x 1,000", "km": "km x 1,000", "months": "months"}


def table_runs(reader: PdfReader, index: int) -> tuple[list[dict], list[tuple[float, float, float]]] | None:
    """Runs and row rules of a grid page in table coordinates: r grows down the rows, c along the
    columns. The 2015-2020 booklets turn the table by 90 degrees (text read upwards: r = page x,
    c = page y, row rules are page-vertical); the 2021-2022 Outlander Sport booklets print it
    upright (r = -page y, c = page x, row rules page-horizontal)."""
    runs = page_runs(reader, index, cid_unicode=True)
    head = next((r for r in runs if r["text"].strip().startswith("miles x 1,000") or r["text"].strip() == "miles"), None)
    if head is None:
        return None
    turned = head["rotated"]
    out = []
    for r in runs:
        if r["rotated"] != turned:
            continue
        if turned:
            out.append({"text": r["text"], "glyphs": list(r["glyphs"]), "r": r["x"], "c": r["y"], "size": r["size"]})
        else:
            glyphs = [(ch, -gy, gx) for ch, gx, gy in r["glyphs"]]
            out.append({"text": r["text"], "glyphs": glyphs, "r": -r["y"], "c": r["x"], "size": r["size"]})
    if turned:
        rules = [(y0, y1, x) for y0, y1, x in page_vrules(reader, index)]
    else:
        rules = [(x0, x1, -y) for x0, x1, y in page_hrules(reader, index)]
    return out, rules


def header_line(runs: list[dict], prefix: str) -> tuple[float, list, float] | None:
    """(r, glyphs in c order, font size) of the header row that starts with the prefix ("miles x
    1,000", "km x 1,000", "months"): all runs of one line (one run, or one run per word)."""
    lines = []
    for run in sorted(runs, key=lambda r: r["r"]):
        if lines and abs(run["r"] - lines[-1][0]) < 1:
            lines[-1][1].append(run)
        else:
            lines.append((run["r"], [run]))
    for r_pos, members in lines:
        glyphs = sorted((g for m in members for g in m["glyphs"]), key=lambda g: g[2])
        text = " ".join("".join(g[0] for g in glyphs).split())
        if text.startswith(prefix):
            return r_pos, glyphs, max(m["size"] for m in members)
    return None


def header_tokens(glyphs: list, prefix: str, size: float) -> list[tuple[float, float]]:
    """(value, c) of the numbers of a header row after its label; digits set apart by kerning
    instead of spaces ("months6 1218...") are split where two glyph centres are more than 0.8 x
    the font size apart."""
    skip = len(prefix.replace(" ", ""))
    rest, seen = [], 0
    for g in glyphs:
        if seen < skip:
            seen += 1 if g[0].strip() else 0
            continue
        rest.append(g)
    out, cur, cs = [], "", []
    for ch, _, gc in rest + [(" ", 0, 1e9)]:
        if (ch.isdigit() or ch == ".") and not (cs and gc - cs[-1] > 0.8 * size):
            cur += ch
            cs.append(gc)
            continue
        if cur.strip("."):
            out.append((float(cur), sum(cs) / len(cs)))
        cur, cs = (ch, [gc]) if (ch.isdigit() or ch == ".") else ("", [])
    return out


def piece(glyphs: list, size: float) -> tuple:
    """(r, first c, text, last c, size) of glyphs of one run."""
    visible = [g for g in glyphs if g[0].strip()] or glyphs
    return (sum(g[1] for g in visible) / len(visible), glyphs[0][2], "".join(g[0] for g in glyphs), glyphs[-1][2], size)


def lines_of(pieces: list[tuple]) -> list[str]:
    """Texts of a cell joined line by line: pieces less than 3.5 pt apart across the lines (a
    raised "*2" footnote mark) are one line, read in c order; pieces set as separate words (one
    run per word, no space glyph) get a space where the gap is wider than a letter."""
    lines = []
    for p in sorted(pieces):
        if lines and p[0] - lines[-1][0] < 3.5:
            lines[-1][1].append(p)
        else:
            lines.append((p[0], [p]))
    out = []
    for _, parts in lines:
        text, last = "", None
        for _, c0, t, c1, size in sorted(parts, key=lambda p: p[1]):
            if last is not None and text and not text.endswith(" ") and not t.startswith(" ") and c0 - last > 0.65 * size:
                text += " "
            text += t
            last = c1
        out.append(text.strip())
    return out


MARK_RUN = re.compile(r"^(?:X(?:\*\d*(?:,\s?\*\d+)*)?\s*)+$")


def split_label(glyphs: list, grid_left: float) -> tuple[list, list]:
    """Glyphs of a run before the grid (row label) and in it (marks, text cells): a word that
    starts in the label column stays in the label; a text cell may run past the last column."""
    label, area, in_word = [], [], False
    for g in glyphs:
        if area:
            area.append(g)
        elif g[2] < grid_left or (in_word and g[0].strip() and g[0] != "X"):
            label.append(g)
            in_word = bool(g[0].strip())
        else:
            area.append(g)
    return label, area


def grid(reader: PdfReader, index: int) -> dict:
    found = table_runs(reader, index)
    if found is None:
        return {"error": "column heading 'miles x 1,000' not found"}
    runs, raw_rules = found
    heads = {}
    for key, prefix in HEADS.items():
        found_line = header_line(runs, prefix)
        if found_line is None:
            return {"error": f"column heading '{prefix}' not found"}
        r_pos, glyphs, size = found_line
        heads[key] = (r_pos, header_tokens(glyphs, prefix, size))
    miles = heads["miles"][1]
    if len(miles) < 5:
        return {"error": "mileage column headings not read"}
    pitch = statistics.median(b[1] - a[1] for a, b in zip(miles, miles[1:]))
    columns = []
    for value, c in miles:
        k = min(heads["km"][1], key=lambda t: abs(t[1] - c), default=None)
        mo = min(heads["months"][1], key=lambda t: abs(t[1] - c), default=None)
        if k is None or mo is None or abs(k[1] - c) > 0.5 * pitch or abs(mo[1] - c) > 0.5 * pitch:
            return {"error": f"column {value} without km / months heading"}
        columns.append({"miles": int(round(value * 1000)), "km": int(round(k[0] * 1000)), "months": int(mo[0]), "c": c,
                        "head": (f"{value:g}", f"{k[0]:g}", f"{int(mo[0])}")})
    head_r = max(heads[k][0] for k in heads) + 2
    grid_left = columns[0]["c"] - 0.5 * pitch  # the label column ends about half a pitch before the first column
    grid_right = columns[-1]["c"] + 0.6 * pitch
    body = [r for r in runs if r["r"] > head_r]
    label_left = min((r["c"] for r in body if r["c"] < grid_left and r["text"].strip()), default=None)
    if label_left is None:
        return {"error": "row labels not found"}
    segments = defaultdict(list)  # a rule may be drawn in pieces: pieces on one line are joined
    for c0, c1, r_pos in raw_rules:
        segments[round(r_pos, 1)].append((c0, c1))
    rules = []
    for r_pos, parts in segments.items():
        parts.sort()
        span = list(parts[0])
        for c0, c1 in parts[1:]:
            if c0 <= span[1] + 2:
                span[1] = max(span[1], c1)
            else:
                rules.append((span[0], span[1], r_pos))
                span = [c0, c1]
        rules.append((span[0], span[1], r_pos))
    # row rules reach at least the end of the label column (the upright 2021-2022 grids draw them
    # in the label column only; the turned ones across the whole table)
    rules = [(c0, c1, r_pos) for c0, c1, r_pos in rules if r_pos > head_r - 1 and c1 >= grid_left - 5]
    major = sorted({r_pos for c0, c1, r_pos in rules if c0 < label_left + 5})
    minor = [(r_pos, c0) for c0, c1, r_pos in rules if label_left + 5 <= c0 < grid_left]
    if len(major) < 2:
        return {"error": "row rules not found"}
    rows = []
    for lo, hi in zip(major, major[1:]):
        inner = [(r_pos, c0) for r_pos, c0 in minor if lo + 1 < r_pos < hi - 1]
        subs = sorted(r_pos for r_pos, _ in inner)
        sub_c0 = min((c0 for _, c0 in inner), default=None)
        bounds = [lo] + subs + [hi]
        rows.append({"band": (lo, hi), "sub_c0": sub_c0, "label": [],
                     "subs": [{"band": (a, b), "label": [], "marks": [], "notes": {}, "cell": []} for a, b in zip(bounds, bounds[1:])]})

    def row_of(r_pos: float):
        for row in rows:
            if row["band"][0] < r_pos < row["band"][1]:
                sub = next((s for s in row["subs"] if s["band"][0] < r_pos < s["band"][1]), row["subs"][0])
                return row, sub
        return None, None

    for run in body:
        label_glyphs, area = split_label(run["glyphs"], grid_left)
        if label_glyphs and "".join(g[0] for g in label_glyphs).strip():
            visible = [g for g in label_glyphs if g[0].strip()]
            r_pos = sum(g[1] for g in visible) / len(visible)
            row, sub = row_of(r_pos)
            if row is not None:
                text = "".join(g[0] for g in label_glyphs)
                target = sub["label"] if row["sub_c0"] is not None and visible[0][2] >= row["sub_c0"] - 1 else row["label"]
                target.append(piece(label_glyphs, run["size"]))
        visible = [g for g in area if g[0].strip()]
        if not visible:
            continue
        r_pos = sum(g[1] for g in visible) / len(visible)
        row, sub = row_of(r_pos)
        if row is None:
            continue
        text = "".join(g[0] for g in area).strip()
        if MARK_RUN.match(text):
            last = None
            for n, (ch, gr, gc) in enumerate(area):
                if ch == "X":
                    col = min(range(len(columns)), key=lambda i: abs(columns[i]["c"] - gc))
                    if gc > grid_right or abs(columns[col]["c"] - gc) > 0.35 * pitch:
                        sub.setdefault("problems", []).append(f"mark between columns at c={gc:.1f}")
                    else:
                        sub["marks"].append(col)
                        last = col
                elif ch == "*" and last is not None:
                    ref = re.match(r"\*(\d+)", "".join(g[0] for g in area[n:]))
                    if ref:
                        sub["notes"].setdefault(last, []).append(ref.group(1))
        else:
            sub["cell"].append(piece(area, run["size"]))
    out = []
    for row in rows:
        parent = " ".join(lines_of(row["label"]))
        for sub in row["subs"]:
            sub_label = " ".join(lines_of(sub["label"]))
            cell = " ".join(lines_of(sub["cell"]))
            refs = re.findall(r"\d+", cell) if re.fullmatch(r"[\d,\s*]+", cell.strip()) else []
            if refs:  # "X*1": the reference of a mark set apart from it
                cell = ""
                sub["notes"].setdefault(-1, []).extend(refs)
            if not (parent.strip() or sub_label.strip()):
                continue
            out.append({"parent": norm(parent) if row["sub_c0"] is not None else None,
                        "label": norm(sub_label) if row["sub_c0"] is not None else norm(parent),
                        "marks": sorted(set(sub["marks"])), "notes": sub["notes"], "cell": norm(cell),
                        "problems": sub.get("problems", [])})
    return {"columns": columns, "rows": out}


FOOTNOTE = re.compile(r"\*(\d+):\s*(.+?)(?=\s\*\d+:|\sMAINTENANCE ITEM|\s\S+\.book|$)")
REFS = re.compile(r"\*(\d+)(?:\s*,\s*\*(\d+))?")


def footnotes(raw_pages: list[str]) -> tuple[dict, dict]:
    """{n: text} and {n: the footnote as printed ("*10:If towing ...")} of a schedule's pages. A
    footnote starts a line ("*10:") and runs over the next lines until a line ends a sentence (the
    table rows that follow the footnotes in the text layer are not taken)."""
    out, raw = {}, {}
    for page in raw_pages:
        lines = [ln.strip() for ln in page.splitlines()]
        n = 0
        while n < len(lines):
            m = re.match(r"\*(\d+):\s*(.*)$", lines[n])
            if not m:
                n += 1
                continue
            parts = [lines[n]]
            while not parts[-1].rstrip().endswith(".") and n + 1 < len(lines) and lines[n + 1] \
                    and not re.match(r"\*\d+:|MAINTENANCE ITEM|\S+\.book", lines[n + 1]):
                n += 1
                parts.append(lines[n])
            text = norm(" ".join(parts))
            raw.setdefault(m.group(1), text)
            out.setdefault(m.group(1), re.sub(r"^\*\d+:\s*", "", text))
            n += 1
    return out, raw


def foot_quote(raw: str, needle: str | None = None) -> str:
    """The footnote as printed up to the end of the sentence that holds the needle (default: its
    first sentence)."""
    at = raw.find(needle) if needle else 0
    end = raw.find(". ", max(at, 0))
    return raw if end < 0 else raw[:end + 1]


def interval_from_points(points: list[tuple[int, int, int | None]]) -> list[dict] | None:
    """[(miles, km, months)] of the marks -> [{occurrence, interval}] or None (irregular)."""
    sm = from_points([p[0] for p in points])
    sk = from_points([p[1] for p in points])
    with_time = all(p[2] for p in points)
    st = from_points([p[2] for p in points]) if with_time else None
    shape = lambda s: [x["occurrence"] for x in s] if s else None  # noqa: E731
    if not sm or shape(sm) != shape(sk) or (with_time and shape(sm) != shape(st)):
        return None
    out = []
    for n, s in enumerate(sm):
        months = st[n]["miles"] if with_time else None
        out.append({"occurrence": s["occurrence"],
                    "interval": {"interval_km": sk[n]["miles"], "interval_miles_original": s["miles"], "interval_months": months,
                                 "rule": "WHICHEVER_FIRST" if months else None}})
    return out


FIRST_THEN = re.compile(r"First (?:change|check) at " + MILES_KM + r"(?: or at (\d+) months)?\s?, thereafter every " + MILES_KM + r"(?: or (\d+) months)?", re.I)
FIRST_THEN_2014 = re.compile(r"Change at first ([\d,]+) Miles \(([\d,]+) km\)(?: or at (\d+) months)?, thereafter every ([\d,]+) Miles \(([\d,]+) km\)(?: or (\d+) months)?", re.I)
FIRST_ONLY = re.compile(r"First (?:change|check) at " + MILES_KM + r"(?: or at (\d+) months)?(?!\s?,? thereafter)\s*$", re.I)
AFTER_EVERY = re.compile(r"After " + MILES_KM + r"(?: or (\d+) months)?, inspect every " + MILES_KM + r"(?: or (\d+) months)?", re.I)
EVERY = re.compile(r"every " + MILES_KM + r"(?: or (?:every )?(\d+) months?)?", re.I)
EVERY_MONTHS = re.compile(r"^every (\d+) months?$", re.I)


def iv(miles, km, months) -> dict:
    months = int(months) if months else None
    return {"interval_km": num(km), "interval_miles_original": num(miles), "interval_months": months,
            "rule": "WHICHEVER_FIRST" if months else None}


def stated(text: str) -> list[dict] | None:
    m = FIRST_THEN.search(text) or FIRST_THEN_2014.search(text)
    if m:
        return [{"occurrence": "FIRST", "interval": iv(m.group(1), m.group(2), m.group(3))},
                {"occurrence": "SUBSEQUENT", "interval": iv(m.group(4), m.group(5), m.group(6))}]
    m = FIRST_ONLY.search(text)
    if m:
        return [{"occurrence": "FIRST", "interval": iv(m.group(1), m.group(2), m.group(3))}]
    m = AFTER_EVERY.search(text)
    if m:
        return [{"occurrence": "FIRST", "interval": iv(m.group(1), m.group(2), m.group(3))},
                {"occurrence": "SUBSEQUENT", "interval": iv(m.group(4), m.group(5), m.group(6))}]
    m = EVERY.search(text)
    if m:
        return [{"occurrence": "EVERY", "interval": iv(m.group(1), m.group(2), m.group(3))}]
    m = EVERY_MONTHS.search(text.strip())
    if m:
        return [{"occurrence": "EVERY", "interval": {"interval_km": None, "interval_miles_original": None,
                                                     "interval_months": int(m.group(1)), "rule": None}}]
    return None


CONDITIONAL = re.compile(r"^If (?P<cond>(?:towing|driving|operating|using)[^.]*?), (?P<rest>(?:inspect|change).*)$", re.I)


def conditional_items(note: str) -> list[dict]:
    """'If towing a trailer ..., change (not just inspect) oil at every 20,000 miles (32,000 km) or
    24 months.' -> SEVERE items with the printed condition."""
    m = CONDITIONAL.match(note)
    if not m:
        return []
    out = []
    for sentence in re.split(r"(?<=\.)\s+", m.group("rest")):
        e = EVERY.search(sentence)
        if not e:
            continue
        if re.search(r"change \(not just inspect\)", sentence, re.I):
            action = "REPLACE"
        elif re.search(r"\binspect\b", sentence, re.I):
            action = "INSPECT"
        else:
            continue
        out.append({"action": action, "interval": iv(e.group(1), e.group(2), e.group(3)), "operation": norm(m.group("cond")),
                    "needle": e.group(0)})
    return out


def grid_items(doc: dict, pages: list[str], flat: list[str], entries: list, gaps: list):
    reader = PdfReader(str(doc["path"]))
    grid_pages = [i for i, t in enumerate(pages) if "miles x 1,000" in t]
    by_schedule = defaultdict(list)
    for i in grid_pages:
        m = re.search(r"^\s*Schedule ([12])\b", pages[i][:200], re.M)
        if m:
            by_schedule[m.group(1)].append(i)
        else:
            gaps.append({"field": "maintenance:schedule", "reason": f"p.{i + 1}: grid page without a Schedule 1 / 2 title"})
    for sched, indexes in sorted(by_schedule.items()):
        condition = "SEVERE" if sched == "1" else "NORMAL"
        notes, raw_notes = footnotes([pages[i] for i in indexes])
        for index in indexes:
            page = index + 1
            g = grid(reader, index)
            if "error" in g:
                gaps.append({"field": "maintenance:schedule", "reason": f"p.{page}: {g['error']}"})
                continue
            cols = g["columns"]
            cursor = 0
            for row in g["rows"]:
                label = row["label"]
                full = f"{row['parent']} {label}" if row["parent"] else label
                if full.startswith("*"):
                    continue  # footnotes printed inside the table frame
                span = find_span(flat[index], label, cursor)
                if span is None:
                    if job_of(full):
                        gaps.append({"field": f"maintenance:{job_of(full)}", "reason": f"p.{page}: row '{full[:60]}' not found in the page text"})
                    continue
                text = flat[index][span[0]:span[1]]
                pspan = find_span(flat[index], row["parent"]) if row["parent"] else None
                # the row as the page text prints it (the glyph runs may lack the spaces: "Changeengineoil")
                full = f"{flat[index][pspan[0]:pspan[1]]} {text}" if pspan else (f"{row['parent']} {text}" if row["parent"] else text)
                job = job_of(full)
                if job is None:
                    continue
                cursor = span[1]
                tail = flat[index][span[1]:]
                marks_text = re.match(r"\s*((?:X(?:\*\d+(?:,\s?\*\d+)*)?\s?)+)(?=\s|$)", tail)
                cell = row["cell"]
                quote = text
                if row["marks"] and marks_text and marks_text.group(1).count("X") == len(row["marks"]):
                    quote = f"{text} {marks_text.group(1).strip()}"
                elif cell and norm(f"{text} {cell}") in flat[index]:
                    quote = f"{text} {cell}"
                elif cell and stated(tail[:len(cell) + 15]):
                    m_cell = re.match(r"\s*(.{%d,}?(?:months?|km\)))" % max(1, len(cell) - 25), tail)
                    quote = f"{text} {m_cell.group(1).strip()}" if m_cell else text
                cites = [(quote, page, f"Schedule {sched} p.{page}, row '{full[:80]}'")]
                if pspan:
                    cites.append((flat[index][pspan[0]:pspan[1]], page, f"Schedule {sched} p.{page}, parent row"))
                refs = [x for m in REFS.finditer(full) for x in m.groups() if x]
                ref_notes = {r: notes.get(r) for r in refs}
                if any(n and re.search(r"Periodic maintenance is not required", n) for n in ref_notes.values()):
                    gaps.append({"field": f"maintenance:{job}",
                                 "reason": f"p.{page} schedule {sched}: '{full[:60]}': footnote: {next(n for n in ref_notes.values() if n and 'not required' in n)[:90]}"})
                    continue
                if row["problems"]:
                    gaps.append({"field": f"maintenance:{job}", "reason": f"p.{page} '{full[:60]}': {'; '.join(row['problems'])}; not converted"})
                    continue
                base = {"job": job, "action": mitsu_action(full), "condition": condition, "text": full, "cites": cites, "page": page}
                foot_iv = next(((r, s) for r, n in ref_notes.items() if n for s in [stated(n)] if s and not CONDITIONAL.match(n)), None)
                cell_iv = (stated(cell) or stated(tail[:len(cell) + 15])) if cell else None
                if foot_iv:
                    r, shapes = foot_iv
                    q = foot_quote(raw_notes[r])
                    fpage = next((i + 1 for i in indexes if q in flat[i]), page)
                    base["cites"] = cites + [(q, fpage, f"Schedule {sched} footnote *{r}")]
                    marks_at = ", ".join(f"{cols[c]['miles']:,}" for c in row["marks"])
                    for s in shapes:
                        entries.append({**base, **s, "note": f"interval as stated in footnote *{r}" + (f"; the grid marks {marks_at} miles" if marks_at else "")})
                elif cell_iv:
                    for s in cell_iv:
                        entries.append({**base, **s, "note": None})
                elif row["marks"]:
                    pts = [(cols[c]["miles"], cols[c]["km"], cols[c]["months"]) for c in row["marks"]]
                    shapes = interval_from_points(pts)
                    if shapes is None:
                        gaps.append({"field": f"maintenance:{job}",
                                     "reason": f"p.{page} schedule {sched} '{full[:60]}': marks at {[p[0] for p in pts]} miles do not form a regular interval; not converted"})
                        continue
                    head = f"miles x 1,000 {' '.join(c['head'][0] for c in cols)}"
                    if norm(head) in flat[index]:
                        base["cites"] = cites + [(head, page, f"Schedule {sched} column headings (miles x 1,000)")]
                    months_head = f"months {' '.join(c['head'][2] for c in cols)}"
                    if norm(months_head) in flat[index]:
                        base["cites"] = base["cites"] + [(months_head, page, f"Schedule {sched} column headings (months)")]
                    parts = [f"grid marks at {', '.join(f'{p[0]:,}' for p in pts)} miles"]
                    if len(pts) == 1:
                        parts.append("listed once within the grid's horizon")
                    mark_refs = sorted({x for v in row["notes"].values() for x in v})
                    for r in mark_refs + refs:
                        if notes.get(r) and not stated(notes[r]):
                            parts.append(f"*{r}: {notes[r][:160]}")
                    for s in shapes:
                        entries.append({**base, **s, "note": "; ".join(dict.fromkeys(parts))})
                else:
                    if not any(n and CONDITIONAL.match(n) for n in ref_notes.values()):
                        gaps.append({"field": f"maintenance:{job}", "reason": f"p.{page} schedule {sched} '{full[:60]}': no mark and no stated interval"})
                for r, n in ref_notes.items():
                    if n and CONDITIONAL.match(n):
                        conds = conditional_items(n)
                        if not conds:
                            gaps.append({"field": f"maintenance:{job}", "reason": f"footnote *{r} states a condition but no interval could be read"})
                        for ci in conds:
                            q = foot_quote(raw_notes[r], ci["needle"])
                            fpage = next((i + 1 for i in indexes if q in flat[i]), page)
                            entries.append({**base, "action": ci["action"], "condition": "SEVERE", "occurrence": "EVERY",
                                            "interval": ci["interval"], "operation": ci["operation"],
                                            "note": f"conditional interval of footnote *{r}",
                                            "cites": [(q, fpage, f"Schedule {sched} footnote *{r}"), cites[0]]})


# ---------------------------------------------------------------- point lists (2014)
POINT = re.compile(r"^● (?:(?P<mi>[\d,]+) Miles \((?P<km>[\d,]+) km\)(?: or at (?P<mo>\d+) months)?|(?P<only>\d+) Months)\s*$")
BULLET = "\x86"
SKIP_LINE = re.compile(r"^(?:MILEAGE/|MONTHS|DEALERSHIP|NAME/CODE|Regular Maintenance Schedule|Severe Maintenance Schedule|"
                       r"Regular maintenance schedule|Severe maintenance schedule|Mileage or Time-Whichever occurs first|"
                       r"The content and mileage interval|model\.|Enter Your Original|Month Day Year|Original In-Service Date|\d+$|.*\.book )")


def point_items(doc: dict, pages: list[str], flat: list[str], entries: list, gaps: list):
    start = next((i for i, t in enumerate(pages) if re.match(r"\s*Regular Maintenance Schedule", t)), None)
    if start is None:
        gaps.append({"field": "maintenance:schedule", "reason": "no Regular maintenance schedule found"})
        return
    bullets, footers, headings = [], {}, {}
    condition, point, cur, foot_mode = None, None, None, False
    for index in range(start, len(pages)):
        head = pages[index].lstrip()
        if head.startswith("Regular Maintenance Schedule"):
            condition = "NORMAL"
        elif head.startswith("Severe Maintenance Schedule"):
            condition = "SEVERE"
        else:
            break
        for raw in pages[index].splitlines():
            line = raw.strip()
            line = re.sub(r"^Mileage or Time-Whichever occurs first\s*", "", line)
            if not line:
                continue
            m = POINT.match(line)
            if m:
                point = (num(m.group("mi")), num(m.group("km")), int(m.group("mo")) if m.group("mo") else None) if m.group("mi") else None
                if point:
                    headings.setdefault((condition, point), (line, index + 1))  # the point heading as printed
                cur, foot_mode = None, False
                continue
            if line.startswith(BULLET):
                cur = {"lines": [line[1:].strip()], "page": index + 1, "point": point, "condition": condition}
                bullets.append(cur)
                foot_mode = False
                continue
            if SKIP_LINE.match(line):
                cur = None if line.startswith(("MILEAGE/", "DEALERSHIP")) else cur
                continue
            if line.startswith("*") or foot_mode:
                foot_mode = True
                if cur is not None:
                    cur.setdefault("foot", []).append(line)
                continue
            if cur is not None:
                cur["lines"].append(line)
    # group the bullets by their text (footnote markers "*", "*1" left out)
    listed = defaultdict(list)  # (condition, text) -> [(point, page, text as printed)]
    for obj in bullets:
        text = norm(" ".join(obj["lines"]))
        key = (obj["condition"], re.sub(r"\s*\*\d*(?=\.|$)", "", text))
        if obj.get("foot"):
            footers.setdefault(key, norm(" ".join(obj["foot"])))
        listed[key].append((obj["point"], obj["page"], text))
    for key, pts in listed.items():
        condition, text = key
        job = job_of(text)
        if job is None:
            continue
        timed = [(p, pg, t) for p, pg, t in pts if p]
        if not timed:
            continue
        first_page, first_text = timed[0][1], timed[0][2]
        span = find_span(flat[first_page - 1], first_text)
        quote = flat[first_page - 1][span[0]:span[1]] if span else None
        if not quote:
            gaps.append({"field": f"maintenance:{job}", "reason": f"p.{first_page}: '{text[:60]}' not found in the page text"})
            continue
        section = "Regular" if condition == "NORMAL" else "Severe"
        cites = [(quote, first_page, f"{section} maintenance schedule, first listed at {timed[0][0][0]:,} miles")]
        base = {"job": job, "action": mitsu_action(text), "condition": condition, "text": text, "cites": cites, "page": first_page}
        foot = footers.get(key)
        foot_iv = stated(foot) if foot else None
        if foot_iv:
            fpage = next((pg for _, pg, _ in timed if norm(foot)[:50] in flat[pg - 1]), first_page)
            sentence = foot if norm(foot) in flat[fpage - 1] else None
            if sentence:
                base["cites"] = cites + [(sentence, fpage, f"{section} maintenance schedule footnote")]
            for s in foot_iv:
                entries.append({**base, **s, "note": "interval as stated in the footnote; listed at "
                                + ", ".join(f"{p[0]:,}" for p, _, _ in timed) + " miles"})
            continue
        points = sorted({p for p, _, _ in timed})
        shapes = interval_from_points(points)
        if shapes is None:
            gaps.append({"field": f"maintenance:{job}",
                         "reason": f"{section.lower()} schedule: '{text[:60]}' listed at {[p[0] for p in points]} miles: not a regular interval; not converted"})
            continue
        parts = [f"listed at {', '.join(f'{p[0]:,}' for p in points)} miles"]
        if len(points) == 1:
            parts.append("listed once within the schedule's horizon")
        if foot:
            parts.append(f"footnote: {foot[:160]}")
        heads = []  # the headings of the first two points: the interval as printed
        for point in points[:2]:
            head = headings.get((condition, point))
            if head and norm(head[0]) in flat[head[1] - 1]:
                heads.append((head[0], head[1], f"{section} maintenance schedule, point heading"))
        for s in shapes:
            entries.append({**base, "cites": cites + heads, **s, "note": "; ".join(parts)})


# ---------------------------------------------------------------- build
def build() -> int:
    lines = our_lines(MAKE)
    docs, skipped = documents()
    per_line = defaultdict(lambda: {"sources": {}, "items": [], "gaps": []})
    phev_years = {int(y) for r in read_csv(MANIFEST) + read_csv(SKIPPED) if is_phev(r["title"]) for y in r["years"].split(";") if y}
    covered = defaultdict(set)  # (line, year) -> {"gas", "phev"}
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
        entries, gaps = [], []
        if any("miles x 1,000" in t for t in pages):
            grid_items(doc, pages, flat, entries, gaps)
        else:
            point_items(doc, pages, flat, entries, gaps)
        for ln in targets:
            gens = generations_of(MAKE, ln)
            scope = f"{MAKE}/{ln} MY{'-'.join(map(str, doc['years']))} ({doc['key']})"
            for g in gaps:
                per_line[ln]["gaps"].append({"scope": scope, **g})
            kept = []
            for e in entries:
                reason = excluded_for(ln, e["text"])
                if reason is None:
                    kept.append(e)
            if not kept:
                per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:schedule", "reason": "no schedule item for this line"})
                continue
            used_pages = {c[1] for e in kept for c in e["cites"]}
            per_line[ln]["sources"][doc["key"]] = pdf_source(
                doc["key"], doc["path"], doc["sha256"], doc["url"], doc["title"], PUBLISHER, REGISTRY, doc["years"], used_pages,
                doc["retrieved_at"])
            for year in doc["years"]:
                gen = gen_for(gens, year)
                if gen is None:
                    per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:schedule", "reason": f"no generation for MY{year}"})
                    continue
                covered[(ln, year)].add("phev" if doc["phev"] else "gas")
                for e in kept:
                    app = applicability(e["text"])
                    if e.get("operation"):
                        app["operation"] = e["operation"]
                    if ln == "outlander" and doc["phev"]:
                        app["edition"] = "Outlander PHEV"
                    elif ln == "outlander" and year in phev_years:
                        app["edition"] = "Outlander"
                    quote, page, locator = e["cites"][0]
                    it = item(ln, gen, year, e["job"], e["action"], condition=e["condition"], occurrence=e["occurrence"],
                              interval=e["interval"], applicability=app, note=e["note"], source=doc["key"], quote=quote,
                              page=page, locator=locator)
                    for q, p, loc in e["cites"][1:]:
                        it["cites"].append({"source": doc["key"], "quote": norm(q), "pages": [p], "locator": loc})
                    per_line[ln]["items"].append(it)
    # model years without a booklet on disk
    for ln, line in lines.items():
        for year in range(line.years[0], line.years[1] + 1):
            wanted = ["gas"] + (["phev"] if ln == "outlander" and year in phev_years else [])
            for kind in wanted:
                if kind in covered[(ln, year)]:
                    continue
                listed = [r for r in skipped if ln in r["lines"].split(";") and str(year) in r["years"].split(";")
                          and (is_phev(r["title"]) == (kind == "phev"))]
                what = "Outlander PHEV" if kind == "phev" else ("Outlander (gasoline)" if ln == "outlander" else "Outlander Sport")
                reason = ("no US booklet on disk (salesforce copies disallowed by robots.txt)" if listed
                          else "no US booklet on disk (none listed in the manifests)")
                per_line[ln]["gaps"].append({"scope": f"{MAKE}/{ln} MY{year}", "field": f"maintenance:schedule ({what})", "reason": reason})
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
        print(f"{MAKE}/{ln}: items {len(items)}, years {years}, sources {len(data['sources'])}, gaps {len(gaps)} "
              f"-> {out.relative_to(WORK.parent)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(build())

"""Ford Fusion maintenance schedules from the factory owner's manuals, chapter "Scheduled
Maintenance" (copies hosted by carmans.net: the Ford owner portal refuses scripted clients, see
manifest_official/www.fordservicecontent.com.csv, status skipped).

Every manual (2014-2020, Fusion and Fusion Hybrid / Energi editions) prints:
  - the Intelligent Oil-Life Monitor ("Never exceed one year or 10000 miles (16000 kilometers)
    between oil change intervals"; hybrid editions also print an "Oil Change Indicator" with its
    own limit): OIL_LIFE_MONITOR items with the stated maximum, no distance invented;
  - "Normal Maintenance Intervals - At every oil change interval as indicated by the information
    display" (tire rotation, inspections): OIL_LIFE_MONITOR items with the table footnote limit
    ("Do not exceed one year or 10000 miles (16000 kilometers) between service intervals");
  - "Other maintenance items": two-column table, interval cell (left) for one or several items
    (right), footnotes ("Initial replacement at six years or 100000 miles (160000 kilometers),
    then every three years or 50000 miles (80000 kilometers)" -> FIRST + SUBSEQUENT);
  - "Brake Fluid Maintenance" (2020): "Every 3 Years";
  - "Special Operating Conditions Scheduled Maintenance": one table per condition (towing,
    extensive idling, dusty roads ...): SEVERE items with {"operating_condition": <title>}.
The page text interleaves the two columns of a table, so the cells are rebuilt from the glyph
positions (pdf_geometry.py): an interval cell is top-aligned with its first item and covers the
items down to the next cell. km as printed ("(32000 km)", "(160000 kilometers)").

Documents: carmans.net copies of the factory manuals (tier B, OWNER_MANUAL_COPY, REVIEWED_MIRROR,
display SECONDARY_NOTE), only editions whose extracted market is US.
Output: data_work/ford/staging/fusion/maintenance_owner_manual.json (maintenance_common).

  .venv/Scripts/python.exe scripts/build_maintenance_ford.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maintenance_common import (  # noqa: E402
    JOBS, action_of, gen_for, generations_of, item, merge_years, norm, our_lines, page_text, pdf_source, write,
)
from pdf_geometry import page_hrules, page_runs  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

MAKE = "ford"
REGISTRY = "factory-ford-us"
NAME = "owner_manual"
CARMANS_MANIFEST = WORK / "_shared" / "manifest_carmans.csv"
NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "ten": 10}
FORD_JOBS = [
    ("tire_rotation", r"^Rotate (?:the )?tires"),
    ("engine_oil_and_filter", r"engine oil filter|engine oil and (?:the )?filter|^Change engine oil"),
    ("manual_transmission_fluid", r"manual transmission fluid"),
    ("engine_coolant", r"engine coolant|engine cooling system"),
    ("accessory_drive_belt", r"accessory drive belt"),
    ("brake_fluid", r"brake fluid"),
]
DIST = re.compile(r"(?P<mi>\d{1,3}(?:,\d{3})+|\d{4,6}) (?:miles|mi)\s*\((?P<km>\d{1,3}(?:,\d{3})+|\d{4,6}) (?:km|kilometers)\)")
TIME = re.compile(r"\b(?P<n>\d{1,2}|one|two|three|four|five|six|seven|eight|ten) (?P<u>years?|months?)\b", re.I)
SKIP_TABLE = re.compile(r"When to [Ee]xpect|Multi-?[Pp]oint [Ii]nspection|Interval|Vehicle [Uu]se", re.I)
OLM_TABLE = re.compile(r"^At [Ee]very [Oo]il [Cc]hange [Ii]nterval", re.I)


def ford_job(text: str) -> str | None:
    for job, pattern in FORD_JOBS + JOBS:
        if re.search(pattern, text, re.I):
            return job
    return None


def number(text: str) -> int:
    return int(text.replace(",", ""))


def months_of(text: str) -> int | None:
    m = TIME.search(text)
    if not m:
        return None
    n = m.group("n").lower()
    n = int(n) if n.isdigit() else NUMBERS[n]
    return n * 12 if m.group("u").lower().startswith("year") else n


def ford_applicability(text: str) -> dict:
    app = {}
    m = re.search(r"\((\d\.\dL)(?: engine)?\)", text, re.I)
    if m:
        app["engine"] = m.group(1)
    if re.search(r"all-wheel drive only", text, re.I):
        app["drive"] = "AWD"
    return app


# ---------------------------------------------------------------- documents
def documents() -> list[dict]:
    docs = []
    with CARMANS_MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if row["make"] != MAKE or row["kind"] != "pdf" or row["status"] != "ok":
            continue
        extracted = WORK / MAKE / "extracted" / f"carmans-{row['post']}.json"
        info = json.loads(extracted.read_text(encoding="utf-8")) if extracted.exists() else {}
        hybrid = "hybrid" in row["post"]
        docs.append({"key": f"carmans-{row['post']}-maintenance", "line": row["line"].split("/")[-1], "years": [int(row["year"])],
                     "title": f"{row['year']} Ford Fusion{' Hybrid / Energi' if hybrid else ''} owner's manual "
                              f"(copy of the factory manual, carmans.net)",
                     "path": RAW_ROOT / row["path"], "url": row["url"], "sha256": row["sha256"], "retrieved_at": row["retrieved_at"],
                     "edition": "Fusion Hybrid / Fusion Energi" if hybrid else "Fusion", "hybrid": hybrid,
                     "market_ok": info.get("status") == "ok" and info.get("edition_market") == "US"})
    return docs


# ---------------------------------------------------------------- tables from glyph positions
def lines_of(runs: list[dict]) -> list[dict]:
    """Body-size runs merged into lines (same baseline, left to right), split at the column gap."""
    body = [r for r in runs if r["size"] >= 6 and r["text"].strip() and not r["rotated"]]
    body.sort(key=lambda r: (-round(r["y"], 0), r["x"]))
    out = []
    for r in body:
        prev = out[-1] if out else None
        # runs of one line follow each other (font changes); a column gap is wider
        if prev and abs(prev["y"] - r["y"]) < 1.5 and r["x"] - prev["x_end"] < 2.5 and r["size"] == prev["size"]:
            # pieces of one word follow each other without a gap (2014 manuals draw glyph clusters)
            gap = r["x"] - prev["x_end"] > 0.15 * r["size"]
            prev["text"] += (" " if gap and not prev["text"].endswith(" ") and not r["text"].startswith(" ") else "") + r["text"]
            prev["x_end"] = r["x_end"]
        else:
            out.append({"x": r["x"], "y": r["y"], "size": r["size"], "text": r["text"], "x_end": r["x_end"]})
    for ln in out:
        ln["text"] = norm(ln["text"])
    return out


def tables_on_page(runs: list[dict]) -> list[dict]:
    lines = lines_of(runs)
    small = [r for r in runs if r["size"] < 6 and r["text"].strip()]
    heads = []
    for ln in (x for x in lines if 6.5 <= x["size"] <= 7.6):  # table titles, one or two lines
        if heads and heads[-1]["bottom"] - ln["y"] < 12:
            heads[-1]["text"] += " " + ln["text"]
            heads[-1]["bottom"] = ln["y"]
        else:
            heads.append({**ln, "bottom": ln["y"]})
    big = [ln for ln in lines if ln["size"] >= 8.6]  # section headings ("Exceptions", "Normal Maintenance Intervals")
    tables = []
    for n, h in enumerate(heads):
        if SKIP_TABLE.search(h["text"]) and not OLM_TABLE.search(h["text"]):
            continue
        below = [x["y"] for x in heads[n + 1:] if x["y"] < h["bottom"] - 1] + [x["y"] for x in big if x["y"] < h["bottom"] - 1]
        bottom = max(below) if below else 25.0
        region = [ln for ln in lines if bottom < ln["y"] < h["bottom"] - 1 and 6 <= ln["size"] < 8.6
                  and not (6.5 <= ln["size"] <= 7.6)]
        if not region:
            continue
        # footnote block: a small marker at the left margin starts each footnote
        marks = sorted((s for s in small if s["x"] < 35 and bottom < s["y"] < h["bottom"]), key=lambda s: -s["y"])
        foot_top = marks[0]["y"] if marks else None
        body = [ln for ln in region if foot_top is None or ln["y"] > foot_top + 2]
        body.sort(key=lambda ln: -ln["y"])
        for k in range(1, len(body)):  # a wide vertical gap ends the table
            if body[k - 1]["y"] - body[k]["y"] > 30:
                body = body[:k]
                break
        foots = {}
        for k, s in enumerate(marks):
            nxt = marks[k + 1]["y"] if k + 1 < len(marks) else -1e9
            block, last = [], None
            for ln in sorted(region, key=lambda ln: -ln["y"]):
                if nxt + 2 < ln["y"] <= s["y"] + 3 and ln["x"] < 35 and (last is None or last - ln["y"] < 12):
                    block.append(ln["text"])
                    last = ln["y"]
            foots[s["text"].strip()] = norm(" ".join(block))
        refs = [s["text"].strip().rstrip(",") for s in small if s["x"] > 100 and -2 < s["y"] - h["y"] < 8]
        tables.append({"title": h["text"], "y": h["y"], "body": body, "foots": foots, "refs": refs, "small": small})
    return tables


def rows_of_table(table: dict, single: bool) -> list[dict]:
    """[{"item", "y", "cell", "refs"}]: items (right column) with their interval cell (left)."""
    body = sorted(table["body"], key=lambda ln: -ln["y"])
    if single:
        lefts, rights = [], body
    else:
        split = 100.0
        lefts = [ln for ln in body if ln["x"] < split]
        rights = [ln for ln in body if ln["x"] >= split]
    # items: a capitalised line starts an item, a lower-case line continues it
    items = []
    for ln in rights:
        if items and (ln["text"][:1].islower() or ln["text"][:1] in "(") and items[-1]["bottom"] - ln["y"] < 12:
            items[-1]["text"] += " " + ln["text"]
            items[-1]["bottom"] = ln["y"]
        else:
            items.append({"text": ln["text"], "top": ln["y"], "bottom": ln["y"]})
    cells = []
    for ln in lefts:
        if cells and cells[-1]["bottom"] - ln["y"] < 11:
            cells[-1]["text"] += " " + ln["text"]
            cells[-1]["bottom"] = ln["y"]
            cells[-1]["lines"].append(ln["text"])
        else:
            cells.append({"text": ln["text"], "top": ln["y"], "bottom": ln["y"], "lines": [ln["text"]]})
    # the row rules drawn across the interval column bound each interval cell; an item belongs to
    # the cell of the band its centre lies in (cells are top-aligned in some tables, centred in others)
    rules = []
    if cells:
        left_x = min(ln["x"] for ln in lefts) + 5
        rules = sorted({round(y, 1) for x0, x1, y in table.get("hrules", []) if x0 <= left_x <= x1}, reverse=True)

    def band(y: float) -> int:
        return sum(1 for r in rules if r > y)

    out = []
    for it in items:
        cell = None
        if rules:
            centre = (it["top"] + it["bottom"]) / 2 + 3
            same = [c for c in cells if band((c["top"] + c["bottom"]) / 2 + 3) == band(centre)]
            cell = same[0] if same else None
        else:
            for c in cells:  # without rules: cells top-aligned with their first item ...
                if c["top"] >= it["top"] - 6:
                    cell = c
            if cell is None:  # ... or centred on a group of items
                below = [c for c in cells if 0 < it["top"] - c["top"] <= 20]
                cell = below[0] if below else None
        refs = [s["text"].strip() for s in table["small"] if s["x"] > 100 and -2 < s["y"] - it["top"] < 8]
        out.append({"item": norm(it["text"]), "y": it["top"], "cell": cell, "refs": refs})
    return out


def interval_of_cell(text: str) -> dict | None:
    m = DIST.search(text)
    months = months_of(text)
    if m:
        return {"occurrence": "FIRST" if re.match(r"\s*At\b", text) else "EVERY", "interval_km": number(m.group("km")),
                "interval_miles_original": number(m.group("mi")), "interval_months": months}
    if months and re.match(r"\s*Every\b", text, re.I):
        return {"occurrence": "EVERY", "interval_km": None, "interval_miles_original": None, "interval_months": months}
    return None


def quote_for(flat_page: str, item_text: str, cell: dict | None) -> list[str]:
    """Quotes as they stand in the page text (the text layer interleaves the two columns)."""
    if cell:
        first = cell["lines"][0]
        for q in (f"{cell['text']} {item_text}", f"{item_text} {cell['text']}", f"{first} {item_text}", f"{item_text} {first}"):
            if norm(q) in flat_page:
                return [q]
        return [q for q in (safe_quote(item_text, flat_page), first if norm(first) in flat_page else None) if q]
    q = safe_quote(item_text, flat_page)
    return [q] if q else []


def build_doc(doc: dict, pages: list[str], flat: list[str], entries: list, gaps: list):
    start = next((i for i, t in enumerate(flat) if i > 20 and "NORMAL SCHEDULED MAINTENANCE" in t), None)
    if start is None:
        gaps.append({"field": "maintenance:schedule", "reason": "chapter Scheduled Maintenance not found"})
        return
    end = next((i for i in range(start, min(start + 8, len(flat))) if re.search(r"\bExceptions\b", flat[i])), start + 5)
    chapter_from = max(start - 4, 0)
    # ---- oil change monitors
    olm = []
    for i in range(chapter_from, end + 1):
        for m in re.finditer(r"Never exceed (?P<t>one|two) years? or (?P<d>[\d,]+ (?:miles|mi) \([\d,]+ (?:kilometers|km)\))\s*between oil change intervals[.,]", flat[i]):
            before = (flat[i - 1] if i else "") + " " + flat[i][:m.start()]
            heads = [(before.rfind(h), h) for h in ("Oil Change Indicator", "Intelligent Oil-Life Monitor")]
            head = max(heads)[1] if max(heads)[0] >= 0 else None
            variants = list(VARIANT.finditer(before))
            d = DIST.search(m.group("d"))
            olm.append({"head": head, "variant": variants[-1].group(0) if variants else None,
                        "max": {"interval_km": number(d.group("km")), "interval_months": NUMBERS[m.group("t")] * 12},
                        "quote": m.group(0).rstrip(","), "page": i + 1})
    if_equipped = re.search(r"Intelligent Oil-Life Monitor \(if equipped\)", " ".join(flat[chapter_from:end + 1]), re.I)
    for o in olm:
        app = {}
        if len(olm) > 1 and doc["hybrid"] and o["variant"] and len({x["variant"] for x in olm}) > 1:
            app = {"variant": variant_name(o["variant"])}
        elif len(olm) > 1 and if_equipped and len({x["head"] for x in olm}) > 1:
            app = {"oil_monitor": "Intelligent Oil-Life Monitor (if equipped)" if o["head"] == "Intelligent Oil-Life Monitor"
                   else "Oil Change Indicator"}
        entries.append({"job": "engine_oil_and_filter", "action": "REPLACE", "condition": "NORMAL", "occurrence": "EVERY",
                        "system": "OIL_LIFE_MONITOR", "interval": None, "max_interval": o["max"], "applicability": app,
                        "note": "oil change when the information display shows the oil change message (Intelligent Oil-Life Monitor)",
                        "cites": [(o["quote"], o["page"], "Scheduled Maintenance: General Maintenance Information (oil change interval)")]})
    if not olm:
        gaps.append({"field": "maintenance:engine_oil_and_filter", "reason": "oil-change limit sentence not found"})
    # ---- tables
    reader = PdfReader(str(doc["path"]))
    severe_from = next((i for i in range(start, end + 1) if "SPECIAL OPERATING CONDITIONS" in flat[i]), end + 1)
    page_tables = {}
    for index in range(start, end + 1):
        runs, rules = page_runs(reader, index), page_hrules(reader, index)
        tables = tables_on_page(runs)
        for t in tables:
            t["hrules"] = rules
        page_tables[index] = (runs, tables)
    # the limit of the oil-change table ("Do not exceed one year or 10000 miles (16000 kilometers) between
    # service intervals") stands under its last page; it holds for the rows of every page of the table
    olm_limit = next(((f, index) for index, (_, tables) in page_tables.items() for t in tables if OLM_TABLE.search(t["title"])
                      for f in t["foots"].values() if re.search(r"Do not exceed .* between service intervals", f)), None)
    for index in range(start, end + 1):
        runs, tables = page_tables[index]
        page = index + 1
        for table in tables:
            title = table["title"]
            single = bool(OLM_TABLE.search(title))
            severe = index > severe_from or (index == severe_from and table["y"] < severe_y(runs))
            rows = rows_of_table(table, single)
            head_foot = olm_limit
            for row in rows:
                text = row["item"]
                job = ford_job(text)
                if job is None:
                    continue
                if re.search(r"as indicated by (?:the )?information display and perform services listed", text, re.I):
                    continue  # severe tables: oil change by the monitor, same as the normal schedule
                action = "ROTATE" if job == "tire_rotation" else action_of(text)
                app = ford_applicability(text)
                cond = "SEVERE" if severe else "NORMAL"
                if severe:
                    app["operating_condition"] = title_case(title)
                prefix = re.match(r"(Fusion (?:full hybrid|Energi plug-in hybrid)):\s*", text, re.I)
                if prefix:
                    app["variant"] = variant_name(prefix.group(1))
                elif doc["hybrid"] and not severe and (single or re.match(r"Normal scheduled maintenance", title, re.I)):
                    # hybrid manuals print two normal schedules (fixed for the full hybrid, by the
                    # oil-life monitor for the Energi); the variant heading names it where printed
                    variant = table_variant(flat[index], title)
                    app.update({"variant": variant} if variant else {"schedule_table": title_case(title)})
                foot = next((table["foots"][r] for r in row["refs"] if r in table["foots"]), None)
                if foot is None and row["refs"] and index + 1 in page_tables:
                    # the table runs over the page break; its footnotes stand under the continuation
                    cont = [t for t in page_tables[index + 1][1] if title_case(t["title"]) == title_case(title)]
                    foot = next((t["foots"][r] for t in cont for r in row["refs"] if r in t["foots"]), None)
                    foot_page = index + 1
                else:
                    foot_page = index
                note = None
                if single:
                    if job == "engine_oil_and_filter" and action == "REPLACE":
                        continue  # the oil change itself: monitor item above
                    mx = None
                    q = safe_quote(text, flat[index])
                    if q is None:
                        gaps.append({"field": f"maintenance:{job}", "reason": f"p.{page}: row text not found in the page text; not used"})
                        continue
                    cites = [(q, page, f"Normal Maintenance Intervals: {title}")]
                    if head_foot:
                        limit, limit_index = head_foot
                        d, t = DIST.search(limit), months_of(limit)
                        mx = {"interval_km": number(d.group("km")) if d else None, "interval_months": t}
                        if norm(limit) in flat[limit_index]:
                            cites.append((limit, limit_index + 1, f"Normal Maintenance Intervals: {title}, footnote"))
                    entries.append({"job": job, "action": action, "condition": cond, "occurrence": "EVERY", "system": "OIL_LIFE_MONITOR",
                                    "interval": None, "max_interval": mx, "applicability": app,
                                    "note": "at every oil change interval as indicated by the information display", "cites": cites})
                    continue
                cell = row["cell"]
                iv = interval_of_cell(cell["text"]) if cell else None
                if iv is None and re.search(r"\bevery\b", text, re.I):  # "Change engine oil and filter every 12 months or ..."
                    iv = interval_of_cell(text[re.search(r"\bevery\b", text, re.I).start():])
                    cell = None
                if iv is None:
                    gaps.append({"field": f"maintenance:{job}", "reason": f"p.{page} '{title}': '{text[:60]}' has no fixed interval"
                                 f" ({cell['text'] if cell else 'no interval cell'})"})
                    continue
                quotes = quote_for(flat[index], text, cell)
                if not quotes:
                    gaps.append({"field": f"maintenance:{job}", "reason": f"p.{page}: row text not found in the page text; not used"})
                    continue
                cites = [(q, page, f"{'Special Operating Conditions' if severe else 'Normal Scheduled Maintenance'}: {title}") for q in quotes]
                plan = [(iv["occurrence"], iv)]
                if foot:
                    first = re.search(r"Initial replacement at (?P<a>.+?), then every (?P<b>.+?)\.", foot)
                    if first:  # the sentence as the page text has it (the glyph runs may split numbers)
                        exact = re.search(r"Initial replacement at (?P<a>[^.]+?), then every (?P<b>[^.]+?)\.", flat[foot_page])
                        first, foot = (exact, exact.group(0)) if exact else (first, foot)
                    if first:
                        a, b = first.group("a"), first.group("b")
                        da, db = DIST.search(a), DIST.search(b)
                        plan = [("FIRST", {"interval_km": number(da.group("km")), "interval_miles_original": number(da.group("mi")),
                                           "interval_months": months_of(a)}),
                                ("SUBSEQUENT", {"interval_km": number(db.group("km")), "interval_miles_original": number(db.group("mi")),
                                                "interval_months": months_of(b)})]
                    elif re.search(r"After initial inspection", foot):
                        plan = [("FIRST", iv)]
                        note = foot
                    else:
                        note = foot
                    if norm(foot) in flat[foot_page]:
                        cites.append((foot, foot_page + 1, f"{title}: footnote"))
                if len(plan) == 2 and plan[1][1]["interval_miles_original"] * 5 < plan[0][1]["interval_miles_original"]:
                    # 2017 Fusion Hybrid: "then every three years or 5,000 mi (8,000 km)" where every other
                    # edition prints 50,000 mi (80,000 km): a misprint is not written
                    gaps.append({"field": f"maintenance:{job}", "reason": f"p.{foot_page + 1}: subsequent interval printed as "
                                 f"{plan[1][1]['interval_miles_original']} mi ({plan[1][1]['interval_km']} km) after a first one of "
                                 f"{plan[0][1]['interval_miles_original']} mi; looks like a misprint, subsequent interval not written"})
                    plan = plan[:1]
                for occurrence, values in plan:
                    interval = {"interval_km": values["interval_km"], "interval_miles_original": values["interval_miles_original"],
                                "interval_months": values["interval_months"], "rule": None}
                    entries.append({"job": job, "action": action, "condition": cond, "occurrence": occurrence,
                                    "interval": interval, "applicability": app, "note": note, "cites": cites})


VARIANT = re.compile(r"Fusion Energi Plug-[il]n Hybrid|Fusion Full Hybrid|Fusion Hybrid(?! \(CC7\)| /)", re.I)


def variant_name(text: str) -> str:
    """"Fusion Energi Plug-ln Hybrid" (text layer) / "Fusion full hybrid" -> one spelling."""
    t = text.lower().replace("plug-ln", "plug-in")
    return "Fusion Energi Plug-in Hybrid" if "energi" in t else "Fusion Full Hybrid" if "full" in t else "Fusion Hybrid"


def table_variant(page_text_: str, title: str) -> str | None:
    """The hybrid variant heading printed just before a table title ("Fusion Energi Plug-in Hybrid")."""
    at = page_text_.lower().find(norm(title)[:30].lower())
    if at < 0:
        return None
    found = list(VARIANT.finditer(page_text_[max(0, at - 120):at]))
    return variant_name(found[-1].group(0)) if found else None


def severe_y(runs: list[dict]) -> float:
    ys = [ln["y"] for ln in lines_of(runs) if "SPECIAL OPERATING" in ln["text"].upper()]
    return max(ys) if ys else -1e9


def title_case(text: str) -> str:
    """Table titles print in sentence case or title case depending on the year: one form."""
    text = norm(text).rstrip(". ")
    return text[:1].upper() + text[1:].lower()


def safe_quote(text: str, flat_page: str) -> str | None:
    """The text itself, or its longest leading part (whole words) found in the page text."""
    words = norm(text).split()
    if " ".join(words) in flat_page:
        return " ".join(words)
    for n in range(len(words) - 1, 3, -1):
        q = " ".join(words[:n])
        if q in flat_page:
            return q
    return None


def build() -> int:
    lines = our_lines(MAKE)
    per_line = defaultdict(lambda: {"sources": {}, "items": [], "gaps": []})
    for doc in documents():
        ln = doc["line"]
        if ln not in lines:
            continue
        line = lines[ln]
        years = [y for y in doc["years"] if line.years[0] <= y <= line.years[1]]
        scope = f"{MAKE}/{ln} MY{'-'.join(map(str, years))} ({doc['key']})"
        if not doc["market_ok"]:
            per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:schedule", "reason": "edition not classified US; not used"})
            continue
        pages = page_text(doc["sha256"])
        flat = [norm(p) for p in pages]
        entries, gaps = [], []
        build_doc(doc, pages, flat, entries, gaps)
        for g in gaps:
            per_line[ln]["gaps"].append({"scope": scope, **g})
        if not entries:
            continue
        used = {c[1] for e in entries for c in e["cites"]}
        per_line[ln]["sources"][doc["key"]] = pdf_source(
            doc["key"], doc["path"], doc["sha256"], doc["url"], doc["title"], "factory owner's manual, copy hosted by carmans.net",
            REGISTRY, years, used, doc["retrieved_at"], source_type="OWNER_MANUAL_COPY", tier="B", authenticity="REVIEWED_MIRROR")
        gens = generations_of(MAKE, ln)
        for year in years:
            gen = gen_for(gens, year)
            if gen is None:
                per_line[ln]["gaps"].append({"scope": scope, "field": "maintenance:schedule", "reason": f"no generation for MY{year}"})
                continue
            for e in entries:
                quote, page, locator = e["cites"][0]
                it = item(ln, gen, year, e["job"], e["action"], condition=e["condition"], occurrence=e["occurrence"],
                          system=e.get("system", "FIXED_INTERVAL"), interval=e["interval"],
                          applicability={"edition": doc["edition"], **e["applicability"]}, note=e["note"],
                          max_interval=e.get("max_interval"), source=doc["key"], quote=quote, page=page, locator=locator,
                          display_level="SECONDARY_NOTE", confidence="MEDIUM")
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

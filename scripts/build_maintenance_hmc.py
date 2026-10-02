"""Structured maintenance items from Hyundai and Kia US owner's manuals (schedule tables).

The manuals print "Normal Maintenance Schedule" as a ruled grid: one column per interval point
(months / miles x 1,000 / km x 1,000, whichever comes first) and one row per item with R
(replace) / I (inspect) marks, or a text cell stating the interval ("At first, replace at
120,000 miles (200,000 km) or 120 months. After that, replace every 24,000 miles ..."). Newer
Hyundai manuals print the grid rotated by 90 degrees; its cells are rebuilt from the character
positions and the grid is transposed. "Maintenance Under Severe Usage Conditions" is a table of
item / operation / interval text / driving conditions.

  marks R at d, 2d, 3d ...      -> EVERY d (miles, km as printed, months)
  first f, then constant step s -> FIRST f + SUBSEQUENT s
  irregular marks               -> not converted (gap entry)
  text cell                      -> the stated interval(s), clause by clause

Engine applicability: the table heading "(Smartstream G1.6 T-GDi)" or the row's engine cell.
An official (tier A) manual wins over a copy (tier B); two documents of the same rank that give
different intervals for one item and year: nothing is written, the conflict is logged.

Output: data_work/<make>/staging/<line>/maintenance.json (same format as build_maintenance.py).

  uv run --no-project --with pdfplumber --with pypdfium2 python scripts/build_maintenance_hmc.py hyundai|kia
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
from build_maintenance import JOBS, from_points  # noqa: E402
from extract_manual_facts import documents, norm  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import BY_KEY  # noqa: E402

SETTINGS = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
EXTRA_JOBS = [
    ("engine_oil_and_filter", r"engine oil and (?:engine )?(?:oil )?filter"),
    ("dct_fluid", r"dual clutch transmission|\bDCT\b"),
    ("tire_rotation", r"rotate tire"),
    ("cabin_air_filter", r"climate control air filter|air conditioning filter"),
]
SCHEDULE_PAGE = re.compile(r"maintenance schedule|severe usage|severe (?:driving )?conditions", re.I)
SEVERE_HEAD = re.compile(r"severe", re.I)
HEADING = re.compile(
    r"(Normal Maintenance Schedule|Maintenance Under Severe Usage Conditions|Severe Maintenance Schedule)"
    r"(?:\s*\((?P<engine>[^()]*\d\.\d[^()]*)\)"
    r"|\s*[-–]\s*(?P<engine2>(?:Non[- ])?Turbo(?: GDI)? Model|[A-Za-z ]{0,20}\d\.\d\s?L?\s?(?:T-?GDI|GDI|MPI|T-?GDi|GDi|MPi)?))?",
    re.I,
)
CLAUSE = re.compile(
    r"(?P<first>at first,?\s*)?(?:(?:thereafter|after that),?\s*)?"
    r"(?:(?P<verb>inspect|replace|change|rotate(?: tires)?|add fuel additives|add)\b[^.,;]*?)?"
    r"\b(?P<kind>every|at)\s+(?P<miles>[\d,]+(?:\.\d+)?)\s*miles"
    r"(?:\s*\((?P<km>[\d,]+)\s*km\))?"
    r"(?:\s*or\s*(?P<time>\d+)\s*(?P<unit>months?|years?))?",
    re.I,
)


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


def cell_text(text) -> str:
    return norm(" ".join((text or "").split()))


def rotated_text(page, bbox) -> str:
    """Text of a cell printed rotated 90 degrees: lines run along y (read bottom to top) and
    follow each other left to right."""
    chars = [c for c in page.crop(bbox).chars if c["text"]]
    if not chars:
        return ""
    chars.sort(key=lambda c: c["x0"])
    lines, cur = [], [chars[0]]
    for c in chars[1:]:
        if abs(c["x0"] - cur[-1]["x0"]) <= 2.5:
            cur.append(c)
        else:
            lines.append(cur)
            cur = [c]
    lines.append(cur)
    return " ".join(" ".join("".join(c["text"] for c in sorted(line, key=lambda c: -c["top"])).split()) for line in lines)


def number(text: str) -> float | None:
    t = (text or "").replace(",", "").strip()
    return float(t) if re.fullmatch(r"\d+(?:\.\d+)?", t) else None


def grid(page, table) -> dict | None:
    """Points (months, miles, km) and per-item marks/text from a normal-schedule table."""
    raw = table.extract()
    flat = " ".join(cell_text(c) for row in raw for c in row if c)
    rotated = "shtnoM" in flat or "000,1×seliM" in flat
    if rotated:
        matrix = [[rotated_text(page, bbox) if bbox else None for bbox in row.cells] for row in table.rows]
        # rotated: rows are interval points (last point first), columns are months/miles/km + items
        found = next(((i, j) for i, r in enumerate(matrix) for j, c in enumerate(r)
                      if c and re.fullmatch(r"months", c, re.I)), None)
        if found is None:
            return None
        head_row, m = found  # months, miles, km in columns m, m+1, m+2; items after them
        head = matrix[head_row]
        point_rows = [r for r in matrix[:head_row] if len(r) > m + 2 and number(r[m]) is not None and number(r[m + 1]) is not None]
        point_rows = point_rows[::-1]
        points = [(number(r[m]), number(r[m + 1]), number(r[m + 2])) for r in point_rows]
        items = []
        for col in range(m + 3, len(head)):
            label = head[col]
            if not label:
                continue
            column = [matrix[i][col] if col < len(matrix[i]) else None for i in range(head_row)]
            text = next((c for c in column if c and len(c) > 3), None)
            marks = [(r[col] if col < len(r) else None) for r in point_rows]
            items.append({"label": label, "engine": None, "text": text, "marks": None if text else marks})
        return {"points": points, "items": items, "rotated": True}
    rows = [[cell_text(c) if c is not None else None for c in r] for r in raw]
    idx = {}
    for i, r in enumerate(rows):
        for j, c in enumerate(r):
            if c and re.fullmatch(r"months", c, re.I):
                idx["months"] = (i, j)
            elif c and re.fullmatch(r"miles\s?[×x]\s?1,?000", c, re.I):
                idx["miles"] = (i, j)
            elif c and re.fullmatch(r"km\s?[×x]\s?1,?000", c, re.I):
                idx["km"] = (i, j)
    if not {"months", "miles"} <= set(idx):
        return None
    start = idx["miles"][1] + 1
    width = max(len(r) for r in rows)
    get = lambda name, k: number(rows[idx[name][0]][k]) if name in idx and k < len(rows[idx[name][0]]) else None  # noqa: E731
    cols = [k for k in range(start, width) if get("miles", k) is not None]
    points = [(get("months", k), get("miles", k), get("km", k)) for k in cols]
    last_head = max(i for i, _ in idx.values())
    items = []
    for r in rows[last_head + 1:]:
        label = r[0]
        if not label:
            continue
        engine = r[1] if len(r) > 1 and r[1] and start > 1 and not re.fullmatch(r"[RI]", r[1]) else None
        cells = [r[k] if k < len(r) else None for k in cols]
        text = next((c for c in cells if c and len(c) > 3), None)
        items.append({"label": label, "engine": engine, "text": text, "marks": None if text else cells})
    return {"points": points, "items": items, "rotated": False}


def severe_rows(table) -> list[dict]:
    rows = [[cell_text(c) if c is not None else None for c in r] for r in table.extract()]
    out, carried = [], {}
    for r in rows:
        if not r or not any(r):
            continue
        if r[0] and re.search(r"maintenance item", r[0], re.I):
            continue
        texts = [c for c in r if c]
        interval = next((c for c in texts if re.search(r"every|more frequently|inspect more", c, re.I)), None)
        op = next((c for c in texts if re.fullmatch(r"[RI]", c)), None)
        label = r[0] or carried.get("label")
        if r[0]:
            carried = {"label": r[0]}
        if label and interval:
            out.append({"label": label, "operation": op, "text": interval})
    return out


def clauses(text: str, default_action: str | None) -> list[dict]:
    """Stated intervals of a text cell, in order: [{occurrence, action, miles, km, months}]."""
    out = []
    for m in CLAUSE.finditer(text):
        verb = (m.group("verb") or "").lower()
        action = ("ROTATE" if verb.startswith("rotate") else "INSPECT" if verb == "inspect"
                  else "REPLACE" if verb in ("replace", "change") else None if verb else default_action)
        if action is None:
            continue  # fuel additives: not a service item
        miles = float(m.group("miles").replace(",", ""))
        months = None
        if m.group("time"):
            months = int(m.group("time")) * (12 if m.group("unit").lower().startswith("year") else 1)
        first = bool(m.group("first")) or m.group("kind").lower() == "at"
        subsequent = re.match(r"\s*(?:thereafter|after that)", text[m.start():], re.I) is not None
        out.append({"occurrence": "FIRST" if first else "SUBSEQUENT" if subsequent else "EVERY", "action": action,
                    "miles": miles, "km": int(m.group("km").replace(",", "")) if m.group("km") else None,
                    "months": months, "quote": m.group(0)})
    return out


def shape(values: list[float]) -> list[tuple[str, float]] | None:
    found = from_points([int(round(v * 10)) for v in values])
    if found is None:
        return None
    return [(s["occurrence"], s["miles"] / 10) for s in found]


def mark_entries(item: dict, points: list[tuple]) -> tuple[list[dict], str | None]:
    out, problem = [], None
    for mark, action in (("R", "REPLACE"), ("I", "INSPECT")):
        idx = [i for i, m in enumerate(item["marks"]) if m and mark in m.replace(" ", "")]
        if not idx or any(points[i][1] is None or points[i][0] is None for i in idx):
            continue
        miles = shape([points[i][1] for i in idx])
        months = shape([points[i][0] for i in idx])
        km = shape([points[i][2] for i in idx]) if all(points[i][2] is not None for i in idx) else None
        if miles is None or months is None or [o for o, _ in miles] != [o for o, _ in months]:
            problem = f"irregular {mark} marks at {[points[i][1] for i in idx]} x1,000 miles"
            continue
        for n, (occurrence, step) in enumerate(miles):
            out.append({"occurrence": occurrence, "action": action, "miles": step * 1000,
                        "km": int(km[n][1] * 1000) if km else None, "months": int(months[n][1]),
                        "quote": item["label"]})
    return out, problem


# ---- list format (older Kia manuals): "7,500 miles (12,000 km) or 6 months ❑ Inspect ... ❑ Replace ..."
POINT = re.compile(
    r"(?<![\(\d,.])(?<!Every )(?<!every )(\d{1,3}(?:,\d{3})+|\d+(?:\.\d)?)\s*miles\s*\((\d{1,3}(?:,\d{3})*)\s*km\)\s*or\s*(\d+)\s*months"
)
ITEM_INTERVAL = re.compile(
    r"\((Every\s+)?(\d{1,3}(?:,\d{3})+|\d+)\s*miles\s*\((\d{1,3}(?:,\d{3})*)\s*km\)(?:\s*or\s*(\d+)\s*months)?\)", re.I
)
ITEM_ENGINE = re.compile(r"\((\d\.\d[^()]*?)\)|-\s*((?:Turbo|Non[- ]Turbo)[^()❑]*?GDI)\b", re.I)
FOOTNOTE = re.compile(
    r"\*\d+\s*([A-Za-z][A-Za-z ,/&]{3,40}?)\s*\((\d\.\d[^()]*)\)\s*((?:Replace|Inspect|Change)\s+every\s+[^*❈]+?)(?=\*\d|❈|$)", re.I
)


def list_points(text: str) -> list[dict]:
    """(job label, engine, action, miles, km, months, explicit-every) for every bullet of every
    mileage block on a page."""
    flat = " ".join(text.split())
    marks = list(POINT.finditer(flat))
    out = []
    for n, m in enumerate(marks):
        block = flat[m.end(): marks[n + 1].start() if n + 1 < len(marks) else len(flat)]
        point = (int(m.group(1).replace(",", "").split(".")[0]) if "." not in m.group(1) else float(m.group(1)),
                 int(m.group(2).replace(",", "")), int(m.group(3)))
        for bullet in block.split("❑")[1:]:
            bullet = re.split(r"\s(?:\*\d+\s+[A-Z]|❈|The following|Keep receipts)", bullet)[0].strip()
            verb = re.match(r"(Inspect|Replace|Rotate|Change|Add)\b", bullet, re.I)
            if not verb:
                continue
            action = {"inspect": "INSPECT", "replace": "REPLACE", "change": "REPLACE", "rotate": "ROTATE"}.get(verb.group(1).lower())
            if action is None:
                continue
            engine = ITEM_ENGINE.search(bullet)
            engine = norm(engine.group(1) or engine.group(2)) if engine else None
            own = ITEM_INTERVAL.search(bullet)
            if own:
                miles, km = int(own.group(2).replace(",", "")), int(own.group(3).replace(",", ""))
                months = int(own.group(4)) if own.group(4) else None
                out.append({"label": bullet, "engine": engine, "action": action, "miles": miles, "km": km,
                            "months": months, "every": bool(own.group(1)), "quote": norm(bullet)})
            else:
                out.append({"label": bullet, "engine": engine, "action": action, "miles": point[0], "km": point[1],
                            "months": point[2], "every": False, "quote": norm(bullet)})
    return out


def page_text(sha: str) -> list[str]:
    with gzip.open(RAW_ROOT / "pagetext" / f"{sha}.json.gz", "rt", encoding="utf-8") as handle:
        return json.load(handle)["pages"]


def build(make: str) -> int:
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
            last_head = (False, None)
            listed = []
            def record(label, row_engine, entry, condition, index, engine_head):
                job = job_of(label)
                if not job:
                    return
                quote = entry["quote"]
                if norm(quote) not in flat_pages[index] and norm(label) not in flat_pages[index]:
                    gaps.append({"scope": f"{line_key} {doc['key']} p.{index + 1}", "field": f"maintenance {job}",
                                 "reason": "quote not found in the page text; not used"})
                    return
                if norm(quote) not in flat_pages[index]:
                    quote = label
                in_label = ITEM_ENGINE.search(label)
                engine = row_engine or (norm(in_label.group(1) or in_label.group(2)) if in_label else None) or engine_head
                applicability = {"edition": edition_of(doc, make), **({"engine": engine} if engine else {})}
                km = entry["km"] or None
                if km is None:
                    from build_maintenance import miles_to_km
                    km = miles_to_km(int(entry["miles"]))
                item = {"job": job, "action": entry["action"], "condition": condition,
                        "schedule_system": "FIXED_INTERVAL", "occurrence": entry["occurrence"],
                        "interval_km": km, "interval_months": entry["months"],
                        "interval_miles_original": int(entry["miles"]),
                        "rule": "WHICHEVER_FIRST" if entry["months"] else None, "note": None}
                cite = {"source": doc["key"], "quote": norm(quote), "pages": [index + 1],
                        "locator": f"page {index + 1}: {label[:80]}"}
                for year in doc["years"]:
                    gen = next((g["code"] for g in gens if g["start_year"] <= year <= g["end_year"]), None)
                    if gen is None or not (line.years[0] <= year <= line.years[1]):
                        continue
                    scope = json.dumps([gen, job, entry["action"], condition, entry["occurrence"], applicability], sort_keys=True)
                    observed[scope][year].append((item, cite, doc["tier"]))
                    used_pages.add(index + 1)
            with pdfplumber.open(doc["path"]) as pdf:
                for index in candidates:
                    page = pdf.pages[index]
                    # the heading can sit anywhere in the extracted text (after the footnotes);
                    # a continuation page without one keeps the previous table's heading
                    head = HEADING.search(" ".join(texts[index].split()))
                    if head:
                        named = head.group("engine") or head.group("engine2")
                        last_head = (bool(SEVERE_HEAD.search(head.group(1))), norm(named) if named else None)
                    severe, engine_head = last_head
                    try:
                        tables = page.find_tables(SETTINGS)
                    except Exception:  # noqa: BLE001 - a damaged page must not stop the document
                        continue
                    entries = []  # (label, engine, entry, condition)
                    tables_used = False
                    for table in tables:
                        if severe:
                            for row in severe_rows(table):
                                default = {"R": "REPLACE", "I": "INSPECT"}.get(row["operation"])
                                for c in clauses(row["text"], default):
                                    if c["action"] in ("REPLACE", "INSPECT") and default and c["action"] != default:
                                        continue
                                    entries.append((row["label"], None, c, "SEVERE"))
                            continue
                        g = grid(page, table)
                        if not g:
                            continue
                        tables_used = True
                        for item in g["items"]:
                            if item["text"]:
                                found = clauses(item["text"], None)
                                if not found and job_of(item["label"]):
                                    gaps.append({"scope": f"{line_key} {doc['key']} p.{index + 1}", "field": f"maintenance {job_of(item['label'])}",
                                                 "reason": f"interval text not understood: {item['text'][:120]}"})
                                entries += [(item["label"], item["engine"], c, "NORMAL") for c in found]
                            elif item["marks"]:
                                found, problem = mark_entries(item, g["points"])
                                if problem and job_of(item["label"]):
                                    gaps.append({"scope": f"{line_key} {doc['key']} p.{index + 1}", "field": f"maintenance {job_of(item['label'])}",
                                                 "reason": problem})
                                entries += [(item["label"], item["engine"], c, "NORMAL") for c in found]
                    for label, row_engine, entry, condition in entries:
                        record(label, row_engine, entry, condition, index, engine_head)
                    if not tables_used and not severe and "\u2751" in texts[index]:
                        for it in list_points(texts[index]):
                            listed.append((it, index, engine_head))
                        for f in FOOTNOTE.finditer(" ".join(texts[index].split())):
                            for c in clauses(f.group(3), None):
                                record(f.group(1), norm(f.group(2)), c, "NORMAL", index, None)
            # list format: the mileage points where each bullet appears give the interval
            grouped = defaultdict(list)
            for it, index, engine_head in listed:
                grouped[(job_of(it["label"]), it["action"], it["engine"] or engine_head)].append((it, index))
            for (job, action, engine), rows in grouped.items():
                if not job:
                    continue
                every = {(it["miles"], it["km"], it["months"]): (it, index) for it, index in rows if it["every"]}
                for (miles, km, months), (it, index) in every.items():
                    record(it["label"], engine, {"occurrence": "EVERY", "action": action, "miles": miles, "km": km,
                                                 "months": months, "quote": it["quote"]}, "NORMAL", index, None)
                points = sorted({(it["miles"], it["km"], it["months"]): (it, index) for it, index in rows if not it["every"]}.items())
                if not points:
                    continue
                miles = shape([pt[0] / 1000 for pt, _ in points])
                months = shape([pt[2] for pt, _ in points])
                km = shape([pt[1] / 1000 for pt, _ in points])
                first_it, first_index = points[0][1]
                if miles is None or months is None or km is None or [o for o, _ in miles] != [o for o, _ in months]:
                    gaps.append({"scope": f"{line_key} {doc['key']}", "field": f"maintenance {job}",
                                 "reason": f"irregular list points {[pt[0] for pt, _ in points]} miles; not converted"})
                    continue
                for n, (occurrence, step) in enumerate(miles):
                    record(first_it["label"], engine, {"occurrence": occurrence, "action": action, "miles": step * 1000,
                                                       "km": int(km[n][1] * 1000), "months": int(months[n][1]),
                                                       "quote": first_it["quote"]}, "NORMAL", first_index, None)
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
                    chosen[scope][year] = (item_json, [c for c, _ in cites])
                    continue
                ranked = sorted(variants.items(), key=lambda kv: (min(t for _, t in kv[1]), -len(kv[1])))
                best = min(t for _, t in ranked[0][1])
                leaders = [kv for kv in ranked if min(t for _, t in kv[1]) == best]
                gen, job, action, condition, occurrence, applicability = json.loads(scope)
                if len(leaders) == 1:
                    chosen[scope][year] = (ranked[0][0], [c for c, _ in ranked[0][1]])
                    resolution = "official manual kept over the copy"
                else:
                    resolution = "documents of the same rank disagree; item not written"
                conflicts.append({"scope": f"{line_key} {gen} MY{year}", "key": f"maintenance {job} {action} {condition} {occurrence}",
                                  "applicability": applicability,
                                  "values": [{k: json.loads(v)[k] for k in ("interval_km", "interval_months", "interval_miles_original")}
                                             for v, _ in ranked],
                                  "sources": [sorted({c["source"] for c, _ in cs}) for _, cs in ranked],
                                  "resolution": resolution})
        items = []
        for scope, by_year in chosen.items():
            gen, job, action, condition, occurrence, applicability = json.loads(scope)
            runs = []
            for year in sorted(by_year):
                item_json, cites = by_year[year]
                if runs and runs[-1]["item"] == item_json and runs[-1]["years"][-1] == year - 1:
                    runs[-1]["years"].append(year)
                    runs[-1]["cites"] += cites
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
        out = WORK / make / "staging" / line.slug / "maintenance.json"
        out.write_text(json.dumps({"sources": sources, "items": items, "gaps": gaps, "conflicts": conflicts},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(line_key, "items", len(items), "sources", len(sources), "gaps", len(gaps), "conflicts", len(conflicts), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(build(sys.argv[1]))

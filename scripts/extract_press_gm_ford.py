"""Facts from the stored GM / Ford US press specification pages (collect_press_gm_ford.py).

Input: the host manifests data_work/_shared/manifest_press/<host>.csv, rows with
doc_type=press_specifications and status=ok, their raw pages under RAW_ROOT and the page text
RAW_ROOT/pagetext/<sha256>.json.gz. Output: one JSON per document and line-year,
data_work/<make>/extracted/press-<host-short>-<line-slug>-<year>-<sha8>.json, in the format of
data_work/_shared/press/FORMAT.md.

How a GM article's specification section is read (all from the page's own markup):
  * a section starts at a stand-alone heading paragraph ("2025 Escalade/Escalade ESV
    Specifications (North America)", or "SPECIFICATIONS" with line/year from the article title)
    and runs to the next such heading; the bold paragraph before each table is its group title
    (ENGINE, TRANSMISSION & AXLE, CHASSIS & SUSPENSION, EXTERIOR DIMENSIONS ...);
  * tables are label/value rows ("Wheelbase (in / mm):" | "120.9 / 3071"), tables whose first
    row holds model columns ("" | "ESCALADE" | "ESCALADE ESV"), or label-less value tables
    (fuel capacity) that take the group title as label;
  * "imperial / metric" pairs take the number in the unit the label names first or second
    ("(cu in / cc)" -> cc is the second); several values in one cell are split at their
    published qualifiers ("(6.2L 2WD)", "– Escalade-V", "Front:", "LT ...") which go into
    engine_text; a cell with several values and a missing qualifier goes to review.
Every quote is the label and value cells of the row as they appear in the page text (cells
are tab-separated there, so whitespace-normalised quotes match); a fact whose quote is not
found is moved to review. Units are not converted.

Usage:
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/extract_press_gm_ford.py [--check 5]
  (--check N re-reads the written JSONs, verifies every quote against the page text and prints
   N random facts with the page-text line they come from)
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))

from collect_press_gm_ford import (  # noqa: E402
    FIELDS,
    MANIFEST_DIR,
    clean,
    heading_targets,
    page_title,
    prepare,
    spec_headings,
)
from us_tech_common import RAW_ROOT, WORK, Manifest, read_maybe_gz  # noqa: E402
from us_tech_lines import BY_KEY  # noqa: E402

EXTRACTOR = "press-gm-ford-1"
HOSTS = {
    "news.gm.com": {"short": "newsgm", "publisher": "General Motors US Newsroom (news.gm.com)"},
}
NUM = r"\d[\d,]*(?:\.\d+)?"
PAIR = re.compile(rf"({NUM})\s*/\s*({NUM})")
TIRE = re.compile(r"\b(?:P|LT)?\d{3}/\d{2}\s?Z?R\s?\d{2}(?:\.\d)?[A-Z]{0,3}\b(?:\s\d{2,3}[A-Z]{1,2}\b)?")
WHEEL = re.compile(r"\b(\d{2}(?:\.\d)?)\s*-?\s*(?:in\b\.?|inch(?:es)?\b|\")")
GAL = re.compile(rf"({NUM})\s*gal\b\.?")
UNITS = {
    "in": {"in", "inches", "inch"},
    "lb": {"lb", "lbs"},
    "cuft": {"cu ft", "cu-ft", "cubic feet"},
    "ft": {"ft", "feet"},
    "cc": {"cc", "cm3"},
    "hp": {"hp"},
    "lbft": {"lb-ft", "lb ft", "lbft"},
}
IGNORED = re.compile(
    r"head ?room|leg ?room|shoulder ?room|hip ?room|payload|mpg|final drive|gear ratio|block|cylinder head|"
    r"recommended fuel|engine speed|boost|forced induction|steering ratio|gvwr|axle ratio|emissions|"
    r"^(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|reverse)$|^\d",
    re.I,
)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def number(text: str):
    text = text.replace(",", "")
    return int(text) if re.fullmatch(r"\d+", text) else float(text)


def base_label(label: str) -> str:
    """'Cargo Volume (cu ft / L) 2 :' -> 'cargo volume (cu ft / l)'."""
    text = label.lower().strip()
    text = re.sub(r"\s*\d\s*:?\s*$", "", text) if re.search(r"\)\s*\d\s*:?\s*$", text) else text
    return text.rstrip(": ").strip()


def unit_index(label: str, unit: str) -> int | None:
    """Position (0/1) of `unit` in the label's '(imperial / metric)' unit pair, or None."""
    found = re.search(r"\(([^()]*?)/([^()]*?)\)", label)
    if not found:
        return None
    for i, raw in enumerate(found.groups()):
        text = re.sub(r"@.*", "", raw.lower().replace(".", "")).strip()
        text = re.sub(r"\s+", " ", text)
        if text in UNITS[unit]:
            return i
    return None


def entries(value: str) -> list[tuple[str, str, str]] | None:
    """Split '5807 / 2634 (6.2L 2WD) 6014 / 2728 (6.2L 4WD)' or 'Front: 63.8 / 1620 Rear: 63.9 / 1622'
    into (first, second, qualifier); None when the layout is not one of these two."""
    matches = list(PAIR.finditer(value))
    if not matches:
        return None
    prefix = value[: matches[0].start()].strip()
    if prefix:
        if value[matches[-1].end():].strip():
            return None
        quals = [prefix] + [value[matches[i - 1].end(): matches[i].start()] for i in range(1, len(matches))]
    else:
        quals = [value[m.end(): (matches[i + 1].start() if i + 1 < len(matches) else len(value))]
                 for i, m in enumerate(matches)]
    return [(m.group(1), m.group(2), q.strip().strip(":;,–—-").strip()) for m, q in zip(matches, quals, strict=True)]


def strip_parens(text: str) -> str:
    text = text.strip()
    while text.startswith("(") and text.endswith(")") and text.count("(") == 1:
        text = text[1:-1].strip()
    return text


def qualified_strings(value: str) -> list[tuple[str, str]]:
    """'CVT (FWD) Hydra-Matic 8T45 eight-speed automatic (AWD)' -> [(CVT, FWD), (..., AWD)];
    a value that is not a sequence of 'text (qualifier)' stays whole."""
    if re.fullmatch(r"(?:\s*[^()]+?\s*\([^()]*\))+\s*", value) and value.count("(") > 1:
        return [(norm(text), norm(qual)) for text, qual in re.findall(r"([^()]+?)\s*\(([^()]*)\)", value)]
    return [(value, "")]


class Doc:
    def __init__(self, page_norm: str):
        self.page = page_norm
        self.facts: list[dict] = []
        self.review: list[dict] = []
        self.ignored: Counter = Counter()
        self.unmapped: Counter = Counter()

    def fact(self, key, value, quote, original, row, engine_text):
        quote = norm(quote)
        if quote not in self.page:
            self.review.append({"page": 1, "row": original, "reason": f"quote for {key} not found in page text"})
            return
        self.facts.append({"key": key, "value": value, "page": 1, "quote": quote, "original": norm(original),
                           "engine_text": engine_text or None, "row": row})

    section = ""  # spec heading of the section being read when a page has several

    def rev(self, original, reason):
        if self.section:
            reason = f"{reason} (section '{self.section}')"
        self.review.append({"page": 1, "row": norm(original), "reason": reason})


def join_text(*parts) -> str | None:
    seen = [p for p in dict.fromkeys(parts) if p]
    return " | ".join(seen) or None


def map_cell(doc: Doc, group: str, label: str, value: str, quote: str, original: str, context: str | None,
             engine: str | None) -> None:
    """Map one label/value cell to facts. `context` is the engine_text prefix (column, section),
    `engine` the engine label for engine rows (None on single-engine documents)."""
    lab = base_label(label)
    grp = group.lower()
    if not value or re.fullmatch(r"(?i)not yet available\.?|n/?a|—|-", value):
        if value:
            doc.ignored[lab] += 1
        return

    def pairs(unit: str, key: str, row: str | None = None, keymap=None):
        idx = unit_index(label, unit)
        if idx is None:
            doc.rev(original, f"{key}: unit '{unit}' not named in the label's unit pair")
            return
        parts = entries(value)
        if not parts:
            doc.rev(original, f"{key}: value is not an 'imperial / metric' pair")
            return
        if len(parts) > 1 and not all(q for _, _, q in parts):
            doc.rev(original, f"{key}: several values without a qualifier for each")
            return
        for first, second, qual in parts:
            qual = strip_parens(qual)
            value_num = number((first, second)[idx])
            if keymap is None:  # qualifier = trim / drive / body the value is given for
                doc.fact(key, value_num, quote, original, row or label, join_text(context, qual))
                continue
            target = keymap(qual)  # qualifier = condition (front/rear, behind which row)
            if target is None:
                doc.rev(original, f"{key}: qualifier '{qual}' not understood")
                continue
            doc.fact(target, value_num, quote, original, f"{label} {qual}".strip(), context)

    def strings(key: str, split: bool = False):
        for text, qual in (qualified_strings(value) if split else [(value, "")]):
            doc.fact(key, text, quote, original, label, join_text(context, qual))

    # ---- engine
    if re.match(r"(horsepower|power)\b", lab):
        parts = entries(value)
        if not parts:
            doc.rev(original, "power_hp: value is not 'hp / kW @ rpm'")
            return
        idx = unit_index(label, "hp")
        if idx is None or (len(parts) > 1 and not all(re.search(r"\(([^()]+)\)", q) for _, _, q in parts)):
            doc.rev(original, "power_hp: units or per-value qualifiers missing")
            return
        for first, second, qual in parts:
            rpm = re.match(r"@\s*(\d[\d,]*(?:\s*[-–]\s*\d[\d,]*)?)\s*(?:rpm)?", qual)
            rest = strip_parens(qual[rpm.end():] if rpm else qual)
            etext = join_text(context, engine, rest)
            doc.fact("power_hp", number((first, second)[idx]), quote, original, label, etext)
            if rpm:
                doc.fact("power_rpm", rpm.group(1).strip(), quote, original, label, etext)
        return
    if re.match(r"torque\b", lab):
        parts = entries(value)
        idx = unit_index(label, "lbft")
        if not parts or idx is None or (len(parts) > 1 and not all(re.search(r"\(([^()]+)\)", q) for _, _, q in parts)):
            doc.rev(original, "torque_lb_ft: value/units/qualifiers not readable")
            return
        for first, second, qual in parts:
            rpm = re.match(r"@\s*(\d[\d,]*(?:\s*[-–]\s*\d[\d,]*)?)\s*(?:rpm)?", qual)
            rest = strip_parens(qual[rpm.end():] if rpm else qual)
            etext = join_text(context, engine, rest)
            doc.fact("torque_lb_ft", number((first, second)[idx]), quote, original, label, etext)
            if rpm:
                doc.fact("torque_rpm", rpm.group(1).strip(), quote, original, label, etext)
        return
    if "engine" in grp and lab == "type":
        strings("engine_description", split=True)
        return
    if lab.startswith("displacement"):
        idx = unit_index(label, "cc")
        parts = entries(value)
        if idx is None or not parts or len(parts) > 1:
            doc.rev(original, "engine_displacement_cc: not one 'cu in / cc' pair")
            return
        doc.fact("engine_displacement_cc", number(parts[0][idx]), quote, original, label, join_text(context, engine))
        return
    if lab.startswith("bore"):
        halves = [h.strip() for h in value.split("/")]
        idx_in, idx_mm = unit_index(label, "in"), None
        found = re.search(r"\(([^()]*?)/([^()]*?)\)", label)
        if found and re.sub(r"[.\s]", "", found.group(2).lower()) == "mm":
            idx_mm = 1
        if (len(halves) != 2 or idx_in != 0 or idx_mm != 1
                or not all(re.fullmatch(rf"{NUM}\s*x\s*{NUM}", h) for h in halves)):
            doc.rev(original, "bore/stroke: not 'in x in / mm x mm'")
            return
        doc.fact("bore_stroke_in", halves[0], quote, original, label, join_text(context, engine))
        doc.fact("bore_stroke_mm", halves[1], quote, original, label, join_text(context, engine))
        return
    if lab.startswith("compression ratio"):
        if not re.fullmatch(r"\d+(?:\.\d+)?\s*:\s*1", value):
            doc.rev(original, "compression_ratio: not one 'n:1' value")
            return
        doc.fact("compression_ratio", value, quote, original, label, join_text(context, engine))
        return
    if re.match(r"valve ?train", lab):
        doc.fact("valvetrain", value, quote, original, label, join_text(context, engine))
        return
    if re.match(r"fuel (delivery|system|injection)", lab):
        doc.fact("injection", value, quote, original, label, join_text(context, engine))
        return
    # ---- driveline / chassis
    if lab.startswith("transmission") or (("transmission" in grp) and lab == "type"):
        strings("transmission_description", split=True)
        return
    if re.match(r"front suspension|suspension,? front", lab) or ("suspension" in grp and lab == "front"):
        doc.fact("front_suspension", value, quote, original, label, context)
        return
    if re.match(r"rear suspension|suspension,? rear", lab) or ("suspension" in grp and lab == "rear"):
        doc.fact("rear_suspension", value, quote, original, label, context)
        return
    if re.fullmatch(r"steering( type)?", lab):
        doc.fact("steering", value, quote, original, label, context)
        return
    if re.match(r"tur\w* (circle|diameter)", lab):
        pairs("ft", "turning_circle_ft")
        return
    if re.match(r"front brakes?|brakes?,? front", lab) or ("brake" in grp and lab == "front"):
        doc.fact("front_brakes", value, quote, original, label, context)
        return
    if re.match(r"rear brakes?|brakes?,? rear", lab) or ("brake" in grp and lab == "rear"):
        doc.fact("rear_brakes", value, quote, original, label, context)
        return
    if lab.startswith("brake"):
        doc.rev(original, "brakes: one description for both axles, no front/rear value")
        return
    if re.match(r"wheels?( size)?$", lab):
        for match in WHEEL.finditer(value):
            after = value[match.end():]
            qual = re.match(r"\s*[^()\d]*\(([^()]*)\)", after)
            qual_text = qual.group(1) if qual and not WHEEL.search(qual.group(1)) else ""
            doc.fact("wheel_size_in", number(match.group(1)), quote, original, label, join_text(context, norm(qual_text)))
        if not WHEEL.search(value):
            doc.rev(original, "wheel_size_in: no size in inches")
        return
    if re.match(r"tires?( size)?$", lab):
        for match in TIRE.finditer(value):
            after = value[match.end():]
            qual = re.match(r"\s*[^()\d]*\(([^()]*)\)", after)
            qual_text = qual.group(1) if qual and not WHEEL.search(qual.group(1)) else ""
            doc.fact("tires", match.group(0), quote, original, label, join_text(context, norm(qual_text)))
        if not TIRE.search(value):
            doc.rev(original, "tires: no tire size")
        return
    # ---- dimensions, weights, capacities
    simple = [
        (r"wheelbase", "in", "wheelbase_in"),
        (r"(overall )?length", "in", "length_in"),
        (r"(overall )?width", "in", "width_in"),
        (r"(overall )?height", "in", "height_in"),
        (r"(minimum )?ground clearance", "in", "ground_clearance_in"),
        (r"curb weight", "lb", "curb_weight_lb"),
        (r"(epa )?passenger volume", "cuft", "passenger_volume_cu_ft"),
        (r"(max(imum)? )?(trailering|towing)( capacity)?", "lb", "towing_lb"),
    ]
    for pattern, unit, key in simple:
        if re.match(pattern + r"\b", lab):
            pairs(unit, key)
            return
    if lab.startswith("track"):
        def side(qual: str):
            if re.search(r"(?i)\bfront\b", qual) or "front" in lab:
                return "track_front_in"
            if re.search(r"(?i)\brear\b", qual) or "rear" in lab:
                return "track_rear_in"
            return None
        pairs("in", "track", keymap=side)
        return
    if lab.startswith("cargo"):
        def cargo(qual: str):
            q = qual.lower()
            if re.search(r"behind (the )?first row|folded|maximum|max\b", q):
                return "cargo_max_cu_ft"
            if re.search(r"behind (the )?(second|third|rear) (row|seat)|seats? up|behind rear seat", q):
                return "cargo_cu_ft"
            return None
        pairs("cuft", "cargo", keymap=cargo)
        return
    if re.match(r"fuel (tank )?capacity|fuel tank", lab):
        found = list(GAL.finditer(value))
        if not found:
            doc.rev(original, "fuel_tank_gal: no gallons value")
            return
        quals = []
        for i, match in enumerate(found):
            tail = value[match.end(): (found[i + 1].start() if i + 1 < len(found) else len(value))]
            tail = re.sub(rf"^\s*/?\s*\(?\s*{NUM}\s*(?:L|liters|litres)\b\.?\s*\)?", "", tail)
            quals.append(strip_parens(tail.strip().strip(";,–—-")))
        if len(found) > 1 and not all(quals):
            doc.rev(original, "fuel_tank_gal: several values without a qualifier for each")
            return
        for match, qual in zip(found, quals, strict=True):
            doc.fact("fuel_tank_gal", number(match.group(1)), quote, original, label, join_text(context, qual))
        return
    if lab.startswith("seating"):
        if re.fullmatch(r"\d+", value):
            doc.fact("seats", int(value), quote, original, label, context)
        else:
            doc.rev(original, "seats: not one total seating number")
        return
    if IGNORED.search(lab):
        doc.ignored[lab] += 1
        return
    doc.unmapped[lab] += 1


def table_rows(table) -> list[list[str]]:
    rows = []
    for tr in table.find_all("tr"):
        if tr.find_parent("table") is not table:
            continue
        cells = [clean(cell.get_text()) for cell in tr.find_all(["td", "th"], recursive=False)]
        if any(cells):
            rows.append(cells)
    return rows


def sections(soup, headings) -> list[dict]:
    """[{heading, groups: [(group title, rows)]}] for each spec heading, in document order."""
    out = []
    heading_set = set(map(id, headings))
    for i, block in enumerate(headings):
        section = {"heading": clean(block.get_text(" ")), "tables": []}
        group = ""
        stop = headings[i + 1] if i + 1 < len(headings) else None
        for element in block.next_elements:
            if element is stop:
                break
            name = getattr(element, "name", None)
            if name is None or id(element) in heading_set:
                continue
            if name in ("b", "strong", "h2", "h3", "h4", "h5", "h6") and not element.find_parent("table"):
                text = clean(element.get_text(" "))
                if text:
                    group = text
            elif name == "table" and not element.find_parent("table"):
                section["tables"].append((group, table_rows(element)))
        out.append(section)
    return out


def section_label(heading: str) -> str:
    """'2025 Escalade-V/Escalade-V ESV Specifications (North America)' -> 'Escalade-V/Escalade-V ESV'."""
    found = re.match(r"^(?:(?:19|20)\d\d\s+)?(.*?)\s*\b(?:Specifications?|Specs)\b", heading, re.I)
    return found.group(1).strip() if found and found.group(1).strip() else ""


def engine_labels(section: dict) -> list[str]:
    labels = []
    for group, rows in section["tables"]:
        if "engine" not in group.lower():
            continue
        for row in rows:
            if len(row) >= 2 and row[0] and not row[0].endswith(":") and not any(row[1:]):
                labels.append(row[0])
            elif len(row) == 2 and base_label(row[0]) == "type" and row[1]:
                labels.append(row[1])
    return labels


def read_section(doc: Doc, section: dict, multi_section: bool, multi_engine: bool) -> None:
    label_sec = section_label(section["heading"]) if multi_section else ""
    doc.section = section["heading"] if multi_section else ""
    for group, rows in section["tables"]:
        if not rows:
            continue
        engine = None
        width = max(len(r) for r in rows)
        head = rows[0]
        if len(head) >= 3 and head[0] == "" and all(head[1:]) and not any(c.endswith(":") for c in head[1:]):
            columns = head[1:]
            for row in rows[1:]:
                if len(row) != len(head):
                    doc.rev(" ".join(row), "row width differs from the model header row")
                    continue
                quote = " ".join(row)
                for column, value in zip(columns, row[1:], strict=True):
                    map_cell(doc, group, row[0], value, quote, f"{row[0]} {value}", column, None)
            continue
        if (len(rows) == 2 and len(head) == len(rows[1]) >= 2 and all(head)
                and not any(c.endswith(":") for c in head + rows[1])):
            quote = " ".join(rows[1])
            for column, value in zip(head, rows[1], strict=True):
                map_cell(doc, group, group, value, quote, value, column, None)
            continue
        if width == 1:
            for row in rows:
                map_cell(doc, group, group, row[0], row[0], row[0], label_sec or None, None)
            continue
        for row in rows:
            if len(row) != 2:
                doc.rev(" ".join(row), f"unexpected {len(row)}-cell row in a label/value table")
                continue
            label, value = row
            if not value:
                if "engine" in group.lower() and label and not label.endswith(":"):
                    engine = label
                    doc.fact("engine_description", label, label, label, group, label_sec or None)
                continue
            if "engine" in group.lower() and base_label(label) == "type":
                engine = value
            context = label_sec or None
            map_cell(doc, group, label, value, f"{label} {value}", f"{label} {value}", context,
                     engine if multi_engine else None)


def extract(host: str, row: dict) -> list[tuple[Path, dict]]:
    info = HOSTS[host]
    raw = RAW_ROOT / row["path"]
    body = read_maybe_gz(raw)
    text_file = RAW_ROOT / "pagetext" / f"{row['sha256']}.json.gz"
    pages = json.loads(gzip.open(text_file, "rb").read())["pages"]
    page_norm = norm(pages[0])
    title = page_title(BeautifulSoup(body, "html.parser"))
    soup = prepare(BeautifulSoup(body, "html.parser"))
    headings = spec_headings(soup)
    keys = [k for k in row["line"].split(";") if k]
    lines = {k: BY_KEY[k] for k in keys}
    targets: dict[tuple[str, int], list] = {}
    all_sections = sections(soup, headings)
    for section in all_sections:
        for key, year, _ in heading_targets(section["heading"], title, keys, lines):
            targets.setdefault((key, year), []).append(section)
    outputs = []
    for (key, year), chosen in sorted(targets.items()):
        doc = Doc(page_norm)
        multi_section = len(chosen) > 1
        engines = {e for s in chosen for e in engine_labels(s)}
        for section in chosen:
            read_section(doc, section, multi_section, len(engines) > 1)
        line = BY_KEY[key]
        codes = sorted({c for e in engines for c in re.findall(r"\(([A-Z][A-Z0-9]{2})\)", e)})
        doc_key = f"press-{info['short']}-{line.slug}-{year}-{row['sha256'][:8]}"
        payload = {
            "doc": {
                "key": doc_key, "make": line.make, "lines": [key], "years": [year],
                "doc_type": "press_specifications", "title": title, "path": str(raw), "url": row["url"],
                "page_url": "", "sha256": row["sha256"], "retrieved_at": row["retrieved_at"], "tier": "A",
                "source_type": "PRESS_RELEASE", "publisher": info["publisher"],
                "authenticity": "OFFICIAL_PUBLISHER",
            },
            "extractor": EXTRACTOR,
            "pages": 1,
            "edition_market": "US",
            "status": "ok" if doc.facts else "no_facts",
            "engine_codes": codes,
            "review": doc.review,
            "facts": doc.facts,
        }
        out = WORK / line.make / "extracted" / f"{doc_key}.json"
        outputs.append((out, payload))
        print(f"{doc_key}: {len(doc.facts)} facts, {len(doc.review)} review; sections: "
              + " || ".join(s["heading"] for s in chosen), flush=True)
        if doc.unmapped:
            print("   unmapped labels: " + ", ".join(f"{k} x{v}" for k, v in doc.unmapped.items()), flush=True)
    return outputs


def check(paths: list[Path], sample: int) -> int:
    """Verify every quote against its page text; print `sample` random facts with their page line."""
    bad, facts = 0, []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        pages = json.loads(gzip.open(RAW_ROOT / "pagetext" / f"{data['doc']['sha256']}.json.gz", "rb").read())["pages"]
        for fact in data["facts"]:
            page = pages[fact["page"] - 1]
            if norm(fact["quote"]) not in norm(page):
                bad += 1
                print(f"QUOTE NOT FOUND {path.name}: {fact['key']} {fact['quote'][:80]}")
            facts.append((path.name, fact, page))
    print(f"check: {len(facts)} facts in {len(paths)} documents, quotes not found: {bad}")
    rng = random.Random()
    for name, fact, page in rng.sample(facts, min(sample, len(facts))):
        quote = norm(fact["quote"])
        lines = [ln for ln in page.split("\n") if norm(ln) and norm(ln) in quote]
        print(f"\n[{name}] {fact['key']} = {fact['value']!r}  engine_text={fact['engine_text']!r}  row={fact['row']!r}")
        print(f"   quote: {quote}")
        for ln in lines[:4]:
            print(f"   page text line: {ln}")
    return bad


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", type=int, default=0, metavar="N")
    args = parser.parse_args(argv)
    written = []
    counts: Counter = Counter()
    for host in HOSTS:
        manifest = Manifest(MANIFEST_DIR / f"{host}.csv", FIELDS)
        for row in manifest.rows.values():
            if row.get("doc_type") != "press_specifications" or row.get("status") != "ok":
                continue
            for out, payload in extract(host, row):
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
                written.append(out)
                counts.update(f["key"] for f in payload["facts"])
    print(f"\n{len(written)} documents written")
    for path in written:
        print(f"  {path}")
    print("facts per key: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if args.check:
        return 1 if check(written, args.check) else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

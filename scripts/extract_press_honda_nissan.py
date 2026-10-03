"""Parse the stored US press specification pages of hondanews.com, usa.nissannews.com,
usa.infinitinews.com and media.mitsubishicars.com into per-document JSON files
(data_work/_shared/press/FORMAT.md), by script only.

How a page is read
  * Only the release body (the same newsroom platform on all four hosts) and only its leaf
    tables are parsed; each table is laid out on a column grid (colspan / rowspan).
  * Row kinds: header rows (trim / model / engine column labels, e.g. "LX | SE | Sport",
    "Altima 2.5 | Altima 3.5", "Q50 2.0t | Q50 2.0t Premium"), group rows above a header row
    ("Gas Engine | Hybrid"), section rows (one cell: "ENGINE", "DIMENSIONS", "Brakes"), and
    data rows (label cell(s) + value cells).
  * A data row label (with its section) is mapped to a fact key by the rules in KEY_RULES.
    Values are paired with the columns they stand in: one fact per distinct value, with
    `engine_text` = the column labels it applies to (null when it applies to every column of a
    table without column labels). hondanews "<<" means "same as the cell to the left".
  * Rows whose label is the value and whose cells are only availability marks ("MacPherson
    Strut Front Suspension | • | •", "16\" steel ... | S | -", "5-Person Seating Capacity") give
    the label text (or the size/number in it) as the value for the marked columns.
  * Lines of text between tables that name a variant ("2017 INFINITI Q50 Sports Sedan - 2.0t")
    are the engine context of the tables that follow when a page has several of them.
  * Ambiguous rows go to `review`: several values in one cell without a label for each, several
    values without column labels, value units that are not the key's unit, numbers outside a
    plausible range, values carried into a row by rowspan.
  * `quote` = the row's cells from the label to the value cell, joined by spaces; it is checked
    against the stored page text (RAW_ROOT/pagetext/<sha256>.json.gz) after whitespace
    normalisation and the document is written with status "quote_error" if any quote fails.
  * Numbers are parsed only; units are not converted.

Usage:
  .venv/Scripts/python.exe scripts/extract_press_honda_nissan.py            (all four hosts)
  .venv/Scripts/python.exe scripts/extract_press_honda_nissan.py --host hondanews.com
"""

from __future__ import annotations

import argparse
import copy
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_press_honda_nissan import (FIELDS, HOSTS, MANIFEST_DIR, cell_lines, content_root,  # noqa: E402
                                        leaf_tables, page_title, row_cells)
from us_tech_common import RAW_ROOT, WORK, Manifest, read_maybe_gz, sha256  # noqa: E402
from us_tech_lines import BY_KEY  # noqa: E402

EXTRACTOR = "press-honda-nissan-1"
HOST_SHORT = {"hondanews.com": "hondanews", "usa.nissannews.com": "nissannews",
              "usa.infinitinews.com": "infinitinews", "media.mitsubishicars.com": "mitsubishicars"}
PUBLISHER = {
    "hondanews.com": "American Honda Motor Co. newsroom (hondanews.com)",
    "usa.nissannews.com": "Nissan USA Newsroom (usa.nissannews.com)",
    "usa.infinitinews.com": "INFINITI USA Newsroom (usa.infinitinews.com)",
    "media.mitsubishicars.com": "Mitsubishi Motors North America newsroom (media.mitsubishicars.com)",
}

NORMALIZE = ((chr(0xF0B4), chr(0x00D7)), (chr(0xF0B0), chr(0x00B0)), (chr(0xFFFE), ""), (chr(0x00AD), ""),
             (chr(0x00A0), " "), (chr(0x201C), '"'), (chr(0x201D), '"'), (chr(0x2019), "'"))


def norm(text: str) -> str:
    for old, new in NORMALIZE:
        text = text.replace(old, new)
    return " ".join(text.split())


# --------------------------------------------------------------------------- cells / grid
MARKS = {"s", "o", "•", "●", "◦", "std", "std.", "standard", "opt", "opt.", "optional", "available",
         "x", "✓", "✔", "yes", "p", "pkg", "pkg."}
EMPTY = {"", "-", "–", "—", "n/a", "na", "n.a.", "--", "---", "no"}


def is_mark(text: str) -> bool:
    t = re.sub(r"\s*\d+$", "", text.strip().lower())  # footnote digits after a mark
    return t in MARKS or bool(re.fullmatch(r"[•●]+", t))


def is_empty(text: str) -> bool:
    return text.strip().lower() in EMPTY


MEASURE = re.compile(r"\d\s*(@|x\b|×|/\s*\d|-?\s*in\b|-?\s*inch|mm\b|lb|hp\b|rpm|cc\b|mpg|gal|cu\.?\s*ft|"
                     r"cubic|ft\b|\"|%|liter|kw\b|amp|:\s*1\b)", re.I)


def header_like(text: str) -> bool:
    t = text.strip()
    return (bool(t) and len(t) <= 48 and not is_mark(t) and not is_empty(t) and t != "<<"
            and bool(re.search(r"[A-Za-z]", t)) and not MEASURE.search(t))


class Cell:
    def __init__(self, tag: Tag, index: int):
        self.lines = cell_lines(tag)
        self.text = " ".join(self.lines)
        self.colspan = _int(tag.get("colspan"))
        self.rowspan = _int(tag.get("rowspan"))
        self.th = tag.name == "th"
        self.index = index
        self.col = self.end = 0


def _int(v) -> int:
    try:
        return max(1, min(int(str(v).strip()), 30))
    except (TypeError, ValueError):
        return 1


class Row:
    def __init__(self, cells: list[Cell], carried: set[int], carried_text: dict | None = None):
        self.cells = cells
        self.carried = carried  # columns filled by a rowspan cell of a row above
        self.carried_text = carried_text or {}  # column -> text of that rowspan cell

    @property
    def nonempty(self):
        return [c for c in self.cells if c.text.strip()]


def grid(table: Tag) -> tuple[list[Row], int]:
    rows, carry, carry_text, width = [], {}, {}, 0
    for tr in table.find_all("tr"):
        cells = [Cell(td, i) for i, td in enumerate(row_cells(tr))]
        occupied = {c for c, n in carry.items() if n > 0}
        occupied_text = {c: carry_text.get(c, "") for c in occupied}
        col = 0
        for cell in cells:
            while col in occupied:
                col += 1
            cell.col, cell.end = col, col + cell.colspan
            col = cell.end
        width = max(width, col, max(occupied) + 1 if occupied else 0)
        new = {c: n - 1 for c, n in carry.items() if n - 1 > 0}
        for cell in cells:
            if cell.rowspan > 1:
                for c in range(cell.col, cell.end):
                    new[c] = cell.rowspan - 1
                    carry_text[c] = cell.text
        carry = new
        rows.append(Row(cells, occupied, occupied_text))
    return rows, width


# --------------------------------------------------------------------------- key rules
def has(pattern: str, text: str) -> bool:
    return bool(re.search(pattern, text, re.I))


def classify(label: str, section: str, motor_ctx: bool) -> str | None:
    """Fact key of a data row, from its label and section heading."""
    l = norm(label).lower()
    s = norm(section).lower()
    both = l + " | " + s
    if not l:
        return None
    if has(r"steer", l) and has(r"motor|assist|electric|power|eps|rack|pinion|type|system|^steering$", l) \
            and not has(r"wheel|column|ratio|turns|lock|mounted|heated|switch|control|paddle|memory|angle|sensor|indicator|warning|light|tilt|telescop|propilot|cruise|lane|park", l):
        return "steering"
    if has(r"steering", s) and has(r"^(type|system|steering type|steering system)$", l):
        return "steering"
    if has(r"transmission", s) and has(r"^(type|transmission type)$", l):
        return "transmission_description"
    if has(r"(total|combined|net) system|system (net )?(horse)?power|hybrid system net power|total system output|"
           r"combined (net )?(horse)?power|system output|total output", both) and has(r"power|hp|output", both):
        return "system_power_hp"
    if has(r"battery|charger|charging|generator|inverter|range\b", l) or (has(r"battery", s) and not has(r"motor", l)):
        return None
    if has(r"\bmotor\b", l) and not has(r"ratio|steer|motorized|mount|seat|door|window|mirror|liftgate|tailgate|"
                                         r"trunk|wiper|sunroof|moonroof", l):
        return "electric_motor"
    if (motor_ctx or has(r"electric motor|\bmotor\b|traction", s)) and has(r"horsepower|power|output|torque|^type$", l):
        return "electric_motor"
    if has(r"horsepower|^(net |max(imum)? |engine |peak )?(power|output|hp)\s*($|\(|@|/|,|:)|^engine (horse)?power", l) \
            and not has(r"weight|per liter|/liter|steering|take-off|outlet|point|seat|mirror|window|lock", l):
        return "power_hp"
    if has(r"torque", l) and not has(r"converter|vector|steer|split|distribution|sensing|wrench|management|"
                                     r"lug|bolt|nut|transfer|all-wheel|awd", l):
        return "torque_lb_ft"
    if has(r"displacement", l):
        return "engine_displacement_cc"
    if has(r"\bbore\b", l):
        return "bore_stroke"
    if has(r"compression ratio", l):
        return "compression_ratio"
    if has(r"valvetrain|valve train|^valves?$|valve gear|^valve( system| mechanism)?$", l):
        return "valvetrain"
    if has(r"fuel injection|fuel system|induction system|fuel delivery|injection system|^injection", l) \
            and not has(r"tank|capacity|economy|filler|door|cap\b|recommend|required", l):
        return "injection"
    if has(r"^(engine )?(code|name|model)$|^engine (code|name|model|designation)", l) and has(r"engine", both):
        return "engine_code"
    if has(r"^engines?\b", s) and has(r"\d\.\d\s?l\b", l) and has(r"cyl|v-?6|inline|in-line", l):
        return "engine_description"  # Mitsubishi "2.4L MIVEC SOHC 16-valve 4-cylinder | STD | -" rows
    if has(r"^engine( type)?$|^engine description$|^type$|^engine type", l) and has(r"engine|power ?unit|powertrain|"
                                                                                    r"mechanical", s + (" engine" if l.startswith("engine") else "")):
        return "engine_description"
    if has(r"transmission|^cvt\b|gearbox", l) and not has(r"city|highway|hwy|mpg|epa|combined|ratio|fluid|cooler|mode|oil|temp|shift(er)?s?\b|"
                                                          r"paddle|range|selector|mount|tunnel|warmer|logic|indicator|warning|light", l):
        return "transmission_description"
    if has(r"^(front |rear )?(stabilizer|shock tower|strut (tower )?bar|sway bar|damper|shock absorber|"
           r"performance damper|monotube)", l) and not has(r"suspension", l):
        return None
    if has(r"front suspension|suspension,? front|suspension \(front\)", l) or (has(r"suspension", s) and has(r"^front\b", l)):
        return "front_suspension"
    if has(r"rear suspension|suspension,? rear|suspension \(rear\)", l) or (has(r"suspension", s) and has(r"^rear\b", l)):
        return "rear_suspension"
    if (has(r"brake", l) or (has(r"brake", s) and has(r"^(front|rear)\b", l))) and not has(r"parking|assist|abs|anti-lock|distribution|ebd|hold|emergency|"
                                       r"override|caliper colou?r|light|lamp|pedal|regenerat|servo|booster|"
                                       r"brake-?force|braking system|smart|pre-crash|collision|auto|thickness", l):
        if has(r"front", l) and has(r"rear", l):
            return "brakes_front_rear"
        if has(r"^front\b|front brake|brakes?,? front|\bfront\b", l):
            return "front_brakes"
        if has(r"^rear\b|rear brake|brakes?,? rear|\brear\b", l):
            return "rear_brakes"
        return None
    if has(r"turning (circle|diameter)", l) and not has(r"radius", l):
        return "turning_circle_ft"
    if (has(r"\btires?\b", l) or (has(r"\btires?\b", s) and TIRE.search(label))) \
            and not has(r"pressure|monitor|repair|inflat|spare|temporary|kit|sealant|chains?\b|rotation", l):
        return "tires"
    if has(r"\bwheels?\b", l) and not has(r"wheelbase|steering|drive|tread|well|arch|lock|chock|cover|nut|"
                                          r"speed|alignment|resonator|spare|base|torque|-wheel|liner|opening|flare|"
                                          r"lug|cap\b|center|track|load|hub", l):
        return "wheel"
    if has(r"\bwheels?\b", s) and not has(r"steering", s) and has(r"\d\s*(\"|”|-?\s*in\b|-?\s*inch|x\s*\d)", l) \
            and not has(r"spare|temporary", l):
        return "wheel"
    if has(r"wheelbase|wheel base", l):
        return "wheelbase_in"
    if has(r"track|tread", l) and not has(r"pad|trac\b|traction|mode|app|tracker|tracking", l):
        if has(r"front", l) and has(r"rear", l):
            return "track_front_rear"
        if has(r"front", l):
            return "track_front_in"
        if has(r"rear", l):
            return "track_rear_in"
        return None
    if has(r"ground clearance|minimum clearance|running ground", l):
        return "ground_clearance_in"
    if has(r"curb weight", l) and not has(r"distribution|ratio|%", l):
        return "curb_weight_lb"
    if has(r"passenger volume|interior passenger volume|passenger compartment volume", l) and not has(r"cargo", l):
        return "passenger_volume_cu_ft"
    if has(r"cargo|trunk|luggage", l) and has(r"volume|capacity|space|area|cu\.? ?ft|cubic|room", l) \
            and not has(r"cover|light|lamp|hook|net|mat|tray|floor|opening|liner|organizer|release|width|length|height|"
                        r"weight|load", l):
        if has(r"max|behind (1st|first|front)|front seats?|seats? (folded|down)|folded|2nd row folded|"
               r"second row folded|rear seats? (folded|down)", l):
            return "cargo_max_cu_ft"
        return "cargo_cu_ft"
    if (has(r"fuel (tank )?(capacity|tank)|^fuel tank|^fuel capacity|tank capacity", l)
            or (l == "fuel" and has(r"capacit", s))) \
            and not has(r"economy|door|filler|recommend|required|type|mpg|octane|range|pressure", l):
        return "fuel_tank_gal"
    if (has(r"seating capacity|passenger capacity|^seating$|^seats$|^passenger seating$|"
            r"\d\s*-?\s*(person|passenger) seating", l)
            or (has(r"seat", s) and has(r"^(capacity|\d\s*-?\s*(person|passenger)s?)$", l))) \
            and not has(r"material|heated|power|trim|position|memory|ventilat|belt|cushion|system|row", l):
        return "seats"
    if has(r"\btow", l) and not has(r"hitch|mirror|mode|package|prep|harness|hook|eye|strap|assist|aid|wiring|"
                                     r"receiver|ball", l):
        return "towing_lb"
    if has(r"length", l) and not has(r"bed|cargo|leg|load|floor|trunk|seat|cable|blade|stroke|wiper|liftgate|"
                                      r"cushion|overhang|arm|rail", l) and has(r"^(overall |body |exterior |vehicle )?length|"
                                                                             r"^length|overall length", l):
        return "length_in"
    if has(r"width", l) and not has(r"mirror|track|tread|between|cargo|liftgate|door|opening|load|floor|trunk|"
                                     r"wheel|tire|seat|cushion|shoulder|hip|tailgate|bed|step|rim|pass-through", l) \
            and has(r"^(overall |body |exterior |vehicle )?width|overall width", l):
        return "width_in"
    if has(r"height", l) and not has(r"step|lift|load|floor|hitch|seat|cushion|liftgate|tailgate|ride|bed|"
                                      r"opening|deck|bumper|roof rack|cargo|trunk|hood", l) \
            and has(r"^(overall |body |exterior |vehicle )?height|overall height", l):
        return "height_in"
    return None


# string values must look like the key (a trim name in a "Steering" header-like row is not a steering type)
VALUE_OK = {
    "steering": r"steer|rack|pinion|assist|eps\b|electric|hydraulic",
    "front_suspension": r"strut|link|wishbone|beam|independent|axle|torsion|coil|leaf|macpherson|double|multi|suspension",
    "rear_suspension": r"strut|link|wishbone|beam|independent|axle|torsion|coil|leaf|macpherson|double|multi|suspension",
    "front_brakes": r"disc|drum|vent|solid|caliper|\d", "rear_brakes": r"disc|drum|vent|solid|caliper|\d",
    "transmission_description": r"speed|cvt|automatic|manual|xtronic|variable|transmission|direct|dct|clutch|"
                                r"drive unit|gear",
    "engine_description": r"cyl|v-?\d|inline|in-line|i-?4|turbo|dohc|sohc|boxer|atkinson|\d\.\d\s?l\b|liter|litre|"
                          r"\b[a-z]{2}\d{2}",
    "injection": r"inject|\bdig\b|mpi|mfi|sfi|gdi|direct|port|multi-?point|multi-?port|sequential|carbur|pgm-fi",
    "valvetrain": r"valve|dohc|sohc|vtec|cvtc|mivec|ohv|vvt|vvel",
    "electric_motor": r"\d",
    "compression_ratio": r"\d",
}
RANGES = {
    "power_hp": (40, 1000), "system_power_hp": (60, 1500), "torque_lb_ft": (40, 1200),
    "engine_displacement_cc": (600, 8000), "turning_circle_ft": (25, 55), "wheel_size_in": (13, 24),
    "length_in": (120, 260), "width_in": (55, 90), "height_in": (40, 90), "wheelbase_in": (80, 160),
    "track_front_in": (50, 75), "track_rear_in": (50, 75), "ground_clearance_in": (3, 14),
    "curb_weight_lb": (1500, 7500), "cargo_cu_ft": (3, 120), "cargo_max_cu_ft": (8, 160),
    "passenger_volume_cu_ft": (50, 200), "fuel_tank_gal": (5, 45), "seats": (2, 9), "towing_lb": (300, 12000),
}
# units that must not appear for a key (no conversion is done, such values go to review)
LITERS = r"\blit(er|re)s?\b|\d\s?L\b|\(L\)"
WRONG_UNIT = {
    "length_in": r"\bmm\b|\bcm\b", "width_in": r"\bmm\b|\bcm\b", "height_in": r"\bmm\b|\bcm\b",
    "wheelbase_in": r"\bmm\b|\bcm\b", "track_front_in": r"\bmm\b", "track_rear_in": r"\bmm\b",
    "ground_clearance_in": r"\bmm\b", "curb_weight_lb": r"\bkg\b", "cargo_cu_ft": LITERS,
    "cargo_max_cu_ft": LITERS, "passenger_volume_cu_ft": LITERS, "fuel_tank_gal": LITERS + r"|\bkg\b",
    "towing_lb": r"\bkg\b", "power_hp": r"\bkw\b(?!.*hp)|\bps\b", "torque_lb_ft": r"\bnm\b|n·m|n-m",
    "turning_circle_ft": r"\bm\b(?!ph)",
}
NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"


def number(text: str):
    m = re.search(NUM, text)
    if not m:
        return None
    v = float(m.group(0).replace(",", ""))
    return int(v) if v.is_integer() else v


def numbers(text: str) -> list:
    return [float(x.replace(",", "")) for x in re.findall(NUM, text)]


TIRE = re.compile(r"\b[PT]?\d{3}\s*/\s*\d{2}\s*/?\s*Z?R\s*-?\s*\d{2}(?:\.\d)?(?:\s*\(?\d{2,3}(?:/\d{2,3})?\s?[A-Z]{1,2}\)?(?![A-Za-z]))?",
                  re.I)
WHEEL = re.compile(r"(?<![\d.])(1[3-9]|2[0-4])(?:\.\d)?\s*(?:\"|”|''|-?\s*in\.?\b|-?\s*inch|\s*x\s*\d)", re.I)
TRANS_DESC = r"\d-speed|\bcvt\b|continuously variable|automatic|manual|xtronic|dual[- ]clutch|\bdct\b|e-?cvt"
HP_RPM = re.compile(r"(" + NUM + r")\s*(?:hp|horsepower|bhp|lb\.?\s*-?\s*ft\.?|lbs?\.?\s*-?\s*ft\.?|ft\.?\s*-?\s*lbs?\.?)?"
                    r"\s*(?:@|at)\s*([\d,]+(?:\s*[-–~]\s*[\d,]+)?)", re.I)


# --------------------------------------------------------------------------- parsing
class Doc:
    def __init__(self, row: dict, host: str):
        self.row, self.host = row, host
        self.facts, self.review, self.engine_codes = [], [], []
        self.pending = []  # facts before the engine-context / duplicate resolution

    def add_review(self, row_label: str, reason: str, quote: str = ""):
        item = {"page": 1, "row": row_label, "reason": reason}
        if quote:
            item["quote"] = quote
        self.review.append(item)


def text_blocks(root: Tag) -> list:
    """Release body as a sequence of ("text", line) and ("table", Tag) items in document order."""
    tables = set(map(id, leaf_tables(root)))
    out, buf = [], []

    def flush():
        line = " ".join(" ".join(buf).split())
        if line:
            out.append(("text", line))
        buf.clear()

    def walk(node):
        for child in node.children:
            if isinstance(child, NavigableString):
                if child.__class__.__name__ == "NavigableString":
                    buf.append(str(child))
            elif isinstance(child, Tag):
                if child.name in ("script", "style"):
                    continue
                if id(child) in tables:
                    flush()
                    out.append(("table", child))
                    continue
                block = child.name in ("p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "td",
                                       "th", "table", "section", "article", "ul", "ol")
                if block:
                    flush()
                walk(child)
                if block:
                    flush()

    walk(root)
    flush()
    return out


CONTEXT = re.compile(r"^(19|20)\d\d(\.5)?\s+\S.{3,90}$")
LINE_NAME = {"honda/accord": r"accord", "honda/civic": r"civic", "honda/cr-v": r"cr-?v", "nissan/altima": r"altima",
             "nissan/sentra": r"sentra", "nissan/rogue": r"rogue", "nissan/pathfinder": r"pathfinder",
             "infiniti/q50": r"q50", "infiniti/qx60": r"qx60|\bjx", "infiniti/fx-qx70": r"qx70|\bfx",
             "mitsubishi/outlander": r"outlander", "mitsubishi/outlander-sport": r"outlander"}
SECTION_VOCAB = set("""engine engines transmission transmissions drive drivetrain system systems steering suspension
brake brakes wheel wheels tire tires dimension dimensions exterior interior weight weights capacity capacities seating
seats chassis body electrical mechanical powertrain performance specification specifications model models grade grades
trim trims audio light lights lighting safety security feature features engineering power unit measurements and
inches in hybrid gasoline fuel economy key options packages instrumentation convenience comfort technology
description descriptions""".split())


def section_like(label: str) -> bool:
    """Label made only of section words: "Steering", "Wheels & Tires", "Exterior (inches)"."""
    words = re.findall(r"[a-z]+", re.sub(r"\(.*?\)", "", label).lower())
    return bool(words) and all(w in SECTION_VOCAB for w in words)


def engine_label(cols: list[int], headers: dict, groups: dict) -> str:
    by_group = defaultdict(list)
    order = []
    for c in cols:
        g = groups.get(c, "")
        h = headers.get(c, "")
        if g not in by_group:
            order.append(g)
        if h and h not in by_group[g]:
            by_group[g].append(h)
    parts = []
    for g in order:
        trims = ", ".join(by_group[g])
        parts.append(f"{g}: {trims}" if g and trims else (g or trims))
    return "; ".join(p for p in parts if p)


def is_context(text: str, line_key: str) -> bool:
    return bool(CONTEXT.match(text)) and not text.lower().startswith("note") \
        and bool(re.search(LINE_NAME.get(line_key, r"$^"), text, re.I))


def parse_doc(doc: Doc, soup: BeautifulSoup):
    root = content_root(soup)
    for tag in root.find_all(["script", "style"]):
        tag.decompose()
    blocks = text_blocks(root)
    line_key = doc.row["line"]
    contexts = [b[1] for b in blocks if b[0] == "text" and is_context(b[1], line_key)]
    multi_context = len(set(contexts)) > 1
    context = ""
    for kind, item in blocks:
        if kind == "text":
            if is_context(item, line_key):
                context = item
            continue
        parse_table(doc, item, context if multi_context else "")


def parse_table(doc: Doc, table: Tag, context: str):
    rows, width = grid(table)
    headers, groups = {}, {}
    first_value_col = None
    section, prev_kind = "", ""
    motor_ctx = False
    n_struct = 0  # header and data rows seen so far (section rows not counted)
    for row in rows:
        ne = row.nonempty
        if not ne:
            continue
        first = row.cells[0]
        # section row: one non-empty cell at column 0 and nothing carried into the row
        if len(ne) == 1 and ne[0].col == 0 and not row.carried and len(ne[0].text) <= 70 \
                and (len(row.cells) == 1 or not headers or ne[0].end >= width - 1) \
                and not re.match(r"^[*†‡\d(]", ne[0].text) and not is_mark(ne[0].text):
            section = f"{section} {ne[0].text}" if prev_kind == "section" else ne[0].text
            motor_ctx = has(r"motor", section)
            prev_kind = "section"
            continue
        # header row: column labels (trims / models / engines)
        label_cells = [c for c in row.cells if c.col == 0] if first.col == 0 else []
        value_cells = [c for c in row.cells if c not in label_cells]
        vals = [c for c in value_cells if c.text.strip()]
        label = " ".join(c.text for c in label_cells).strip()
        # trim names can look like marks or numbers ("S", "2.5"): allowed when most labels are words
        distinct = len({norm(c.text) for c in vals}) == len(vals)
        tokens_ok = all(header_like(c.text) or (distinct and (is_mark(c.text) or re.fullmatch(r"\d\.\d", c.text.strip())))
                        for c in vals) and sum(header_like(c.text) for c in vals) * 2 >= len(vals)
        if (len(vals) >= 2 and tokens_ok
                and (distinct or label.isupper() or n_struct == 0)
                and not row.carried
                and (not label or n_struct == 0 or label.isupper() or first.th
                     or (section_like(label) and (not headers or prev_kind == "header"
                                                  or {norm(c.text) for c in vals} <= {norm(v) for v in headers.values()})))):
            new_headers = {}
            for c in vals:
                for col in range(c.col, c.end):
                    new_headers[col] = c.text
            if prev_kind == "header" and headers:
                # the row above is a group row ("Gas Engine | Hybrid"); titles are not groups
                groups = {c: t for c, t in headers.items()
                          if not re.search(r"specification|feature|option|standard|(19|20)\d\d", t, re.I)}
            headers = new_headers
            first_value_col = min(c.col for c in value_cells)
            if label:
                section = label
                motor_ctx = has(r"motor", section)
            prev_kind = "header"
            n_struct += 1
            continue
        prev_kind = "data"
        n_struct += 1
        if headers and len(row.cells) > 2 and not row.cells[0].text and row.cells[0].col == 0                 and row.cells[-1].end == max(headers) + 1 + row.cells[0].colspan:
            # an empty leading cell pushes this row one column to the right of the header row
            shift = row.cells[0].colspan
            cells = [copy.copy(c) for c in row.cells[1:]]
            for c in cells:
                c.col, c.end = c.col - shift, c.end - shift
            row = Row(cells, {c - shift for c in row.carried if c >= shift})
        lab = handle_data_row(doc, row, headers, groups, first_value_col, section, context, motor_ctx, width)
        if lab and has(r"\bmotor\b", lab) and not has(r"steer", lab):
            motor_ctx = True
        elif lab and not has(r"torque|horsepower|power|output", lab):
            motor_ctx = has(r"motor", section)


def data_label(row: Row, first_value_col):
    """(label text, label cells, value cells) of a data row."""
    cells = row.cells
    if cells and cells[0].col > 0 and any(row.carried_text.get(c) for c in range(cells[0].col)):
        return "", [], cells  # label column filled by a (non-empty) rowspan cell above
    if first_value_col is not None and cells and cells[0].col < first_value_col:
        lab = [c for c in cells if c.col < first_value_col]
        val = [c for c in cells if c.col >= first_value_col]
    else:
        lab, val = [], []
        for i, c in enumerate(cells):
            valueish = bool(re.search(r"\d", c.text)) or is_mark(c.text) or c.text.strip() == "<<"
            if not val and i < len(cells) - 1 and (not lab or not valueish):
                lab.append(c)
            elif not lab:
                lab.append(c)
            else:
                val.append(c)
    return " ".join(c.text for c in lab if c.text).strip(), lab, val


def handle_data_row(doc: Doc, row: Row, headers: dict, groups: dict, fvc, section: str, context: str,
                    motor_ctx: bool, width: int) -> str:
    label, lab_cells, val_cells = data_label(row, fvc)
    if not label:
        if row.cells and row.cells[0].col == 0 and not row.cells[0].text and \
                any(re.search(r"\d\s*(hp|lb|in\b|in\.|cu|gal|@|rpm|mm|ft|cc|\")", c.text, re.I) for c in val_cells):
            doc.add_review(section or "(no label)", "row with values but without a label",
                           " ".join(c.text for c in row.cells if c.text))
        return ""
    key = classify(label, section, motor_ctx)
    # label written on several lines ("Front" / "Stabilizer bar") with values on the same lines
    label_lines = [l for c in lab_cells for l in c.lines]
    line_idx = None
    if len(label_lines) > 1 and (key is None or key in VALUE_OK):
        hit = next(((i, k) for i, k in enumerate(classify(l, section, motor_ctx) for l in label_lines) if k), None)
        if hit and (key is None or hit[1] == key):
            line_idx, key = hit
    if key is None:
        return label
    row_label = label if not section or norm(section).lower() in norm(label).lower() else f"{section} > {label}"

    def quote_upto(cell: Cell) -> str:
        return " ".join(c.text for c in row.cells if c.index <= cell.index and c.text)

    # value of every value column ("<<" = same as the cell to the left)
    col_cell, last = {}, None
    for c in val_cells:
        src = last if (c.text.strip() == "<<" and last is not None) else c
        for col in range(c.col, c.end):
            col_cell[col] = src
        if c.text.strip() != "<<":
            last = c
    value_cols = sorted(col_cell)
    if not value_cols:
        if row.carried:
            doc.add_review(row_label, "value carried from the row above (rowspan)", label)
        return label
    texts = {col: col_cell[col].text.strip() for col in value_cols}

    # second label cell with one line per variant ("6-speed manual" / "Xtronic") and value cells with one
    # availability mark per line
    ql = lab_cells[-1].lines if len(lab_cells) > 1 else []
    filled = [c for c in val_cells if c.text.strip() and c.text.strip() != "<<"]
    if len(ql) > 1 and filled and all(len(c.lines) == len(ql) and all(is_mark(x) or is_empty(x) for x in c.lines)
                                      for c in filled):
        for i, qline in enumerate(ql):
            marked = [col for col in value_cols if len(col_cell[col].lines) == len(ql)
                      and is_mark(col_cell[col].lines[i])]
            line_texts = {col: (col_cell[col].lines[i] if len(col_cell[col].lines) == len(ql) else "")
                          for col in value_cols}
            if marked:
                mark_row(doc, classify(qline, section, motor_ctx) or key, qline, f"{row_label} > {qline}", row,
                         lab_cells, marked, value_cols, line_texts, headers, groups, context, quote_upto)
        return label

    # transmission rows whose label is the transmission and whose cells say for which trims
    if key == "transmission_description" and has(TRANS_DESC, label) \
            and not has(r"^(transmission|transmission type|type)$", norm(label)):
        marked = [col for col in value_cols if not is_empty(texts[col]) and texts[col] != "<<"]
        if marked:
            mark_row(doc, key, label, row_label, row, lab_cells, marked, value_cols,
                     {c: ("S" if c in marked else "-") for c in value_cols}, headers, groups, context, quote_upto)
        return label

    # the label is the value, the cells are availability marks
    if all(is_mark(t) or is_empty(t) for t in texts.values()):
        marked = [col for col in value_cols if is_mark(texts[col])]
        if marked:
            mark_row(doc, key, label, row_label, row, lab_cells, marked, value_cols, texts, headers, groups,
                     context, quote_upto)
        return label

    by_value, first_cell = defaultdict(list), {}
    for col in value_cols:
        t = texts[col]
        if is_empty(t) or is_mark(t) or t == "<<":
            continue
        k = norm(t)
        by_value[k].append(col)
        first_cell.setdefault(k, col_cell[col])
    plans = []
    for val_text, cols in by_value.items():
        cell = first_cell[val_text]
        if headers:
            if len(by_value) == 1 and set(cols) == set(value_cols):
                eng = None
            else:
                eng = engine_label(cols, headers, groups) or None
                if eng is None:
                    doc.add_review(row_label, "value columns without column labels", quote_upto(cell))
                    continue
        else:
            eng = None
            if len(by_value) > 1:
                qual = re.search(r"\(([^()]*[A-Za-z][^()]*)\)\s*$", cell.text)
                if not qual:
                    doc.add_review(row_label, "several values in one row without column labels", quote_upto(cell))
                    continue
                eng = qual.group(1).strip()
        plans.append((cell, eng))
    # different values under the same column label (e.g. two columns both headed "Sport")
    dup = {e for e, n in Counter(e for _, e in plans if e).items() if n > 1}
    for cell, eng in plans:
        if eng in dup:
            doc.add_review(row_label, f"different values under the same column label '{eng}'", quote_upto(cell))
            continue
        if context:
            eng = f"{context}: {eng}" if eng else context
        qual_lines = lab_cells[-1].lines if len(lab_cells) > 1 and len(lab_cells[-1].lines) > 1 else []
        value_cell = cell
        if line_idx is not None and len(cell.lines) == len(label_lines):
            value_cell = copy.copy(cell)  # only the line next to the label line of the key
            value_cell.lines = [cell.lines[line_idx]]
            value_cell.text = cell.lines[line_idx]
            qual_lines = []
        emit(doc, key, value_cell, label, row_label, eng, quote_upto(cell), section, qual_lines)
    return label


def mark_row(doc, key, label, row_label, row, lab_cells, marked, value_cols, texts, headers, groups, context,
             quote_upto):
    """Label carries the value; marks tell which columns have it."""
    last_marked_cell = None
    for c in row.cells:
        if c.col in marked or any(col in marked for col in range(c.col, c.end)):
            last_marked_cell = c
    quote = quote_upto(last_marked_cell) if last_marked_cell else label
    eng = None
    if headers and set(marked) != set(value_cols):
        eng = engine_label(marked, headers, groups)
        marks = sorted(set(texts[c] for c in marked))
        if any(m.upper() == "O" for m in marks):
            eng = "; ".join(f"{headers.get(c, '')} ({texts[c]})" for c in marked)
    elif not headers and set(marked) != set(value_cols):
        doc.add_review(row_label, "availability marks without column labels", quote)
        return
    if context:
        eng = f"{context}: {eng}" if eng else context
    if key in ("front_suspension", "rear_suspension", "steering", "transmission_description", "injection",
               "front_brakes", "rear_brakes", "engine_description", "valvetrain"):
        if norm(label).lower() in ("front", "rear", "type", "standard", "transmission", "steering", "engine"):
            return
        add_fact(doc, key, norm(label), quote, label + " " + " ".join(texts[c] for c in marked[:1]), eng, row_label)
    elif key == "tires":
        sizes = TIRE.findall(label)
        for size in sizes:
            add_fact(doc, "tires", norm(size), quote, label, eng, row_label)
    elif key == "wheel":
        m = WHEEL.search(label)
        if m:
            add_fact(doc, "wheel_size_in", number(m.group(1)), quote, label, eng, row_label)
    elif key == "seats":
        m = re.search(r"(\d)\s*-?\s*(?:person|passenger|seat)", label, re.I)
        if m:
            add_fact(doc, "seats", int(m.group(1)), quote, label, eng, row_label)


def add_fact(doc: Doc, key, value, quote, original, eng, row_label):
    if value is None or value == "":
        return
    if key in VALUE_OK and not has(VALUE_OK[key], str(value)):
        return  # a header or note cell read as a value
    if key in RANGES and isinstance(value, (int, float)):
        lo, hi = RANGES[key]
        if not lo <= value <= hi:
            doc.add_review(row_label, f"{key} value {value} outside plausible range {lo}-{hi}", quote)
            return
    doc.pending.append({"key": key, "value": value, "page": 1, "quote": quote, "original": norm(original),
                        "engine_text": eng, "row": norm(row_label)})


def split_parts(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\s*/\s*", text) if p.strip()]


SPACE_THOUSANDS = re.compile(r"^\s*(\d{1,3}(?: \d{3})+)\s*(lbs?\.?|cc)?\s*$", re.I)
BIG_KEYS = ("curb_weight_lb", "towing_lb", "engine_displacement_cc")


def number_for(key: str, text: str):
    """Number of a value text; "3 497" (space as thousands separator) for keys in thousands."""
    m = SPACE_THOUSANDS.match(text)
    if key in BIG_KEYS and m:
        return int(m.group(1).replace(" ", ""))
    return number(text)


def slash_qualifiers(label: str) -> list[str]:
    """Qualifiers written as "A/B" in a label: "Curb Weight (lbs, MT/AT)", "(6MT/CVT/CVT with HS)",
    "Height FWD / 4WD (in)". Empty when the parts are not all distinct variant names."""
    variant = r"(\b\d*(wd|mt|at|cvt|awd|fwd|rwd|4wd|2wd)\b|\bhs\b|sensing|navi)"
    candidates = [g.split(",")[-1] for g in re.findall(r"[(\[]([^()\[\]]*/[^()\[\]]*)[)\]]", label)]
    candidates += [m.group(1) for m in re.finditer(r"(\b[A-Za-z0-9]+(?:\s*/\s*[A-Za-z0-9]+)+\b)", re.sub(r"[(\[][^)\]]*[)\]]", "", label))]
    for cand in candidates:
        parts = [p.strip() for p in re.split(r"\s*(?<![Ww])/\s*", cand) if p.strip()]  # not "w/Navi"
        if len(parts) > 1 and all(has(variant, p) for p in parts) \
                and not any(has(r"^(front|rear|up|down)$", p) for p in parts):
            return parts if len(set(parts)) == len(parts) else []
    return []


def emit(doc: Doc, key: str, cell: Cell, label: str, row_label: str, eng, quote: str, section: str,
         qual_lines: list[str] | None = None):
    """Facts of one value cell. `qual_lines`: lines of a second label cell ("FWD / AWD" on two lines)
    that name the lines of the value cell."""
    qual_lines = qual_lines or []
    original = f"{label} {cell.text}"
    lines = []
    for l in [l for l in cell.lines if l.strip()] or [cell.text]:
        parts = re.split(r"\s+/\s+", l)
        # "38.1 ft (CVT) / 39.4 ft (6MT)", "16.2 – FWD / 16.0 - AWD": one value per qualified part
        if len(parts) > 1 and all(len(re.findall(NUM, p)) == 1 and qualifier(re.sub(NUM, "", p, count=1))
                                  for p in parts):
            lines.extend(parts)
        else:
            lines.append(l)
    unit_ctx = f"{label} {section}"

    def add(k, value, e=eng, row=row_label):
        add_fact(doc, k, value, quote, original, e, row)

    def with_q(q):
        return f"{eng} ({q})" if eng else q

    if key == "engine_code":
        for code in re.findall(r"\b[A-Z0-9]{2,}[A-Z0-9-]*\b", cell.text):
            if re.search(r"[A-Z]", code) and re.search(r"\d", code) and code not in doc.engine_codes:
                doc.engine_codes.append(code)
        return
    if key in ("engine_description", "valvetrain", "injection", "transmission_description", "front_suspension",
               "rear_suspension", "steering", "electric_motor", "compression_ratio", "front_brakes", "rear_brakes"):
        if key == "compression_ratio" and not re.search(r"\d", cell.text):
            return
        add(key, norm(cell.text))
        return
    if key == "brakes_front_rear":
        lab = re.sub(r"\s*\((?:in\.?|inches|mm)\)\s*$", "", norm(label))
        unit = re.search(r"\((in\.?|inches|mm)\)", label)
        lparts, vparts = split_parts(lab), split_parts(cell.text)
        if len(lparts) == 2 and len(vparts) == 2 and has(r"front", lparts[0]) and has(r"rear", lparts[1]):
            for k, lp, vp in (("front_brakes", lparts[0], vparts[0]), ("rear_brakes", lparts[1], vparts[1])):
                add(k, f"{lp} {vp}" + (f" {unit.group(1)}" if unit else ""))
        else:
            doc.add_review(row_label, "front/rear brakes row that cannot be split", quote)
        return
    if key == "bore_stroke":
        t = cell.text
        mm = has(r"\bmm\b", unit_ctx + " " + t)
        inch = has(r"\bin\b|\binch|\bin\.", unit_ctx + " " + t)
        if mm and inch:
            doc.add_review(row_label, "bore x stroke in mixed units", quote)
        elif mm:
            add("bore_stroke_mm", norm(t))
        elif inch:
            add("bore_stroke_in", norm(t))
        else:
            doc.add_review(row_label, "bore x stroke without unit", quote)
        return
    if key == "tires":
        for size in dict.fromkeys(norm(s) for s in TIRE.findall(cell.text)):
            add("tires", size)
        return
    if key == "wheel":
        m = WHEEL.search(cell.text)
        if not m and has(r"\(in\.?\)|inch|\bin\b", label):
            m = re.match(r"\s*(1[3-9]|2[0-4])(?:\.\d)?\b", cell.text)
        if m:
            add("wheel_size_in", number(m.group(1)))
        return
    if key == "track_front_rear":
        if has(WRONG_UNIT["track_front_in"], unit_ctx + " " + cell.text):
            doc.add_review(row_label, "track in mm", quote)
            return
        items = []
        one_per_line = [re.findall(NUM, l) for l in lines]
        if len(lines) == 2 and all(len(v) == 1 for v in one_per_line) and not re.search(r"[A-Za-z]{2}", cell.text):
            # "Front Rear" label cells, one number per line: front on the first line, rear on the second
            items = [([one_per_line[0][0], one_per_line[1][0]], "")]
            lines = []
        for l in lines:
            vals = re.findall(NUM, re.sub(r"\([^)]*\)", "", l))
            q = re.search(r"\(([^)]*[A-Za-z][^)]*)\)", l)
            if len(vals) == 2:
                items.append((vals, q.group(1).strip() if q else ""))
            elif vals:
                items = None
                break
        if not items or (len(items) > 1 and not all(q for _, q in items)):
            doc.add_review(row_label, "front/rear track row that cannot be split", quote)
            return
        for vals, q in items:
            e = with_q(q) if len(items) > 1 else eng
            add("track_front_in", number(vals[0]), e, row_label + " (front)")
            add("track_rear_in", number(vals[1]), e, row_label + " (rear)")
        return
    lab_parts = split_parts(re.sub(r"\([^)]*\)", "", label))
    if key in ("length_in", "width_in", "height_in") and len(lab_parts) > 1 and not slash_qualifiers(label):
        # "Overall Length/Width/Height (in) | 185.8/74.7/68.8"
        vparts = split_parts(cell.text)
        keys = [classify(p, section, False) for p in lab_parts]
        if len(vparts) == len(lab_parts) and all(k in ("length_in", "width_in", "height_in") for k in keys):
            if has(r"\bmm\b", unit_ctx + " " + cell.text):
                doc.add_review(row_label, "dimensions in mm", quote)
                return
            for k, vp in zip(keys, vparts):
                add(k, number(vp))
        else:
            doc.add_review(row_label, "combined dimension row that cannot be split", quote)
        return
    if key in ("cargo_cu_ft", "cargo_max_cu_ft") and has(r"up\s*/\s*down|seats? up\s*/\s*(folded|down)", label):
        parts = split_parts(re.sub(r"\([^)]*\)", "", cell.text))
        vals = [re.match(r"\s*(" + NUM + r")", p) for p in parts]
        if len(parts) == 2 and all(vals) and not has(LITERS, cell.text):
            add("cargo_cu_ft", number(vals[0].group(1)), eng, row_label + " (up)")
            add("cargo_max_cu_ft", number(vals[1].group(1)), eng, row_label + " (down)")
        else:
            doc.add_review(row_label, "cargo up/down row that cannot be split", quote)
        return
    if key in WRONG_UNIT and has(WRONG_UNIT[key], cell.text + " " + label):
        doc.add_review(row_label, f"value unit is not the unit of {key}", quote)
        return
    # "Curb Weight (lbs, MT/AT) | 3192 / 3254"
    quals = slash_qualifiers(label)
    if quals and key not in ("power_hp", "torque_lb_ft"):
        vparts = split_parts(cell.text)
        if len(vparts) == len(quals) and all(re.fullmatch(r"(" + NUM + r")\s*[A-Za-z.]*|n/?a|-", v, re.I) for v in vparts):
            for q, v in zip(quals, vparts):
                if re.search(r"\d", v):
                    add(key, number_for(key, v), with_q(q))
        elif len(vparts) == 1 and len(numbers(cell.text)) == 1:
            # one value in the column (the trim's value); the label only lists the variants
            add(key, number_for(key, cell.text))
        else:
            doc.add_review(row_label, "values that do not match the label qualifiers", quote)
        return
    numeric_lines = [l for l in lines if re.search(r"\d", l)]
    if key in ("power_hp", "torque_lb_ft", "system_power_hp"):
        items = []
        for l in numeric_lines:
            matches = list(HP_RPM.finditer(l))
            if matches:
                for i, m in enumerate(matches):
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(l)
                    start = m.start() if i else 0
                    items.append((number(m.group(1)), m.group(2).strip(), l[start:m.start()] + l[m.end():end], l))
            else:
                n = number(l)
                if n is not None:
                    items.append((n, None, re.sub(NUM, "", l, count=1), l))
        if not items:
            return
        quals = list(qual_lines) if len(qual_lines) == len(items) > 1 else [qualifier(it[2]) for it in items]
        if len(items) > 1 and (not all(quals) or len(set(quals)) != len(quals)):
            doc.add_review(row_label, "several values in one cell without a label for each", quote)
            return
        rpm_key = {"power_hp": "power_rpm", "torque_lb_ft": "torque_rpm"}.get(key)
        for (n, rpm, rest, l), q in zip(items, quals):
            e = with_q(q) if len(items) > 1 else eng
            if key in WRONG_UNIT and has(WRONG_UNIT[key], l):
                doc.add_review(row_label, f"value unit is not the unit of {key}", quote)
                continue
            before = len(doc.pending)
            add(key, n, e)
            if rpm and rpm_key and len(doc.pending) > before:
                add(rpm_key, rpm, e)
        return
    if key == "engine_displacement_cc":
        t = cell.text
        m = re.search(r"(" + NUM + r")\s*cc\b", t, re.I)
        paren = re.search(r"\(([^)]*)\)", label)
        lparts = split_parts(paren.group(1)) if paren else []
        parts = split_parts(t)
        idx = next((i for i, p in enumerate(lparts) if has(r"\bcc\b", p)), None)
        if m:
            add(key, number(m.group(1)))
        elif has(r"\bcc\b", label) and len(parts) == 1 and len(lparts) <= 1:
            add(key, number_for(key, parts[0]))
        elif idx is not None and len(parts) == len(lparts):
            add(key, number_for(key, parts[idx]))
        else:
            doc.add_review(row_label, "displacement without a cc value", quote)
        return
    if key == "towing_lb" and len(qual_lines) == len(numeric_lines) > 1 and any(has(r"tongue", q) for q in qual_lines):
        # "Towing | Trailer / Tongue": the trailer line is the towing capacity
        trailer = [l for l, q in zip(numeric_lines, qual_lines) if has(r"trailer", q)]
        if len(trailer) == 1:
            add(key, number_for(key, trailer[0]))
        else:
            doc.add_review(row_label, "towing row without a single trailer value", quote)
        return
    if key == "ground_clearance_in" and has(r"\bfr\.?\s*/\s*rr\b|front\s*/\s*rear", label):
        doc.add_review(row_label, "ground clearance given for front/rear", quote)
        return
    if key == "curb_weight_lb" and len(qual_lines) == len(numeric_lines) > 1 \
            and any(has(r"front|rear", q) for q in qual_lines):
        # "Curb weight (lbs.) | Front / Rear / Total": axle loads are not the curb weight
        total = [l for l, q in zip(numeric_lines, qual_lines) if has(r"total", q)]
        if len(total) == 1:
            add(key, number_for(key, total[0]))
        else:
            doc.add_review(row_label, "curb weight given per axle without a total", quote)
        return
    if len(numeric_lines) > 1 and len({number(l) for l in numeric_lines}) > 1:
        quals = (list(qual_lines) if len(qual_lines) == len(numeric_lines)
                 else [qualifier(re.sub(NUM, "", l, count=1)) for l in numeric_lines])
        if all(quals) and len(set(quals)) == len(quals):
            for l, q in zip(numeric_lines, quals):
                add(key, number_for(key, l), with_q(q))
        else:
            doc.add_review(row_label, "several values in one cell without a label for each", quote)
        return
    if key in ("cargo_cu_ft", "cargo_max_cu_ft") and len(numbers(re.sub(r"\([^)]*\)", "", cell.text))) > 1:
        doc.add_review(row_label, "several cargo values in one cell", quote)
        return
    text = numeric_lines[0] if numeric_lines else cell.text
    if "/" in text and len(re.findall(NUM, re.sub(r"\([^)]*\)", "", text))) > 1:
        doc.add_review(row_label, "several values separated by '/' without a label for each", quote)
        return
    add(key, number_for(key, text))


UNIT_WORDS = r"(hp|horsepower|bhp|lb\.?-?\s*ft\.?|lbs?\.?-?\s*ft\.?|lb\.?|lbs\.?|rpm|in\.?|inches|ft\.?|cu\.?\s*ft\.?|" \
             r"cubic\s*f(ee|oo)t\.?|gal\.?|gallons|kw|@|at|net|sae|approx\.?|est\.?|estimated)"


def qualifier(rest: str) -> str:
    q = re.sub(UNIT_WORDS, " ", rest, flags=re.I)
    q = re.sub(r"[\s\-–—:;,()/]+", " ", q).strip()
    return q if re.search(r"[A-Za-z]", q) else ""


# --------------------------------------------------------------------------- documents
def finalize(doc: Doc):
    """Merge duplicates; several different values of a key without engine/trim label -> review."""
    seen = set()
    by_key = defaultdict(list)
    for f in doc.pending:
        sig = (f["key"], json.dumps(f["value"]), f["engine_text"], f["row"])
        if sig in seen:
            continue
        seen.add(sig)
        by_key[f["key"]].append(f)
    single_valued = {"power_hp", "torque_lb_ft", "engine_displacement_cc", "system_power_hp", "length_in", "width_in",
                     "height_in", "wheelbase_in", "track_front_in", "track_rear_in", "ground_clearance_in",
                     "fuel_tank_gal", "seats", "towing_lb", "turning_circle_ft", "curb_weight_lb",
                     "passenger_volume_cu_ft", "compression_ratio", "bore_stroke_mm", "bore_stroke_in",
                     "power_rpm", "torque_rpm"}
    for key, facts in by_key.items():
        unlabeled = [f for f in facts if not f["engine_text"]]
        values = {json.dumps(f["value"]) for f in unlabeled}
        rows = {f["row"] for f in unlabeled}
        if key in single_valued and len(values) > 1 and len(rows) == 1:
            for f in unlabeled:
                doc.add_review(f["row"], f"{key}: several values without engine/trim label", f["quote"])
            facts = [f for f in facts if f["engine_text"]]
        elif key in single_valued and len(values) > 1 and key not in ("cargo_cu_ft", "cargo_max_cu_ft"):
            # different rows give different values with no engine label: keep, the rows differ
            pass
        doc.facts.extend(facts)


def check_quotes(doc: Doc, page_text: str) -> list[str]:
    page = norm(page_text)
    bad = [f["quote"] for f in doc.facts if norm(f["quote"]) not in page]
    bad += [r["quote"] for r in doc.review if r.get("quote") and norm(r["quote"]) not in page]
    return bad


def release_id(url: str) -> str:
    m = re.search(r"release-[0-9a-f]{32}", url)
    return m.group(0) if m else url


def run(hosts: list[str]) -> dict:
    stats = {}
    for host in hosts:
        manifest = Manifest(MANIFEST_DIR / f"{host}.csv", FIELDS)
        rows = [r for r in manifest.rows.values() if r.get("status") == "ok"]
        done_ids, written = set(), []
        key_counts, n_docs, n_review, quote_errors = Counter(), 0, 0, 0
        for row in rows:
            rid = release_id(row["url"])
            if rid in done_ids:
                continue
            done_ids.add(rid)
            raw = RAW_ROOT / row["path"]
            body = read_maybe_gz(raw)
            assert sha256(body) == row["sha256"], raw
            pt = json.loads(gzip.open(RAW_ROOT / "pagetext" / f"{row['sha256']}.json.gz").read().decode("utf-8"))
            soup = BeautifulSoup(body, "html.parser")
            doc = Doc(row, host)
            parse_doc(doc, soup)
            finalize(doc)
            bad = check_quotes(doc, pt["pages"][0])
            line = BY_KEY[row["line"]]
            dkey = f"press-{HOST_SHORT[host]}-{line.slug}-{row['year']}-{row['sha256'][:8]}"
            out = {
                "doc": {
                    "key": dkey, "make": line.make, "lines": [line.key], "years": [int(row["year"])],
                    "doc_type": "press_specifications", "title": row["title"] or page_title(soup),
                    "path": str(raw), "url": row["url"], "page_url": "", "sha256": row["sha256"],
                    "retrieved_at": row["retrieved_at"], "tier": "A", "source_type": "PRESS_RELEASE",
                    "publisher": PUBLISHER[host], "authenticity": "OFFICIAL_PUBLISHER",
                },
                "extractor": EXTRACTOR,
                "pages": 1,
                "edition_market": "US",
                "status": "ok" if not bad else "quote_error",
                "engine_codes": doc.engine_codes,
                "review": doc.review,
                "facts": doc.facts,
            }
            if bad:
                out["quote_errors"] = bad
                quote_errors += len(bad)
            if not doc.facts:
                out["status"] = "no_facts" if not bad else out["status"]
            target = WORK / line.make / "extracted" / f"{dkey}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
            written.append(target)
            n_docs += 1
            n_review += len(doc.review)
            key_counts.update(f["key"] for f in doc.facts)
        stats[host] = {"documents": n_docs, "facts": sum(key_counts.values()), "review": n_review,
                       "quote_errors": quote_errors, "facts_per_key": dict(sorted(key_counts.items()))}
        print(host, json.dumps(stats[host], ensure_ascii=False))
    return stats


def verify(hosts: list[str], samples: int, seed: int) -> int:
    """Re-read every written document: each quote must occur in its stored page text (after whitespace
    normalisation) and contain the fact value's number; print `samples` random facts with the page
    line that holds the quote, for a manual check of label/value pairing."""
    import random
    shorts = [HOST_SHORT[h] for h in hosts]
    docs = []
    for path in sorted(WORK.glob("*/extracted/press-*.json")):
        if any(path.name.startswith(f"press-{s}-") for s in shorts):
            docs.append(json.loads(path.read_text(encoding="utf-8")))
    bad, checked, facts = 0, 0, []
    for d in docs:
        pt = json.loads(gzip.open(RAW_ROOT / "pagetext" / f"{d['doc']['sha256']}.json.gz").read().decode("utf-8"))
        page = norm(pt["pages"][0])
        for f in d["facts"]:
            checked += 1
            ok = norm(f["quote"]) in page
            if ok and isinstance(f["value"], (int, float)):
                digits = [x.replace(",", "") for x in re.findall(NUM, f["quote"])]
                digits += [x.replace(" ", "") for x in re.findall(r"\d{1,3}(?: \d{3})+", f["quote"])]
                ok = any(_num_eq(x, f["value"]) for x in digits)
            if not ok:
                bad += 1
                print("QUOTE PROBLEM", d["doc"]["key"], f["key"], f["value"], f["quote"][:120])
            facts.append((d, f, pt["pages"][0]))
    print(f"documents {len(docs)}, facts {checked}, quote problems {bad}")
    random.seed(seed)
    for d, f, text in random.sample(facts, min(samples, len(facts))):
        q = norm(f["quote"])
        line = next((l for l in text.split("\n") if norm(l) and norm(l).startswith(q[:60])), "")
        print(f"\n{d['doc']['key']} | {d['doc']['title']}\n  fact: {f['key']} = {f['value']!r} | engine_text: "
              f"{f['engine_text']} | row: {f['row']}\n  page line: {line.replace(chr(9), ' | ')[:400]}")
    return bad


def _num_eq(text: str, value) -> bool:
    try:
        return abs(float(text) - float(value)) < 1e-9
    except ValueError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", action="append", choices=list(HOSTS))
    ap.add_argument("--verify", action="store_true", help="check the written documents instead of parsing")
    ap.add_argument("--samples", type=int, default=5, help="random facts to print with --verify")
    ap.add_argument("--seed", type=int, default=20261002)
    args = ap.parse_args()
    if args.verify:
        sys.exit(1 if verify(args.host or list(HOSTS), args.samples, args.seed) else 0)
    run(args.host or list(HOSTS))


if __name__ == "__main__":
    main()

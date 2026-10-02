"""Parse the stored Toyota / Lexus US press specification documents into per-document JSON.

Input: rows `doc_type=press_specifications, status=ok` of
data_work/_shared/manifest_press/pressroom.toyota.com.csv and pressroom.lexus.com.csv (written by
scripts/collect_press_toyota.py) and the stored files under RAW_ROOT/press/<host>/.
Output: data_work/<make>/extracted/press-<toyota|lexus>-<line-slug>-<year>-<sha8>.json in the
format of data_work/_shared/press/FORMAT.md.

The spec documents are "Product Information" / "Specifications" PDFs: Word tables with a label
column and one value column, or several value columns titled in the section header row
("ENGINE  FOUR-CYLINDER  V6"). The parser works on pdfplumber words (the same word and line
clustering as pdfplumber's extract_text, which is the stored page text):
  * lines are split into cells where the horizontal gap between words is larger than 8 pt;
  * a section starts at an upper-case title in the label column ("EXTERIOR DIMENSIONS");
  * the value-column start of a section is the most frequent x of the first value cell;
  * a row starts at a label in the label column; "- Front" style labels are sub-rows; lines
    without a label continue the row; label-only lines continue a wrapped label;
  * grade header lines inside a row ("LE  SE  XLE  XSE" over "3,450  3,494 ...") give the
    labels of the numbers below them (paired by horizontal position);
  * qualifiers "(LE and XLE)", "L/LE (All) = ..." and the column title give `engine_text`;
    conditions "(w/ moonroof)", "(17-in. wheels)" go into `row`.
Every fact quote is a contiguous run of words of the page text and is checked against
RAW_ROOT/pagetext/<sha256>.json.gz; rows that map to a fact key but cannot be read
unambiguously go to `review`. Units are not converted.

Run:
  uv run --offline --no-project --with pdfplumber --with pypdfium2 python scripts/extract_press_toyota.py
  ... scripts/extract_press_toyota.py --verify            (quote check of the written JSON)
  ... scripts/extract_press_toyota.py --spot 5 --seed 7    (print random facts with page context)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from operator import itemgetter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

EXTRACTOR = "press-toyota-1"
HOSTS = {
    "pressroom.toyota.com": {"short": "toyota", "publisher": "Toyota USA Newsroom (pressroom.toyota.com)"},
    "pressroom.lexus.com": {"short": "lexus", "publisher": "Lexus USA Newsroom (pressroom.lexus.com)"},
}
MANIFEST_DIR = WORK / "_shared" / "manifest_press"
GAP = 8.0  # pt; a larger gap between two words separates two table cells


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


# ---------------------------------------------------------------------------------------
# Page model
# ---------------------------------------------------------------------------------------
@dataclass
class Seg:
    line: "Line"
    w0: int  # first word index in the line
    w1: int  # last word index (inclusive)

    @property
    def words(self):
        return self.line.words[self.w0 : self.w1 + 1]

    @property
    def x0(self) -> float:
        return self.words[0]["x0"]

    @property
    def x1(self) -> float:
        return self.words[-1]["x1"]

    @property
    def center(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def text(self) -> str:
        return " ".join(w["text"] for w in self.words)


@dataclass
class Line:
    gi: int  # global index over the document
    page: int  # 1-based
    top: float
    words: list
    height: float
    segs: list = field(default_factory=list)
    band: tuple | None = None  # (page, number of table rules above the line) when the page has rules

    @property
    def text(self) -> str:
        return " ".join(w["text"] for w in self.words)


def load_lines(pdf) -> tuple[list[Line], int]:
    from pdfplumber.utils import cluster_objects

    lines: list[Line] = []
    for pno, page in enumerate(pdf.pages, start=1):
        words = page.extract_words()
        # horizontal table rules (cell borders) give the row bands of the Word tables
        rules: list[float] = []
        for y in sorted(e["top"] for e in page.edges if e["orientation"] == "h" and e["width"] > 0.25 * page.width):
            if not rules or y - rules[-1] > 2.0:
                rules.append(y)
        for group in cluster_objects(words, itemgetter("top"), 3):
            group = sorted(group, key=itemgetter("x0"))
            line = Line(len(lines), pno, group[0]["top"], group, float(page.height))
            if len(rules) >= 3:
                middle = (min(w["top"] for w in group) + max(w["bottom"] for w in group)) / 2
                line.band = (pno, sum(1 for y in rules if y < middle))
            start = 0
            for i in range(1, len(group) + 1):
                if i == len(group) or group[i]["x0"] - group[i - 1]["x1"] > GAP:
                    line.segs.append(Seg(line, start, i - 1))
                    start = i
            lines.append(line)
    return lines, len(pdf.pages)


def boilerplate(lines: list[Line], npages: int) -> set[int]:
    """Running headers/footers: lines in the top 15 % / bottom 13 % of a page whose text (digits
    masked) repeats at the same height on several pages (3, or 2 in documents of up to 5 pages)."""
    if npages < 2:
        return set()
    zone = [ln for ln in lines if ln.top < 0.15 * ln.height or ln.top > 0.87 * ln.height]
    pages_by_key: dict[tuple, set[int]] = defaultdict(set)
    for ln in zone:
        pages_by_key[(re.sub(r"\d+", "#", ln.text), round(ln.top / 8))].add(ln.page)  # same text, same height
    keys = {k for k, pages in pages_by_key.items() if len(pages) >= min(3, max(2, npages // 2))}
    return {ln.gi for ln in zone if (re.sub(r"\d+", "#", ln.text), round(ln.top / 8)) in keys}


def span_text(lines: list[Line], start: tuple[int, int], end: tuple[int, int]) -> str:
    """Words from (line gi, word index) to (line gi, word index), inclusive, in page order."""
    (l0, w0), (l1, w1) = start, end
    out = []
    for gi in range(l0, l1 + 1):
        words = lines[gi].words
        a = w0 if gi == l0 else 0
        b = w1 if gi == l1 else len(words) - 1
        out += [w["text"] for w in words[a : b + 1]]
    return " ".join(out)


# ---------------------------------------------------------------------------------------
# Sections, columns, rows
# ---------------------------------------------------------------------------------------
NUMERIC_START = re.compile(r"^(?:[•●▪]\s*)?(?:P|LT)?\d")
SUB_LABEL = re.compile(r"^[-–]\s*\S")


def is_header_text(text: str) -> bool:
    head = text.split("(")[0].strip()
    letters = re.sub(r"[^A-Za-z]", "", head)
    return len(letters) >= 4 and head == head.upper() and not re.match(r"^[\d•]", head)


def numeric(seg_text: str) -> bool:
    return bool(re.search(r"\d", seg_text))


@dataclass
class Column:
    x0: float
    x1: float
    title: str | None


@dataclass
class Section:
    title: str
    header: Line
    lines: list = field(default_factory=list)
    columns: list = field(default_factory=list)
    boundary: float = 0.0
    label_x: float = 0.0
    extra_titles: list = field(default_factory=list)  # second column-title line
    extra_checked: bool = False

    @property
    def kind(self) -> str:
        t = self.title.upper()
        if re.search(r"FEATURES|OPTIONS|PACKAGES?\b|COLORS|WARRANTY|AUDIO|SAFETY|SECURITY|MULTIMEDIA|ACCESSOR|"
                     r"CONVENIENCE|BY GRADE|PRICING|MSRP|ENTUNE|CONNECTED|APPEARANCE|TRIM LEVELS", t):
            return "features"
        if "BATTERY" in t:
            return "battery"
        if re.search(r"DRIVETRAIN|TRANSMISSION|DRIVE ?LINE", t):
            return "drivetrain"
        if "MOTOR" in t and "ENGINE" not in t:
            return "motor"
        if "ENGINE" in t:
            return "engine"
        if "HYBRID" in t or re.search(r"SYSTEM$", t):
            return "hybrid_system"
        return "other"


@dataclass
class Cell:
    seg: Seg
    col: int
    sub: str | None = None  # grade header text above the value
    sub_seg: Seg | None = None


@dataclass
class Row:
    section: Section
    labels: list  # Segs
    parent: "Row | None" = None
    cells: list = field(default_factory=list)
    dash_children: bool = False
    band: tuple | None = None

    @property
    def own(self) -> str:
        return norm(" ".join(s.text for s in self.labels))

    @property
    def label(self) -> str:
        if not self.parent:
            return self.own
        # "Steering - Type" on the main line: the sub-rows below hang under "Steering"
        prefix = re.split(r"\s+[-–]\s+", self.parent.own, maxsplit=1)[0]
        return norm(prefix + " " + self.own)


def build_sections(lines: list[Line], skip: set[int]) -> list[Section]:
    """A section starts at an upper-case title at the label margin; the other cells of the
    title line (if any) are upper-case column titles ("FOUR-CYLINDER", "V6", "LE")."""
    body = [ln for ln in lines if ln.segs and ln.gi not in skip]
    page_left: dict[int, float] = {}
    for ln in body:
        page_left[ln.page] = min(page_left.get(ln.page, 1e9), ln.segs[0].x0)

    # Spec sheets in matrix form repeat the model column titles in every section title line
    # ("Engine | RX 350 (FWD/AWD) | RX 350h AWD | RX 500h AWD"): such a repeated title tuple
    # marks a section title even when the title itself is not upper case.
    def title_key(ln: Line) -> tuple | None:
        rest = ln.segs[1:]
        if not rest or len(ln.segs[0].text.split()) > 5 or re.search(r"\d", ln.segs[0].text):
            return None
        for s in rest:
            if not re.search(r"[A-Za-z]{2}", s.text) or NON_VALUES.match(s.text) or ":" in s.text or "@" in s.text:
                return None
        return tuple(re.sub(r"\s+", "", s.text).lower() for s in rest)

    repeated = Counter(k for k in (title_key(ln) for ln in body) if k)
    sections: list[Section] = []
    current = None
    for i, ln in enumerate(body):
        first = ln.segs[0]
        nxt = body[i + 1] if i + 1 < len(body) else None
        # a title sits at the page margin or directly above labels that start where it starts
        at_margin = first.x0 <= page_left[ln.page] + 12 or (
            first.x0 <= page_left[ln.page] + 60
            and nxt is not None and nxt.page == ln.page and abs(nxt.segs[0].x0 - first.x0) <= 4
        )
        rest_ok = all(not re.search(r"[a-z]", s.text) and not re.match(r"^[\d•.,/-]", s.text) for s in ln.segs[1:])
        key = title_key(ln)
        matrix_title = at_margin and key is not None and repeated[key] >= 2
        if (at_margin and is_header_text(first.text) and rest_ok) or matrix_title:
            if current is not None and not current.lines and len(ln.segs) == 1 and ln.gi == current.header.gi + 1:
                current.title = norm(current.title + " " + first.text)  # title wrapped onto two lines
                continue
            current = Section(first.text, ln)
            sections.append(current)
            continue
        if current is not None:
            current.lines.append(ln)
    return sections


def layout_section(sec: Section, doc_boundary: float | None) -> None:
    sec.label_x = sec.header.segs[0].x0
    samples = []
    for ln in sec.lines:
        s0 = ln.segs[0]
        if abs(s0.x0 - sec.label_x) <= 8 and len(ln.segs) >= 2:
            for s in ln.segs[1:]:
                if not SUB_LABEL.match(s.text):
                    samples.append(round(s.x0 / 4) * 4)
                    break
    counts = Counter(samples)
    boundary = None
    if counts:
        value, n = counts.most_common(1)[0]
        if n >= 2 or doc_boundary is None:
            boundary = float(value)
    if boundary is None:
        boundary = doc_boundary if doc_boundary is not None else sec.label_x + 150
    # column titles in the header row, kept only when values sit under them
    titles = [s for s in sec.header.segs[1:]]
    value_segs = [s for ln in sec.lines for s in ln.segs if s.x0 >= min([boundary] + [t.x0 for t in titles]) - 10]
    real = []
    for t in titles:
        if any(abs(v.x0 - t.x0) <= 15 or abs(v.center - t.center) <= 20 for v in value_segs):
            real.append(t)
    if real:
        first_col = min(t.x0 for t in real)
        if len(real) >= 2 or boundary > first_col:
            boundary = first_col  # the value area starts at the first titled column
        sec.columns = [Column(t.x0, t.x1, norm(t.text)) for t in real]
        # a second title line ("Premium/Premium+ | Luxury/Luxury+ | Overtrail/Overtrail+")
        while sec.lines and len(sec.columns) >= 2 and not sec.extra_checked:
            ln = sec.lines[0]
            if ln.segs[0].x0 < boundary - 10 or any(re.search(r"\d", s.text) for s in ln.segs):
                break
            if not all(any(abs(s.x0 - c.x0) <= 15 for c in sec.columns) for s in ln.segs):
                break
            sec.extra_titles.append(sec.lines.pop(0))
        sec.extra_checked = True
        for ln in sec.extra_titles:
            for s in ln.segs:
                col = min(sec.columns, key=lambda c: abs(s.x0 - c.x0))
                col.title = norm(f"{col.title} {s.text}")
    else:
        sec.columns = [Column(boundary, boundary, None)]
        if len(titles) >= 2 and min(t.x0 for t in titles) > sec.label_x + 80:
            # matrix sheet section whose values are all merged across the model columns: the value
            # area still starts at the first model column (sub-labels such as "(in.)" sit left of it)
            boundary = min(t.x0 for t in titles)
            sec.columns = [Column(boundary, boundary, None)]
    sec.boundary = boundary


def column_of(sec: Section, seg: Seg) -> int:
    if len(sec.columns) == 1:
        return 0
    best, dist = 0, None
    for i, col in enumerate(sec.columns):
        if col.x0 - 25 > seg.x0:
            continue
        d = abs(seg.x0 - col.x0)
        if dist is None or d < dist:
            best, dist = i, d
    return best


def label_continues(text: str, row: Row) -> bool:
    own = " ".join(s.text for s in row.labels)
    if own.count("(") > own.count(")"):
        return True
    if own.endswith(("-", "/", ",", "&", " and", " of")):
        return True
    return bool(re.match(r"^[(a-z]", text))


def build_rows(sec: Section) -> list[Row]:
    rows: list[Row] = []
    main: Row | None = None
    cur: Row | None = None
    lines = sec.lines
    sub_header: tuple[Row, list[Seg]] | None = None
    pending: list[tuple[Line, list[Seg]]] = []  # value lines that belong to a later table row band
    tol = 8.0

    def zone(ln: Line, boundary: float | None = None) -> tuple[list[Seg], list[Seg]]:
        if boundary is None:  # under a grade header the numbers may start a little left of the column
            boundary = sub_header[2] if sub_header is not None and sub_header[0] is main else sec.boundary
        # a cell that is not the first of its line and starts just left of the value column is a value
        # (centred grade titles such as "L" over "3,241")
        is_val = [s.x0 >= boundary - tol or (i > 0 and s.x0 >= boundary - 20) for i, s in enumerate(ln.segs)]
        return ([s for s, v in zip(ln.segs, is_val) if not v], [s for s, v in zip(ln.segs, is_val) if v])

    def number_words(segs: list[Seg]) -> list[Seg]:
        """'3,241 3,296' printed closely under 'L  LE': one Seg per number."""
        out = []
        for s in segs:
            if s.w1 > s.w0 and all(re.fullmatch(NUM, w["text"]) for w in s.words):
                out += [Seg(s.line, i, i) for i in range(s.w0, s.w1 + 1)]
            else:
                out.append(s)
        return out

    def add_values(row: Row, ln: Line, vsegs: list[Seg]) -> None:
        if sub_header is not None and sub_header[0] is (row.parent or row):
            vsegs = number_words(vsegs)
        for s in vsegs:
            sub, sub_seg = None, None
            if sub_header is not None and sub_header[0] is (row.parent or row) and numeric(s.text):
                h = min(sub_header[1], key=lambda h: abs(h.center - s.center))
                if abs(h.center - s.center) <= 18:
                    sub, sub_seg = norm(h.text), h
            col = column_of(sec, s)
            if len(sec.columns) >= 2 and len(vsegs) == 1 and all(abs(s.x0 - c.x0) > 6 for c in sec.columns):
                col = -1  # one value centred over several titled columns: a merged cell valid for all of them
            row.cells.append(Cell(s, col, sub, sub_seg))

    def flush(new_band) -> None:
        nonlocal pending
        if pending:
            target = None
            if new_band is not None and pending[0][0].band == new_band:
                return  # attached by the caller to the new row
            target = cur
            if target is not None:
                for pl, ps in pending:
                    add_values(target, pl, ps)
            pending = []

    for idx, ln in enumerate(lines):
        if ln.text.startswith("*") and len(ln.segs) == 1:
            continue  # footnote
        lsegs, vsegs = zone(ln)
        for s in lsegs:
            text = s.text
            if abs(s.x0 - sec.label_x) <= 8:
                nxt = lines[idx + 1] if idx + 1 < len(lines) else None
                if cur is not None and not cur.cells and label_continues(text, cur):
                    cur.labels.append(s)
                elif cur is not None and cur.cells and re.match(r"^[(a-z]", text) and ln.band == cur.band:
                    cur.labels.append(s)
                elif main is not None and main.own.count("(") > main.own.count(")") and not vsegs and len(lsegs) == 1:
                    main.labels.append(s)  # "Curb Weight (Emission" / "Regulation)"
                elif main is not None and cur is not None and cur.cells and not vsegs and len(lsegs) == 1 \
                        and ln.band is None and nxt is not None and abs(nxt.segs[0].x0 - sec.label_x) <= 8 \
                        and not is_header_text(text):
                    main.labels.append(s)  # "Min. Running Ground" / "Clearance" (wrapped main label)
                else:
                    flush(ln.band)
                    main = cur = Row(sec, [s], band=ln.band)
                    rows.append(cur)
                    if pending and pending[0][0].band == ln.band:
                        for pl, ps in pending:
                            add_values(cur, pl, ps)
                    pending = []
                    if sub_header and sub_header[0] is not main:
                        sub_header = None
            else:
                if SUB_LABEL.match(text) and main is not None:
                    flush(None)
                    cur = Row(sec, [s], parent=main, band=ln.band)
                    main.dash_children = True
                    rows.append(cur)
                elif cur is None:
                    main = cur = Row(sec, [s], band=ln.band)
                    rows.append(cur)
                elif main is not None and not main.dash_children and vsegs and not label_continues(text, cur) \
                        and (cur is not main or not cur.cells or len(sec.columns) >= 2 or re.match(r"^\S+$", text)):
                    flush(None)
                    # "1st", "2nd" under "Gear Ratios"; "Length (in.)" under "Overall" in matrix sheets
                    cur = Row(sec, [s], parent=main, band=ln.band)
                    rows.append(cur)
                else:
                    cur.labels.append(s)
        if not vsegs:
            continue
        if cur is None:
            continue
        if not lsegs and ln.band is not None and cur.band is not None and ln.band != cur.band:
            pending.append((ln, vsegs))
            continue
        # grade header line inside a row: >= 2 short non-numeric cells over numbers
        if len(vsegs) >= 2 and all(not numeric(s.text) and len(s.text) <= 15 and len(s.text.split()) <= 3
                                   and not NON_VALUES.match(s.text) for s in vsegs):
            relaxed = min(sec.boundary, min(h.x0 for h in vsegs) - 15)
            nxt = next((l2 for l2 in lines[idx + 1 : idx + 3] if zone(l2, relaxed)[1]), None)
            if nxt is not None:
                nl, nv = zone(nxt, relaxed)
                nv = number_words(nv)
                if (not nl or (lsegs and all(SUB_LABEL.match(x.text) for x in nl))) and len(nv) >= 2                         and all(numeric(s.text) for s in nv)                         and all(any(abs(n.center - h.center) <= 18 for h in vsegs) for n in nv):
                    sub_header = (main, vsegs, relaxed)
                    continue
        add_values(cur, ln, vsegs)
    flush(None)
    return rows


# ---------------------------------------------------------------------------------------
# Label -> fact key
# ---------------------------------------------------------------------------------------
NUM_KEYS = {
    "power_hp", "system_power_hp", "torque_lb_ft", "engine_displacement_cc", "turning_circle_ft", "wheel_size_in",
    "length_in", "width_in", "height_in", "wheelbase_in", "track_front_in", "track_rear_in", "ground_clearance_in",
    "curb_weight_lb", "cargo_cu_ft", "cargo_max_cu_ft", "passenger_volume_cu_ft", "fuel_tank_gal", "seats",
    "towing_lb", "track_pair",
}
TEXT_KEYS = {
    "engine_description", "valvetrain", "injection", "transmission_description", "front_suspension",
    "rear_suspension", "front_brakes", "rear_brakes", "steering", "electric_motor",
}


UNIT_IN_LABEL = re.compile(
    r"\(\s*(?:in|lbs?|cu\.?\s*ft|ft|gal|mm|hp|kW|lb\.?\s*-?\s*ft)[^)]*\)\*?|"
    r"\b(?:inches|gallons|persons?|lbs\.|cu\.\s*ft\s*\.?|degrees|hp\s*@\s*rpm|lb\.?-ft\.?\s*@\s*rpm|in\.)(?=\s|$)",
    re.I,
)


def key_for(label: str, sec: Section, own: str = "") -> str | None:
    lab = norm(UNIT_IN_LABEL.sub(" ", norm(label).replace("–", "-").replace("—", "-")))
    kind = sec.kind
    if kind == "features" or len(lab) > 90:
        return None
    own = norm(UNIT_IN_LABEL.sub(" ", own))
    # matrix sheets list engine / motor outputs as sub-rows of "Total System Output"
    if own and re.match(r"^Engine\b", own) and re.search(r"\bhp\b|horsepower|output", label, re.I):
        return "power_hp"
    if own and re.match(r"^Engine\b", own) and re.search(r"lb\.?\s*-?\s*ft|torque", label, re.I):
        return "torque_lb_ft"
    if own and re.search(r"\bMotor\b", own) and re.search(r"\bhp\b|lb\.?\s*-?\s*ft|output|torque", label, re.I):
        return "electric_motor"
    if re.search(r"^Curb\s+Weight", lab, re.I) and re.search(r"\b(?:Front|Rear)\b", lab, re.I):
        return None  # axle weights
    if re.search(r"Towing", lab, re.I) and re.search(r"without\s+brake|unbraked", lab, re.I):
        return None
    if re.search(r"\bswept\b|\bthickness only\b|stabilizer|\bratio\b|\bturns\b|lock to lock|lock-to-", lab, re.I) \
            and not re.search(r"compression", lab, re.I):
        if not re.search(r"Turning", lab, re.I):
            return None
    if kind == "battery":
        return None
    if kind == "motor" or re.search(r"\bmotor\b|\bMG\d\b", lab, re.I):
        if re.search(r"type|output|power|torque|horsepower|voltage|motor", lab, re.I):
            return "electric_motor"
        return None
    if re.search(r"system|combined|total", lab, re.I) and re.search(r"horsepower|\bpower\b|output", label, re.I) \
            or (re.search(r"system|combined", lab, re.I) and re.search(r"\(\s*hp\s*\)", label, re.I)):
        return "system_power_hp"
    if kind == "hybrid_system" and re.search(r"horsepower|net power", lab, re.I) and not re.search(r"engine", lab, re.I):
        return "system_power_hp"
    if re.search(r"^(?:Engine\s+)?(?:Net\s+|Max(?:imum)?\.?\s+)?Horsepower\b|^Horsepower|^Engine\s+Output|^Output\b", lab, re.I):
        return "power_hp"
    if re.search(r"^(?:Engine\s+)?(?:Net\s+|Max(?:imum)?\.?\s+)?Torque\b", lab, re.I):
        return "torque_lb_ft"
    if re.search(r"^Displacement\b", lab, re.I):
        return "engine_displacement_cc"
    if re.search(r"^Bore\s*(?:x|×|and)\s*Stroke", lab, re.I):
        return "bore_stroke"
    if re.search(r"^Compression\s+Ratio", lab, re.I):
        return "compression_ratio"
    if re.search(r"^Valve\s*train|^Valve\s+Mechanism", lab, re.I):
        return "valvetrain"
    if re.search(r"^(?:Fuel\s+(?:Injection\s+)?(?:System|Injection|Delivery)|Injection(?:\s+System)?)$", lab, re.I):
        return "injection"
    if re.search(r"^(?:Designation|Engine\s+(?:Code|Designation))$", lab, re.I) and kind in ("engine", "other"):
        return "engine_code"
    if kind in ("engine", "other") and re.search(r"^(?:Engine\s+)?Type(?:,?\s*(?:and\s+)?Materials?)?$|^Type/Materials$", lab, re.I):
        return "engine_description"
    if re.search(r"^Transmission(?:\s+Type)?$|^Transaxle(?:\s+Type)?$", lab, re.I):
        return "transmission_description"
    if re.search(r"^(?:Suspension(?:\s+Type)?\s*-?\s*Front|Front\s+Suspension)\b", lab, re.I):
        return "front_suspension"
    if re.search(r"^(?:Suspension(?:\s+Type)?\s*-?\s*Rear|Rear\s+Suspension)\b", lab, re.I):
        return "rear_suspension"
    if re.search(r"^(?:Brakes?(?:\s+Type)?\s*-?\s*Front|Front\s+Brakes?)\b(?!.*(?:Swept|Area|Thickness$))", lab, re.I):
        return "front_brakes"
    if re.search(r"^(?:Brakes?(?:\s+Type)?\s*-?\s*Rear|Rear\s+Brakes?)\b(?!.*(?:Swept|Area|Thickness$))", lab, re.I):
        return "rear_brakes"
    if re.search(r"Turning\s+(?:Circle|Diameter)", lab, re.I) and not re.search(r"radius|wall", lab, re.I):
        return "turning_circle_ft"
    if re.search(r"Turning\s+(?:Circle\s+)?Radius", lab, re.I):
        return "turning_radius"  # reported in review, not converted
    if re.search(r"^Steering(?:\s*-\s*Type|\s+Type|\s+System)?$", lab, re.I):
        return "steering"
    if re.search(r"^Tires?(?:\s+Size)?(?:\s*/\s*Type)?$|^Tire\s+Size\b", lab, re.I) and not re.search(r"spare", lab, re.I):
        return "tires"
    if re.search(r"^Wheels?(?:\s+Size)?(?:\s*/\s*Type)?$|^Wheel\s+Size\b", lab, re.I):
        return "wheel_size_in"
    if re.search(r"^Wheelbase\b", lab, re.I):
        return "wheelbase_in"
    if re.search(r"^(?:Overall\s+)?Length\b", lab, re.I):
        return "length_in"
    if re.search(r"^(?:Overall\s+)?Width\b", lab, re.I):
        return "width_in"
    if re.search(r"^(?:Overall\s+|Unload(?:ed)?\s+)?Height\b", lab, re.I):
        return "height_in"
    if re.search(r"^(?:Tread|Track)(?:\s+Width)?\s*(?:-\s*)?\(?\s*Front\s*/\s*Rear\s*\)?", lab, re.I):
        return "track_pair"
    if re.search(r"^(?:Tread|Track)(?:\s+Width)?\s*(?:-\s*)?\(?Front\)?$|^Front\s+(?:Tread|Track)", lab, re.I):
        return "track_front_in"
    if re.search(r"^(?:Tread|Track)(?:\s+Width)?\s*(?:-\s*)?\(?Rear\)?$|^Rear\s+(?:Tread|Track)", lab, re.I):
        return "track_rear_in"
    if re.search(r"Ground\s+Clearance", lab, re.I):
        return "ground_clearance_in"
    if re.search(r"^Curb\s+Weight", lab, re.I):
        return "curb_weight_lb"
    if re.search(r"Cargo\s+(?:Volume|Capacity|Space|Area)", lab, re.I):
        return "cargo"
    if re.search(r"Passenger\s+Volume", lab, re.I):
        return "passenger_volume_cu_ft"
    if re.search(r"^Fuel\s+(?:Tank\s+)?Capacity|^Fuel\s+Tank\b", lab, re.I):
        return "fuel_tank_gal"
    if re.search(r"^Seating(?:\s+Capacity)?\b|^Passenger\s+Capacity", lab, re.I):
        return "seats"
    if re.search(r"Towing", lab, re.I) and not re.search(r"tongue|hitch|package", lab, re.I):
        return "towing_lb"
    return None


# ---------------------------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------------------------
NUM = r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)"
CONDITION = re.compile(
    r"\bw/o\b|\bw/|\b(?:with|without|mirrors?|antenna|wheels?|moonroof|sunroof|roof|seats?|folded|up|down|standard|"
    r"optional|option|stand-alone|package|row|behind|shade|cargo|third|second|first|max(?:imum)?|panoramic|"
    r"min(?:imum)?|est(?:imated)?|approx\.?|unloaded|loaded|base|run[- ]flat|spare|tire|tires)\b|\d+\s*(?:-?in\.?|”|\")",
    re.I,
)
UNIT_ALT = re.compile(
    r"^\s*(?:" + NUM + r")\s*(?:mm|cm|cm2|cm\^?3|kg|L|liters?|km/hr?\.?|kW|Nm|N·m|N-m|kPa)\b", re.I
)
UNITS = {
    "in": r"(?:in\.?|inch(?:es)?|”|\"|-in\.?)?",
    "lb": r"(?:lbs?\.?|pounds)?",
    "cuft": r"(?:cu\.?\s*ft\.?|cubic\s+feet|ft3|ft\.3)?",
    "gal": r"(?:gal\.?|gallons?)?",
    "ft": r"(?:ft\.?|feet)?",
    "seats": r"(?:passengers?|occupants?|people|seats?)?",
}
KEY_UNIT = {
    "length_in": "in", "width_in": "in", "height_in": "in", "wheelbase_in": "in", "track_front_in": "in",
    "track_rear_in": "in", "ground_clearance_in": "in", "track_pair": "in", "curb_weight_lb": "lb",
    "towing_lb": "lb", "cargo_cu_ft": "cuft", "cargo_max_cu_ft": "cuft", "passenger_volume_cu_ft": "cuft",
    "cargo": "cuft", "fuel_tank_gal": "gal", "turning_circle_ft": "ft", "seats": "seats",
}
NON_VALUES = re.compile(r"^(?:N/?A|TBD|TBA|—|-|–|Not\s+(?:available|applicable|recommended)|None|Standard|Optional)\.?$", re.I)


def to_number(text: str):
    text = text.replace(",", "")
    if text.startswith("."):
        text = "0" + text
    return float(text) if "." in text else int(text)


@dataclass
class Item:
    cells: list  # Cells (one per line)

    @property
    def text(self) -> str:
        return norm(" ".join(c.seg.text for c in self.cells))


def split_items(cells: list[Cell], key: str) -> list[Item]:
    items: list[Item] = []
    text_key = key in TEXT_KEYS or key in ("bore_stroke", "compression_ratio", "engine_code")
    for c in cells:
        t = c.seg.text
        bullet = bool(re.match(r"^[•●▪]", t))
        if not items:
            items.append(Item([c]))
        elif items[-1].text.count("(") > items[-1].text.count(")") and c.col == items[-1].cells[-1].col:
            items[-1].cells.append(c)  # "62.9 (62.5 in. w/18” or" / "19” wheels)"
        elif text_key:
            if bullet or re.match(r"^(?:Front|Rear)\s*:", t):
                items.append(Item([c]))
            else:
                items[-1].cells.append(c)
        elif bullet or NUMERIC_START.match(t) or " = " in t or c.sub != items[-1].cells[-1].sub \
                or re.match(r"^[^:@\d]{1,40}:\s*\d", t):  # "Bench: 7" / "Captain’s Chairs: 6"
            items.append(Item([c]))
        else:
            items[-1].cells.append(c)
    return items


def qualifier(text: str) -> tuple[str, str | None]:
    """(value text, qualifier) for "<qualifier> = <value>", "<value> (<qualifier>)", "• L 4,145"."""
    t = re.sub(r"^[•●▪]\s*", "", text).strip()
    depth, eq_outside = 0, False
    for ch in t:
        depth += (ch == "(") - (ch == ")")
        if ch == "=" and depth == 0:
            eq_outside = True
            break
    if eq_outside:
        left, right = re.split(r"\s*=\s*", t, maxsplit=1)
        return right.strip(), left.strip() or None
    found = re.search(r"\(([^()]*)\)\s*\.?\s*$", t)
    if found and not UNIT_ALT.match(found.group(1)) and re.search(r"[A-Za-z]", found.group(1)):
        return t[: found.start()].strip(), found.group(1).strip()
    colon = re.match(r"^([^:@]{1,40}?)\*{0,2}\s*:\s*((?:" + NUM + r").*)$", t)  # "FWD: 8.19", "3rd Row Folded: 40.2"
    if colon and re.search(r"[A-Za-z]", colon.group(1)):
        return colon.group(2).strip(), colon.group(1).strip().rstrip("*")
    lead = re.match(r"^([A-Za-z][^\d=]*?)\s+((?:" + NUM + r").*)$", t)
    if lead and not re.match(r"^(?:approx|est|up to|max|min)", lead.group(1), re.I):
        return lead.group(2).strip(), lead.group(1).strip()
    return t, None


def classify_qualifier(q: str | None) -> tuple[str | None, str | None]:
    """(engine/trim text, condition text)."""
    if not q:
        return None, None
    if CONDITION.search(q) and not re.search(r"\bgrades?\b|\bAll\b|FWD|AWD|4WD|2WD|RWD", q):
        return None, q
    return q, None


def label_pair(label: str) -> tuple[str, str] | None:
    found = re.search(r"\b([A-Za-z0-9]+)\s*/\s*([A-Za-z0-9]+)\b", label)
    if found and not re.search(r"lb|ft|cu|in|mpg|hwy", found.group(0), re.I):
        return found.group(1), found.group(2)
    return None


def parse_number_with_unit(value: str, unit: str) -> list[str]:
    """Numbers of `value` that carry the expected unit (or no unit); [] when another unit."""
    out = []
    for m in re.finditer(r"(" + NUM + r")\s*(" + UNITS[unit] + r")", value):
        after = value[m.end() : m.end() + 6]
        if re.match(r"\s*(?:mm|cm|kg|L\b|liters?|km|kW|Nm|mph|sec|%|x\b|×)", after, re.I):
            continue
        out.append(m.group(1))
    return out


def facts_from_item(key: str, label: str, item: Item, col_title: str | None) -> tuple[list[dict], list[str]]:
    """Facts (without quote/page) and review reasons for one value item."""
    text = item.text
    sub = item.cells[0].sub
    facts: list[dict] = []
    reasons: list[str] = []
    value_text, qual = qualifier(text)
    trim, cond = classify_qualifier(qual)
    if key in KEY_UNIT or key in ("power_hp", "system_power_hp", "torque_lb_ft", "wheel_size_in", "tires"):
        if re.search(r"\([^()]*=[^()]*\)", text):
            return [], [f"value with an exception in parentheses: {text!r}"]
        if qual and key in KEY_UNIT and re.match(r"^\s*" + NUM + r"\s*(?:in\b|in\.|lbs?\b|lbs?\.|cu\.|gal|ft\b|ft\.)", qual):
            return [], [f"second value in parentheses: {text!r}"]  # "62.9 (62.5 in. w/18” or 19” wheels)"
    unit_label = label.lower()
    if key in ("engine_description", "valvetrain", "injection", "transmission_description", "front_suspension",
               "rear_suspension", "front_brakes", "rear_brakes", "steering", "electric_motor", "engine_code"):
        value = norm(re.sub(r"^[•●▪]\s*", "", text))
        trim = None
        if qual and "=" in text and norm(value_text) != value:
            value, trim = norm(value_text), qual  # "L → PLTM (FWD/AWD) = Solid Disc"
        if NON_VALUES.match(value) and key not in ("front_brakes", "rear_brakes"):
            return [], []
        facts.append({"key": key, "value": value, "trim": trim, "cond": None})
        return facts, reasons
    if NON_VALUES.match(value_text) or not re.search(r"\d", value_text):
        if re.search(r"\d", text) and key not in ("seats",):
            reasons.append(f"no number in value part: {text!r}")
        return [], reasons
    rpm_tail = r"(?:\s*@\s*(" + NUM + r"(?:\s*[-–]\s*" + NUM + r")?))?\s*$"
    if key in ("power_hp", "system_power_hp") and re.search(r"\bhp\b|horsepower", unit_label) \
            and not re.search(r"hp|horsepower", value_text, re.I):
        m = re.match(r"^\s*(" + NUM + r")" + rpm_tail, value_text)  # unit in the label: "Output hp @ rpm | 275 @ 6,000"
        if not m:
            return [], [f"value not readable with unit from label: {text!r}"]
        facts.append({"key": key, "value": to_number(m.group(1)), "trim": trim, "cond": cond})
        if m.group(2) and key == "power_hp":
            facts.append({"key": "power_rpm", "value": norm(m.group(2)), "trim": trim, "cond": cond})
        return facts, reasons
    if key == "torque_lb_ft" and re.search(r"lb\.?\s*-?\s*ft", unit_label) and not re.search(r"lb|ft", value_text, re.I):
        m = re.match(r"^\s*(" + NUM + r")" + rpm_tail, value_text)
        if not m:
            return [], [f"value not readable with unit from label: {text!r}"]
        facts.append({"key": key, "value": to_number(m.group(1)), "trim": trim, "cond": cond})
        if m.group(2):
            facts.append({"key": "torque_rpm", "value": norm(m.group(2)), "trim": trim, "cond": cond})
        return facts, reasons
    if key == "power_hp" or key == "system_power_hp":
        m = re.search(r"(" + NUM + r")\s*(?:hp|horsepower|HP)\b", value_text)
        if not m:
            if re.search(r"\bkW\b", value_text) and not re.search(r"hp|horsepower", value_text, re.I):
                return [], []
            reasons.append(f"no hp value: {text!r}")
            return [], reasons
        facts.append({"key": key, "value": to_number(m.group(1)), "trim": trim, "cond": cond})
        rpm = re.search(r"@\s*(" + NUM + r"(?:\s*[-–]\s*" + NUM + r")?)\s*rpm", value_text, re.I)
        if rpm and key == "power_hp":
            facts.append({"key": "power_rpm", "value": norm(rpm.group(1)), "trim": trim, "cond": cond})
        return facts, reasons
    if key == "torque_lb_ft":
        m = re.search(r"(" + NUM + r")\s*(?:lbs?\.?[\s\-‐‑–]*ft\.?|pound-feet|ft\.?[\s\-‐‑–]*lbs?\.?)", value_text, re.I)
        if not m:
            if re.search(r"\bN·?m\b|\bNm\b", value_text):
                return [], []
            reasons.append(f"no lb-ft value: {text!r}")
            return [], reasons
        facts.append({"key": key, "value": to_number(m.group(1)), "trim": trim, "cond": cond})
        rpm = re.search(r"@\s*(" + NUM + r"(?:\s*[-–]\s*" + NUM + r")?)\s*rpm", value_text, re.I)
        if rpm:
            facts.append({"key": "torque_rpm", "value": norm(rpm.group(1)), "trim": trim, "cond": cond})
        return facts, reasons
    if key == "engine_displacement_cc":
        m = re.search(r"(" + NUM + r")\s*(?:cc|cm\^?3|cm³)", text)
        if m:
            facts.append({"key": key, "value": to_number(m.group(1)), "trim": trim, "cond": cond})
        elif re.search(r"cu\.?\s*in\.?\s*\(\s*(?:cm\s*3|cc)\s*\)", unit_label):
            # label "Displacement cu. in. (cm3)", value "146.03 (2,393)": the bracketed number is the cm3 value
            b = re.fullmatch(r"\s*" + NUM + r"\s*\(\s*(" + NUM + r")\s*\)\s*", text)
            if b:
                facts.append({"key": key, "value": to_number(b.group(1)), "trim": trim, "cond": cond})
            else:
                reasons.append(f"displacement not readable: {text!r}")
        return facts, reasons
    if key == "bore_stroke":
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(mm|in\.?)?\s*[x×]\s*(\d+(?:\.\d+)?)\s*(mm|in\.?|\(mm\)|\(in\.?\))?", text):
            unit = (m.group(4) or m.group(2) or "").strip("().")
            if unit not in ("mm", "in"):
                tail = text[m.end() : m.end() + 8]
                unit = "mm" if re.match(r"\s*\(?mm", tail) else ("in" if re.match(r"\s*\(?in", tail) else "")
            if unit not in ("mm", "in"):  # unit given in the label: "Bore x Stroke (in.)" / "Bore x Stroke in."
                lab_unit = re.search(r"\(\s*(mm|in)\.?\s*\)|\b(mm|in)\.?\s*$", unit_label)
                unit = (lab_unit.group(1) or lab_unit.group(2)) if lab_unit else ""
            if unit in ("mm", "in"):
                facts.append({"key": f"bore_stroke_{unit}", "value": f"{m.group(1)} x {m.group(3)}", "trim": None,
                              "cond": None})
            else:
                reasons.append(f"bore x stroke without unit: {text!r}")
        return facts, reasons
    if key == "compression_ratio":
        m = re.search(r"(\d+(?:\.\d+)?)\s*:\s*1\b", text)
        if m:
            facts.append({"key": key, "value": f"{m.group(1)}:1", "trim": trim, "cond": cond})
        return facts, reasons
    if key == "tires":
        sizes = re.findall(r"\b(?:P|LT)?\d{3}/\d{2}\s?Z?R\s?F?\d{2}(?:\s+\d{2,3}[A-Z]{1,2}\b)?", value_text)
        if not sizes:
            reasons.append(f"no tire size: {text!r}")
        for size in sizes:
            facts.append({"key": "tires", "value": norm(size), "trim": trim, "cond": cond})
        return facts, reasons
    if key == "wheel_size_in":
        head = value_text.split("(")[0].split(";")[0]
        sized = re.match(r"^\s*(" + NUM + r")\s*(?:x|×)\s*(" + NUM + r")", head)  # "17 x 7.0 in." / "6.5 x 16 in."
        inch = re.match(r"^\s*(" + NUM + r")\s*(?:-?\s*in\b\.?|-inch|”|\")", head)  # "18-in. Painted Alloy"
        nums = list(sized.groups()) if sized else ([inch.group(1)] if inch else re.findall(NUM, head))
        dia = [n for n in nums if 13 <= float(n.replace(",", "")) <= 24]
        if len(dia) == 1:
            facts.append({"key": key, "value": to_number(dia[0]), "trim": trim, "cond": cond})
        else:
            reasons.append(f"wheel size not readable: {text!r}")
        return facts, reasons
    if key in ("cargo", "track_pair") or key in KEY_UNIT:
        unit = KEY_UNIT[key]
        nums = parse_number_with_unit(value_text, unit)
        pair = re.search(r"(" + NUM + r")\s*(?:in\.|in\b|”|lbs?\.?)?\s*/\s*(" + NUM + r")", value_text)
        if pair:
            hint = label_pair(label)
            if key == "track_pair" or (hint and hint[0].lower() == "front" and hint[1].lower() == "rear"):
                if key in ("track_pair",):
                    facts.append({"key": "track_front_in", "value": to_number(pair.group(1)), "trim": trim, "cond": cond})
                    facts.append({"key": "track_rear_in", "value": to_number(pair.group(2)), "trim": trim, "cond": cond})
                    return facts, reasons
            if hint:
                for v, h in ((pair.group(1), hint[0]), (pair.group(2), hint[1])):
                    facts.append({"key": key, "value": to_number(v), "trim": trim, "cond": cond, "pair": h})
                return facts, reasons
            reasons.append(f"two values without labels: {text!r}")
            return [], reasons
        if key == "track_pair":
            reasons.append(f"front/rear label but one value: {text!r}")
            return [], reasons
        if not nums:
            reasons.append(f"no value with unit {unit}: {text!r}")
            return [], reasons
        if len(nums) > 1:
            reasons.append(f"several numbers: {text!r}")
            return [], reasons
        if key == "seats" and not re.fullmatch(r"\d+", nums[0]):
            reasons.append(f"seating not an integer: {text!r}")
            return [], reasons
        facts.append({"key": key, "value": to_number(nums[0]), "trim": trim, "cond": cond})
        return facts, reasons
    return facts, reasons


def cargo_key(label: str, cond: str | None) -> str:
    text = f"{label} {cond or ''}"
    if re.search(r"fold|behind\s+(?:front|1st|first)\s+row|\bmax", text, re.I):
        return "cargo_max_cu_ft"
    return "cargo_cu_ft"


# ---------------------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------------------
def load_pagetext(sha: str) -> list[str] | None:
    path = RAW_ROOT / "pagetext" / f"{sha}.json.gz"
    if not path.exists():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)["pages"]


def parse_pdf(path: Path, page_texts: list[str]) -> dict:
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        lines, npages = load_lines(pdf)
    norm_pages = [norm(p) for p in page_texts]
    skip = boilerplate(lines, npages)
    sections = build_sections(lines, skip)
    # document-level value boundary for sections without own samples
    all_samples = []
    for sec in sections:
        layout_section(sec, None)
        if len(sec.columns) == 1 and sec.columns[0].title is None:
            all_samples.append(round(sec.boundary / 4) * 4)
    doc_boundary = float(Counter(all_samples).most_common(1)[0][0]) if all_samples else None
    facts, review, codes = [], [], []
    for sec in sections:
        layout_section(sec, doc_boundary)
        multi = len(sec.columns) > 1
        for row in build_rows(sec):
            key = key_for(row.label, sec, row.own if row.parent else "")
            if key is None or not row.cells:
                continue
            if key == "turning_radius":
                review.append({"page": row.cells[0].seg.line.page, "row": row.label,
                               "reason": "turning radius (not a turning-circle diameter); not converted"})
                continue
            by_col: dict[tuple[int, str | None], list[Cell]] = defaultdict(list)
            for c in row.cells:
                by_col[(c.col, None)].append(c)
            for (col, _), cells in by_col.items():
                col_title = sec.columns[col].title if multi and col >= 0 else None
                for item in split_items(cells, key):
                    found, reasons = facts_from_item(key, row.label, item, col_title)
                    if key in ("front_brakes", "front_suspension") and re.search(r"Front\s*/\s*Rear", row.label, re.I):
                        # one cell for "Brake Type Front/Rear": the value is published for both axles
                        found += [{**f, "key": f["key"].replace("front_", "rear_")} for f in found]
                    first, last = item.cells[0].seg, item.cells[-1].seg
                    page = first.line.page
                    for reason in reasons:
                        review.append({"page": page, "row": row.label, "reason": reason})
                    for f in found:
                        if f["key"] == "engine_code":
                            for code in re.split(r"\s*[,/;]\s*|\s+or\s+", f["value"]):
                                if code and code not in codes:
                                    codes.append(code)
                            continue
                        fact = make_fact(f, row, item, col_title, lines, norm_pages)
                        if fact is None:
                            review.append({"page": page, "row": row.label,
                                           "reason": f"quote not found in page text: {item.text!r}"})
                        else:
                            facts.append(fact)
    return {"facts": facts, "review": review, "engine_codes": codes, "pages": npages,
            "sections": [s.title for s in sections]}


def make_fact(f: dict, row: Row, item: Item, col_title: str | None, lines: list[Line], norm_pages: list[str]) -> dict | None:
    first, last = item.cells[0].seg, item.cells[-1].seg
    page = first.line.page
    if last.line.page != page:
        last = next(c.seg for c in reversed(item.cells) if c.seg.line.page == page)
    start = (first.line.gi, first.w0)
    end = (last.line.gi, last.w1)
    # include the row label when it stands directly left of the value on the same line
    label_segs = [s for s in row.labels if s.line.gi == first.line.gi and s.w1 < first.w0]
    if label_segs and label_segs[-1].w1 == first.w0 - 1:
        start = (first.line.gi, label_segs[0].w0)
    if item.cells[0].sub_seg is not None and item.cells[0].sub_seg.line.page == page:
        # value under a grade header: quote the header line and the value line ("LE SE XLE XSE 3,450 3,494 ...")
        head = item.cells[0].sub_seg.line
        start = (head.gi, 0)
        end = (last.line.gi, len(last.line.words) - 1)
    quote = span_text(lines, start, end)
    if norm(quote) not in norm_pages[page - 1]:
        quote = span_text(lines, (first.line.gi, first.w0), end)
        if norm(quote) not in norm_pages[page - 1]:
            quote = first.text
            if norm(quote) not in norm_pages[page - 1]:
                return None
    parts = [p for p in (col_title, item.cells[0].sub, f.get("trim")) if p]
    if f.get("pair") and f["key"] not in ("track_front_in", "track_rear_in"):
        if f["key"] in ("curb_weight_lb", "towing_lb"):
            parts.append(f["pair"])
    engine_text = "; ".join(parts) if parts else None
    row_text = row.label
    if f.get("cond"):
        row_text += f" ({f['cond']})"
    if f.get("pair") and f["key"] not in ("curb_weight_lb", "towing_lb"):
        row_text += f" [{f['pair']}]"
    key = f["key"]
    if key == "cargo":
        key = cargo_key(row.label + (" " + f["pair"] if f.get("pair") else ""), f.get("cond"))
    original = norm(" ".join(p for p in (row.label, item.cells[0].sub, item.text) if p))
    if key == "electric_motor" and not re.search(r"motor", row.label, re.I):
        row_text = f"{row.section.title}: {row_text}"
    return {"key": key, "value": f["value"], "page": page, "quote": norm(quote), "original": original,
            "engine_text": engine_text, "row": row_text}


def manifest_docs(hosts: list[str]) -> list[dict]:
    docs: dict[str, dict] = {}
    for host in hosts:
        path = MANIFEST_DIR / f"{host}.csv"
        if not path.exists():
            continue
        rows: dict[str, dict] = {}
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                rows[row["url"]] = row  # last row per URL wins (append-only manifest)
        for row in rows.values():
            if row["doc_type"] != "press_specifications" or row["status"] != "ok":
                continue
            doc = docs.setdefault(row["sha256"], {"host": host, "rows": []})
            doc["rows"].append(row)
    return list(docs.values())


def doc_title(page_texts: list[str], make: str) -> tuple[int | None, str | None, str]:
    """Model year and line named by the document's own title (first lines of page 1),
    e.g. "2019 RAV4 Product Information", "2022 NX 350 Specifications"."""
    from collect_press_toyota import title_line

    head = (page_texts[0] if page_texts else "").splitlines()[:8]
    for i, line in enumerate(head):
        found = re.search(r"\b(20\d\d)\b", line)
        if not found:
            continue
        context = " ".join(head[i : i + 2])  # "2025 Camry" / "Product Information" on two lines
        named = title_line(make, context)
        if named or re.search(r"Product|Specification|Spec Sheet|Features", context, re.I):
            return int(found.group(1)), named, norm(context)
    return None, None, norm(" ".join(head))


def run(hosts: list[str], only: str | None = None) -> None:
    from collect_press_toyota import TITLE_EXCLUDE
    from us_tech_lines import BY_KEY

    summary = Counter()
    per_key = Counter()
    for doc in manifest_docs(hosts):
        rows = sorted(doc["rows"], key=lambda r: (r["year"], r["url"]))
        main = rows[0]
        host = doc["host"]
        sha = main["sha256"]
        if only and not sha.startswith(only):
            continue
        make = main["make"]
        raw = RAW_ROOT / main["path"]
        pages = load_pagetext(sha)
        lines_keys = sorted({r["line"] for r in rows})
        years = sorted({int(r["year"]) for r in rows})
        review: list[dict] = []
        status = "ok"
        result = {"facts": [], "review": [], "engine_codes": [], "pages": len(pages or [])}
        if pages is None:
            status = "no_pagetext"
        elif not raw.suffix.lower() == ".pdf":
            status = "unsupported"
        elif sum(len(p.strip()) for p in pages) == 0:
            status = "no_text_layer"
            review.append({"page": 1, "row": "", "reason": "PDF has no text layer (image-only); not parsed"})
        else:
            result = parse_pdf(raw, pages)
            review += result["review"]
            year, named, head = doc_title(pages, make)
            if year is not None and years != [year]:
                linked = years
                line = BY_KEY[lines_keys[0]]
                if line.years[0] <= year <= line.years[1] and 2014 <= year <= 2026:
                    years = [year]  # the document's own model year wins over the linking page
                    review.append({"page": 1, "row": "", "reason": f"document title states model year {year} "
                                   f"({head[:80]}); linked from newsroom page(s) for {linked}"})
                else:
                    status = "year_mismatch"
                    review.append({"page": 1, "row": "", "reason": f"document title states model year {year} "
                                   f"({head[:80]}), outside the line years; linked for {linked}"})
            if year is None:
                review.append({"page": 1, "row": "", "reason": f"model year not found in document title: {head[:100]}"})
            if (named and named not in lines_keys) or TITLE_EXCLUDE.search(head):
                status = "line_mismatch"
                review.append({"page": 1, "row": "", "reason": f"document title names another model ({head[:80]}), "
                               f"linked as {lines_keys}"})
        line_slug = lines_keys[0].split("/")[1]
        key = f"press-{HOSTS[host]['short']}-{line_slug}-{years[0]}-{sha[:8]}"
        page_url = re.search(r"page_url=(\S+?);", main["note"] + ";")
        out = {
            "doc": {
                "key": key,
                "make": make,
                "lines": lines_keys,
                "years": years,
                "doc_type": "press_specifications",
                "title": main["title"],
                "path": str(raw),
                "url": main["url"],
                "page_url": page_url.group(1) if page_url else "",
                "sha256": sha,
                "retrieved_at": main["retrieved_at"],
                "tier": "A",
                "source_type": "PRESS_RELEASE",
                "publisher": HOSTS[host]["publisher"],
                "authenticity": "OFFICIAL_PUBLISHER",
            },
            "extractor": EXTRACTOR,
            "pages": result["pages"],
            "edition_market": "US",
            "status": status,
            "engine_codes": result["engine_codes"],
            "review": review,
            "facts": result["facts"],
        }
        target = WORK / make / "extracted" / f"{key}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        summary[(host, status)] += 1
        for f in out["facts"]:
            per_key[(host, f["key"])] += 1
        print(f"{key}: status={status} facts={len(out['facts'])} review={len(review)}")
    print("\nstatus:", dict(summary))
    for host in hosts:
        print(host, {k: v for (h, k), v in sorted(per_key.items()) if h == host})


def written_docs(hosts: list[str]) -> list[Path]:
    out = []
    for host in hosts:
        short = HOSTS[host]["short"]
        make = "toyota" if short == "toyota" else "lexus"
        out += sorted((WORK / make / "extracted").glob(f"press-{short}-*.json"))
    return out


def verify(hosts: list[str]) -> int:
    bad = 0
    total = 0
    for path in written_docs(hosts):
        doc = json.loads(path.read_text(encoding="utf-8"))
        pages = load_pagetext(doc["doc"]["sha256"]) or []
        normed = [norm(p) for p in pages]
        for f in doc["facts"]:
            total += 1
            if not (1 <= f["page"] <= len(normed)) or norm(f["quote"]) not in normed[f["page"] - 1]:
                bad += 1
                print("QUOTE NOT FOUND:", path.name, f["key"], f["quote"][:80])
    print(f"verify: {total} facts, {bad} quotes not found")
    return bad


def spot(hosts: list[str], n: int, seed: int) -> None:
    rng = random.Random(seed)
    pool = []
    for path in written_docs(hosts):
        doc = json.loads(path.read_text(encoding="utf-8"))
        pool += [(path, doc, f) for f in doc["facts"]]
    for path, doc, f in rng.sample(pool, min(n, len(pool))):
        pages = load_pagetext(doc["doc"]["sha256"])
        text = pages[f["page"] - 1]
        lines = text.splitlines()
        first_word = f["quote"].split(" ")[0]
        idx = next((i for i, ln in enumerate(lines) if norm(f["quote"]).startswith(norm(ln)[: len(first_word)])
                    and first_word in ln), None)
        hit = next((i for i, ln in enumerate(lines) if norm(f["quote"])[:25] in norm(ln) or norm(ln)[:25] in norm(f["quote"])), idx)
        print("=" * 100)
        print(path.name, "| page", f["page"], "|", doc["doc"]["url"])
        print(json.dumps(f, ensure_ascii=False))
        if hit is not None:
            for ln in lines[max(0, hit - 4) : hit + 5]:
                print("   |", ln)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--host", action="append", choices=sorted(HOSTS))
    ap.add_argument("--only", help="sha256 prefix of one document")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--
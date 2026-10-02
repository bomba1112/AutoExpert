"""Parse the stored US press specification documents of hyundainews.com / kiamedia.com.

Input: the press manifests written by scripts/collect_press_hyundai_kia.py
(data_work/_shared/manifest_press/<host>.csv, rows doc_type=press_specifications, status=ok),
the stored PDFs under RAW_ROOT/press/<host>/ and their page text RAW_ROOT/pagetext/<sha256>.json.gz.
Output: one JSON per document, data_work/<make>/extracted/press-<host-short>-<line-slug>-<year>-<sha8>.json,
in the format of data_work/_shared/press/FORMAT.md.

How values are read (by script only):
- The spec sheets are tables. pdfplumber gives the table cells (bounding boxes); the words inside
  each cell (with their x/y position and font size) give the cell text and its visual lines.
- Column headers (trim / engine labels) are header rows: cells right of the label column whose
  text is a short name (no number with a unit, no S/- mark) and that are set in a larger font, or
  follow a section title. Two stacked header rows are combined ("Hybrid" over "SE" = "Hybrid SE").
  A value cell belongs to the header columns it covers horizontally; that label is the fact's
  engine_text. A value that covers all columns gets engine_text = the engine sub-heading of the
  ENGINE block when the sheet lists several engines, else null.
- Cells that stack several labels / values (one per visual line) are paired line by line when
  the lines sit at the same height; lines that do not line up go to `review`.
- Rows of S / O / - marks give the item of the row (a transmission, a tire size, a wheel) for
  the columns marked S, O or P.
- A cell without a vertical rule between label and value ("Power Output   39 kW ...") is split
  at the wide horizontal gap between the words.
- Values that carry their own unit ("191 hp @ 6100 rpm", "181 lb.-ft. @ 4000", "(2,497 cc)",
  "Bore & Stroke (mm): 85.5 x 101.5") are read from the cell text itself.
- Numbers are parsed, units are never converted; a numeric fact needs its unit on the row, in the
  column/section heading or in the value (e.g. inches for dimensions), otherwise it goes to review.
- Every fact gets a verbatim quote: the shortest of (label + value, the whole row, the label and
  value cells, the value) that occurs in the stored page text (whitespace-normalised). Facts without
  such a quote are not written (they are listed in review).

Run:
  uv run --no-project --with pdfplumber --with pypdfium2 python scripts/extract_press_hyundai_kia.py [--host H] [--only SUBSTR] [--verify]
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
from dataclasses import dataclass, field, replace
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import BY_KEY  # noqa: E402

EXTRACTOR = "press-hyundai_kia-1"
HOSTS = {
    "www.hyundainews.com": ("hyundainews", "Hyundai USA Media Center (www.hyundainews.com)"),
    "www.kiamedia.com": ("kiamedia", "Kia America media site (www.kiamedia.com)"),
}
MANIFEST_DIR = WORK / "_shared" / "manifest_press"

MARKS = {"S", "O", "P", "-", "–", "—", "N/A", "NA", "●", "○", "X", "STD", "STD.", "OPT", "OPT.", "N/A*"}
AVAILABLE = {"S", "O", "P", "●", "STD", "STD.", "OPT", "OPT."}
EMPTY_VALUES = {"", "TBD", "TBA", "N/A", "NA", "-", "–", "—", "NOT RECOMMENDED", "NOT AVAILABLE", "N/A*"}
SECTION_RE = re.compile(
    r"(?i)^(mechanical|engine|motor|electric|transmission|gear|suspension|steering|brake|tire|wheel|"
    r"exterior|interior|dimension|weight|capacit|volume|fuel economy|mpg|charging|battery|"
    r"performance|specification|chassis|powertrain|drivetrain|body|electrical|epa|towing|cargo)"
)
BOLD = re.compile(r"(?i)bold|black|heavy|semibold|demi")
TITLE_RE = re.compile(SECTION_RE.pattern[:-1] + r"|hybrid)")  # stand-alone title rows
UNIT_RE = re.compile(
    r"(?i)(\d\s*(\"|”|″|in\b|in\.|inch|mm\b|cm\b|lbs?\b|lb\.|kg\b|cu\.?\s*ft|cubic|gal|hp\b|ps\b|kw\b|"
    r"rpm|ft\b|ft\.|feet|:1\b|v\b|ah\b|kwh|mpg|mph|sec|qt|cc\b|liters?\b|litres?\b|j\b))|@|\d{3}/\d{2}|"
    r"\d\s*[x×]\s*\d"
)
NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?|\.\d+")
TIRE_RE = re.compile(r"(?<![\w/])[PT]?\d{3}\s?/\s?\d{2}\s?[A-Z]?R\s?F?\s?\d{2}(?:\s?\d{2,3}[A-Z]{1,2}\b)?")
HP_RE = re.compile(
    r"(?i)(?<![\d.,])(\d{2,4}(?:\.\d)?)\s*(?:hp|horsepower)\b\.?\s*(?:@\s*([\d,]+(?:\s*[-–~]\s*[\d,]+)?)(?:\s*rpm)?)?"
)
TQ_RE = re.compile(
    r"(?i)(?<![\d.,])(\d{2,4}(?:\.\d)?)\s*lb\.?\s*[-.‐–\xad]?\s*ft\.?\s*(?:@\s*([\d,]+(?:\s*[-–~\xad]\s*[\d,]+)?)(?:\s*rpm)?)?"
)
CC_RE = re.compile(r"(?i)(?<![\d.])(\d[\d,]{2,5})\s*cc\b")
BORE_RE = re.compile(
    r"(?i)(\d{2,3}(?:\.\d+)?)\s*(mm|in\.?)?\s*[xX×]\s*(\d{2,3}(?:\.\d+)?)\s*(mm|in\.?)?"
)
DASHES = str.maketrans({"\xad": "-", "￾": "-", "\x02": "-","‐": "-", "‑": "-", " ": " ", "\xa0": " "})


def join_lines(lines: list[str]) -> str:
    """Lines of one cell; a word hyphenated at the line end is joined without a space."""
    out = ""
    for line in lines:
        if out and re.search(r"[A-Za-z][-\xad]$", out) and re.match(r"[a-z]", line):
            out += line
        else:
            out = f"{out} {line}" if out else line
    return out


def norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def disp(text: str) -> str:
    """Display form of published text: soft hyphens shown as hyphens, single spaces."""
    return norm_ws((text or "").translate(DASHES))


def is_mark(text: str) -> bool:
    return disp(text).upper() in MARKS


def num(text: str):
    found = NUM_RE.search(text or "")
    if not found:
        return None
    raw = found.group(0).replace(",", "")
    value = float(raw)
    return int(value) if value.is_integer() and "." not in raw else value


# ---------------------------------------------------------------------------------------------
# Quotes: verbatim from the stored page text (whitespace-normalised)
# ---------------------------------------------------------------------------------------------
FOLD = str.maketrans({"\xad": "-", "￾": "-", "\x02": "-", "‐": "-", "‑": "-", "–": "-", "—": "-", "”": '"', "″": '"', "“": '"',
                      "’": "'", "‘": "'"})


class PageText:
    def __init__(self, text: str):
        self.norm = norm_ws(text)
        squeezed, index = [], []
        for pos, char in enumerate(self.norm):
            if char.isspace():
                continue
            squeezed.append(char.translate(FOLD).lower())
            index.append(pos)
        self.squeezed = "".join(squeezed)
        self.index = index

    def find(self, candidate: str) -> str | None:
        key = "".join(c.translate(FOLD).lower() for c in candidate if not c.isspace())
        if not key:
            return None
        at = self.squeezed.find(key)
        if at < 0:
            return None
        start, end = self.index[at], self.index[at + len(key) - 1] + 1
        return self.norm[start:end]


# ---------------------------------------------------------------------------------------------
# Table model
# ---------------------------------------------------------------------------------------------
@dataclass
class Line:
    text: str
    top: float
    x0: float
    x1: float
    size: float
    segments: list  # [(text, x0, x1)]
    bold: bool = False


@dataclass
class Cell:
    x0: float
    x1: float
    top: float
    bottom: float
    lines: list = field(default_factory=list)

    @property
    def text(self) -> str:
        return join_lines([line.text for line in self.lines])

    @property
    def center(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def size(self) -> float:
        return max((line.size for line in self.lines), default=0)

    @property
    def bold(self) -> bool:
        return bool(self.lines) and all(line.bold for line in self.lines)


@dataclass
class Leaf:
    label: str
    x0: float
    x1: float


def join_hyphens(row: list) -> list:
    """'6', '‐', 'speed' set as separate words that touch each other are one word: '6‐speed'."""
    out: list = []
    i = 0
    while i < len(row):
        word = row[i]
        if out and i + 1 < len(row) and word["text"] in {"-", "‐", "‑", "\xad"} \
                and word["x0"] - out[-1]["x1"] < 2.5 and row[i + 1]["x0"] - word["x1"] < 2.5:
            nxt = row[i + 1]
            out[-1] = {**out[-1], "text": out[-1]["text"] + word["text"] + nxt["text"], "x1": nxt["x1"],
                       "bottom": max(out[-1]["bottom"], nxt["bottom"])}
            i += 2
            continue
        out.append(word)
        i += 1
    return out


def words_to_lines(words: list, gap: float = 9.0) -> list[Line]:
    rows: list[list] = []
    for word in sorted(words, key=lambda w: (round(w["top"], 1), w["x0"])):
        for row in rows:
            if abs(row[0]["top"] - word["top"]) <= 2.6 or abs(row[0]["bottom"] - word["bottom"]) <= 1.6:
                row.append(word)
                break
        else:
            rows.append([word])
    lines = []
    for row in rows:
        row.sort(key=lambda w: w["x0"])
        row = join_hyphens(row)
        segments, current = [], [row[0]]
        for prev, word in zip(row, row[1:]):
            limit = max(gap, 1.1 * max(word.get("size", 10), prev.get("size", 10)))
            if word["x0"] - prev["x1"] > limit:
                segments.append(current)
                current = [word]
            else:
                current.append(word)
        segments.append(current)
        segs = [(" ".join(w["text"] for w in s), s[0]["x0"], s[-1]["x1"]) for s in segments]
        lines.append(Line(
            text=" ".join(w["text"] for w in row), top=min(w["top"] for w in row),
            x0=row[0]["x0"], x1=row[-1]["x1"], size=max(w.get("size", 0) for w in row), segments=segs,
            bold=all(BOLD.search(w.get("fontname", "")) for w in row),
        ))
    lines.sort(key=lambda line: line.top)
    return lines


@dataclass
class Row:
    cells: list  # Cell objects left to right (grid positions covered by a merged cell are left out)
    first_missing: bool  # the first grid position is covered by a cell merged from the row above


def page_rows(page) -> list[Row]:
    """Rows of cells of all tables on the page (top to bottom); pages without tables: text lines."""
    words = page.extract_words(x_tolerance=1.5, y_tolerance=2.5, extra_attrs=["size", "fontname"])
    tables = page.find_tables()
    rows: list[tuple[float, Row]] = []
    used = set()
    for table in tables:
        for row in table.rows:
            cells = []
            for bbox in row.cells:
                if bbox is None:
                    continue
                x0, top, x1, bottom = bbox
                inside = []
                for i, w in enumerate(words):
                    cx, cy = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
                    if x0 - 0.5 <= cx <= x1 + 0.5 and top - 0.5 <= cy <= bottom + 0.5 and i not in used:
                        inside.append(w)
                        used.add(i)
                cell = Cell(x0, x1, top, bottom, words_to_lines(inside) if inside else [])
                cells.append(cell)
            if any(cell.lines for cell in cells):
                rows.append((min(c.top for c in cells), Row(cells, row.cells[0] is None)))
    if not tables:
        for line in words_to_lines(words):
            cells = [Cell(x0, x1, line.top, line.top + line.size,
                          [Line(t, line.top, x0, x1, line.size, [(t, x0, x1)])]) for t, x0, x1 in line.segments]
            rows.append((line.top, Row(cells, False)))
    rows.sort(key=lambda item: item[0])
    return [row for _, row in rows]


def upper_title(text: str) -> bool:
    """All capitals once a parenthetical unit is removed: 'VOLUME (cubic ft)'."""
    bare = re.sub(r"\([^)]*\)", "", disp(text)).strip()
    return bool(bare) and bare.isupper()


def trim_like(text: str) -> bool:
    text = disp(text)
    words = [w for w in text.split() if w not in {"/", "&", "|", "-", "–"}]
    listing = text.count("/") >= 2  # "SE / SEL Sport / SEL Sport Premium / LIMITED"
    if not text or is_mark(text) or len(text) > (60 if listing else 45) or len(words) > (9 if listing else 7):
        return False
    if re.search(r"(?i)cylinder|valve|\bDOHC\b|\bSOHC\b|block|alumin|\bdisc\b|strut|independent|multi-link|"
                 r"torsion|automatic|manual|speed|steering|motor\b", text):
        return False
    if UNIT_RE.search(text) or TIRE_RE.search(text) or ":" in text or re.search(r"\d-?in\b", text):
        return False
    if any(is_mark(token) for token in text.split()):
        return False  # a column of S / - marks
    if re.fullmatch(r"[\d\s,./()+-]+", text):
        return False
    return True


def covers(cell: Cell, leaf: Leaf) -> bool:
    overlap = min(cell.x1, leaf.x1) - max(cell.x0, leaf.x0)
    width = max(leaf.x1 - leaf.x0, 1)
    center = (leaf.x0 + leaf.x1) / 2
    return overlap >= 0.5 * width or (cell.x0 - 1 <= center <= cell.x1 + 1) or (leaf.x0 - 1 <= cell.center <= leaf.x1 + 1)


# ---------------------------------------------------------------------------------------------
# Fact keys
# ---------------------------------------------------------------------------------------------
INCH = re.compile(r"(?i)\(in\.?\)|\(inches\)|\binches\b|\bin\.|\d\s*in\b|”|\"|″|\(in\b")
FOOT = re.compile(r"(?i)\bft\b|ft\.|feet")
LBS = re.compile(r"(?i)\blbs?\b|lb\.|pounds")
GAL = re.compile(r"(?i)\bgal")
CUFT = re.compile(r"(?i)cu\.?\s*ft|cubic|cu\. ?ft")


@dataclass
class Entry:
    page: int
    section: str
    sub: str
    group: str
    label: str
    value: str  # value text (or item text for S/O rows)
    engine_text: str | None
    quotes: list  # candidate quote strings, best first
    original: str
    mark_row: bool = False
    motor_ctx: bool = False  # follows an electric-motor row of the same block


def slash_variants(label: str, value: str) -> list[tuple[str, str]] | None:
    """'Minimum Ground Clearance (2WD/AWD)' + '7.1 / 8.3' -> [('2WD', '7.1'), ('AWD', '8.3')]."""
    names = re.search(r"\(([^()]+/[^()]+)\)\s*$", label) or re.search(
        r"(?<![\w/])([A-Z0-9]{2,5}(?:\s*/\s*[A-Z0-9]{2,5})+)\s*$", label)
    if not names:
        return None
    parts = [n.strip() for n in names.group(1).split("/")]
    values = [v.strip() for v in value.split("/")]
    if any(re.search(r"(?i)front|rear", n) for n in parts):
        return None
    if len(parts) != len(values) or not all(re.fullmatch(r"\d[\d,]*(?:\.\d+)?", v) for v in values):
        return None
    return list(zip(parts, values))


def numeric_fact(key, value_text, ctx, unit_re, unit_name, entry, out, review):
    text = disp(value_text)
    if text.upper() in EMPTY_VALUES:
        return
    numbers = NUM_RE.findall(re.sub(r"\([^)]*\)", "", text))
    if not numbers:
        return
    variants = slash_variants(disp(entry.label), text)
    if variants:
        if not unit_re.search(ctx + " " + text):
            review.append({"page": entry.page, "row": entry.original, "reason": f"{key}: unit ({unit_name}) not stated"})
            return
        for name, part in variants:
            engine = f"{entry.engine_text} {name}" if entry.engine_text else name
            out.append((key, num(part), replace(entry, engine_text=engine), text))
        return
    if len([part for part in re.sub(r"\([^)]*\)", "", text).split("/") if part.strip()]) > 1:
        review.append({"page": entry.page, "row": entry.original, "reason": f"{key}: several values in one cell"})
        return
    if len(numbers) > 1 or re.search(r"\(\s*[^)]*\d", text):
        review.append({"page": entry.page, "row": entry.original, "reason": f"{key}: several numbers in one cell"})
        return
    if not unit_re.search(ctx + " " + text):
        review.append({"page": entry.page, "row": entry.original, "reason": f"{key}: unit ({unit_name}) not stated"})
        return
    out.append((key, num(text), entry, text))


def map_entry(entry: Entry, multi_engine: bool, out: list, review: list, unit_ctx: str = "") -> None:
    """Fact keys for one label/value pair."""
    sec, sub, group, label = entry.section.upper(), entry.sub.upper(), entry.group.upper(), entry.label.upper()
    lab = disp(f"{group} {label}").upper()
    ctx = disp(f"{entry.section} | {entry.sub} | {entry.group} | {entry.label}")
    ctxu = ctx.upper()
    uctx = f"{ctx} | {unit_ctx}"  # units may be stated on a heading or sibling row of the same block
    value = disp(entry.value)
    valu = value.upper()
    if not value or valu in EMPTY_VALUES:
        return
    if not entry.mark_row and is_mark(value):
        return
    words = disp(entry.label).split()
    last = words[-1] if words else ""
    if len(last) >= 4 and last.isalpha() and last.lower() not in {"feet", "inch", "inches", "gallons", "liters"} \
            and value.endswith(" " + last) and not entry.mark_row:
        review.append({"page": entry.page, "row": entry.original, "reason": "value cell repeats the row label"})
        return
    motor = (entry.motor_ctx or bool(MOTOR_CTX.search(f"{sub} {group} {label}"))) and "MOTOR MOUNT" not in lab \
        and "STEERING" not in ctxu and not re.search(r"ENGINE\s*\+|GAS(OLINE)? ENGINE", lab)
    battery = "BATTERY" in f"{group} {label}" and "MOTOR" not in label
    combined = bool(re.search(r"COMBINED|SYSTEM (HORSE|POWER|OUTPUT|NET)|TOTAL SYSTEM|NET HORSEPOWER|SYSTEM PERF|"
                              r"ENGINE\s*\+\s*(ELECTRIC )?MOTOR|TOTAL OUTPUT|TOTAL TORQUE|TOTAL (SYSTEM )?(HORSE)?POWER", ctxu))

    # transmission description rows
    if entry.mark_row:
        if re.search(r"TRANSMISSION", ctxu) and GEARBOX.search(value) \
                and not re.search(r"(?i)paddle|clutch type|^shiftronic|^manual shift|shift-by", value):
            out.append(("transmission_description", value, entry, value))
        elif re.search(r"\bTIRES?\b", lab) and "SPARE" not in lab and "PRESSURE" not in lab:
            for tire in TIRE_RE.findall(value):
                out.append(("tires", norm_ws(tire), entry, tire))
        elif re.search(r"\bWHEELS?\b", lab) and not re.search(r"WHEELBASE|STEERING|DRIVE|TREAD|SPARE|LOCK", lab):
            size = re.match(r"\s*(\d{2})(?:\s*x|\s*-?\s*in|\s*”|\s*\"|-inch)", value)
            if size:
                out.append(("wheel_size_in", int(size.group(1)), entry, value))
        elif "STEERING" in ctxu and not is_mark(value) and (
                re.search(r"(?i)power steering|rack|pinion|MDPS|\bEPS\b", value)
                or re.match(r"(?i)\s*(motor\s*-?\s*driven )?power steering|\s*steering\b", entry.group)) \
                and not re.search(r"(?i)wheel|column tilt|heated|telescop|energy|collapsible|warning|light|indicator",
                                  f"{entry.group} {value}"):
            out.append(("steering", value, entry, value))
        elif motor and re.search(r"(?i)\bmotor\b", value) and not re.search(r"(?i)mount", value):
            out.append(("electric_motor", value, entry, value))
        return

    # power / torque
    if re.search(r"HORSEPOWER|\bOUTPUT\b|MAX\.? POWER|\bPOWER\b", label) and "STEERING" not in ctxu \
            and "BATTERY POWER" not in label and not battery and "TORQUE" not in label:
        if KW_FIRST.search(value) and not combined and not motor:
            review.append({"page": entry.page, "row": entry.original,
                           "reason": "power given in kW first: motor or engine not stated"})
            return
        if motor and not combined:
            out.append(("electric_motor", value, entry, value))
            return
        hp = HP_RE.search(value) or re.match(r"\s*(\d{2,4})\s*(?:@\s*([\d,]+(?:\s*[-–~]\s*[\d,]+)?))?", value)
        if not hp:
            return
        key = "system_power_hp" if combined else "power_hp"
        if not combined and "HORSEPOWER" not in label and "HP" not in valu:
            return
        out.append((key, num(hp.group(1)), entry, value))
        if hp.group(2) and key == "power_hp":
            out.append(("power_rpm", hp.group(2).replace(" ", ""), entry, value))
        return
    if re.search(r"\bTORQUE\b", label) and "CONVERTER" not in label:
        if motor and not combined:
            out.append(("electric_motor", value, entry, value))
            return
        if combined:
            return
        tq = TQ_RE.search(value) or re.match(r"\s*(\d{2,4})\s*(?:@\s*([\d,]+(?:\s*[-–~]\s*[\d,]+)?))?", value)
        if not tq:
            return
        if not LBS.search(uctx + " " + value):
            review.append({"page": entry.page, "row": entry.original, "reason": "torque: unit not stated"})
            return
        out.append(("torque_lb_ft", num(tq.group(1)), entry, value))
        if tq.group(2):
            out.append(("torque_rpm", tq.group(2).replace(" ", ""), entry, value))
        return
    if motor and re.search(r"MOTOR TYPE|^TYPE$|^MOTOR$", label) and not battery:
        out.append(("electric_motor", value, entry, value))
        return
    if motor and not battery and re.search(r"(?i)motor", label) and not re.search(r"MOUNT", label):
        out.append(("electric_motor", f"{entry.label} {value}" if is_mark(value) else value, entry, value))
        return
    if battery or motor:
        return

    # engine
    if re.search(r"DISPLACEMENT", label):
        cc = CC_RE.search(value)
        if cc:
            out.append(("engine_displacement_cc", num(cc.group(1)), entry, value))
        return
    if re.search(r"BORE", label):
        found = BORE_RE.search(value)
        if found:
            unit = (found.group(2) or found.group(4) or "").lower()
            unit = unit or ("mm" if "MM" in lab else ("in" if re.search(r"\bIN\b|INCH", lab) else ""))
            if unit.startswith("mm"):
                out.append(("bore_stroke_mm", f"{found.group(1)} x {found.group(3)}", entry, value))
            elif unit.startswith("in"):
                out.append(("bore_stroke_in", f"{found.group(1)} x {found.group(3)}", entry, value))
            else:
                review.append({"page": entry.page, "row": entry.original, "reason": "bore/stroke: unit not stated"})
        return
    if re.search(r"COMPRESSION", label):
        if re.fullmatch(r"\d{1,2}(\.\d+)?\s*(:\s*1)?", value):
            out.append(("compression_ratio", value, entry, value))
        elif NUM_RE.search(value):
            review.append({"page": entry.page, "row": entry.original, "reason": "compression ratio not readable"})
        return
    if re.search(r"VALVETRAIN|VALVE TRAIN|VALVE SYSTEM|VALVE GEAR", label):
        out.append(("valvetrain", value, entry, value))
        return
    if re.search(r"FUEL (SYSTEM|DELIVERY|INJECTION)|INJECTION", label):
        out.append(("injection", value, entry, value))
        return
    if re.search(r"^ENGINE|ENGINE$", sec + " " + sub) or sub.startswith("ENGINE") or sec.startswith("ENGINE"):
        if re.fullmatch(r"(ENGINE )?TYPE|ENGINE", label.strip()):
            out.append(("engine_description", value, entry, value))
            return

    # transmission
    if "TRANSMISSION" in ctxu and re.search(r"TRANSMISSION|^TYPE$", label) and "DRIVE" not in label:
        if GEARBOX.search(value) or re.match(r"(?i)\s*(automatic|manual)\b", value):
            out.append(("transmission_description", value, entry, value))
        return

    # suspension / brakes / steering
    if "SUSPENSION" in ctxu:
        if not re.fullmatch(r"(FRONT|REAR)( SUSPENSION)?( TYPE)?|(FRONT|REAR) SUSPENSION TYPE|TYPE,? (FRONT|REAR)", lab.strip()):
            return
        if "FRONT" in lab:
            out.append(("front_suspension", value, entry, value))
        elif "REAR" in lab:
            out.append(("rear_suspension", value, entry, value))
        return
    if "BRAKE" in ctxu and not re.search(r"ABS|ASSIST|PARKING|GENERAL|EBD|HOLD", lab) \
            and not re.search(r"TREAD|TRACK|TIRE|WHEEL|OVERHANG|ROOM|SEAT|SUSPENSION|STABI|LIGHT", lab) \
            and (re.match(r"(FRONT|REAR)\b", lab.strip()) or "BRAKE" in lab):
        if "FRONT" in lab:
            out.append(("front_brakes", value, entry, value))
        elif "REAR" in lab:
            out.append(("rear_brakes", value, entry, value))
        return
    if re.search(r"TURNING (DIAMETER|CIRCLE)", lab):
        numeric_fact("turning_circle_ft", value, uctx, FOOT, "feet", entry, out, review)
        return
    if "STEERING" in ctxu and re.search(r"^TYPE$|^STEERING$|STEERING TYPE", label.strip()):
        out.append(("steering", value, entry, value))
        return

    # tires / wheels with values
    if re.search(r"\bTIRES?\b", lab) and not re.search(r"SPARE|PRESSURE|MENDING|REPAIR|MOBILITY", lab):
        for tire in TIRE_RE.findall(value):
            out.append(("tires", norm_ws(tire), entry, tire))
        return
    if re.search(r"\bWHEELS?\b", lab) and not re.search(r"WHEELBASE|STEERING|DRIVE|TREAD|SPARE|LOCK|BASE", lab):
        size = re.match(r"\s*(\d{2})(?:\s*x|\s*-?\s*in|\s*”|\s*\"|-inch)", value)
        if size and not re.search(r"\d{2}\s*(?:x|-?\s*in|”|\").*\b\d{2}\s*(?:x|-?\s*in|”|\")", value):
            out.append(("wheel_size_in", int(size.group(1)), entry, value))
        return

    # dimensions
    if re.search(r"INTERIOR", sec + " " + sub) and not re.search(r"PASSENGER|CARGO|VOLUME", lab):
        return
    dims = [
        (r"WHEELBASE", "wheelbase_in"),
        (r"(OVERALL )?LENGTH", "length_in"),
        (r"(OVERALL )?WIDTH", "width_in"),
        (r"(OVERALL )?HEIGHT", "height_in"),
        (r"GROUND CLEARANCE", "ground_clearance_in"),
    ]
    if not re.search(r"ROOM|LEG|HEAD|SHOULDER|HIP|CARGO|LIFTOVER|STEP|SEAT|TRUNK|OPENING|BED|DOOR", lab):
        for pattern, key in dims:
            if re.search(rf"(^|[^A-Z]){pattern}($|[^A-Z])", lab):
                if key == "width_in" and re.search(r"TRACK|TREAD", lab):
                    continue
                numeric_fact(key, value, uctx, INCH, "inches", entry, out, review)
                return
    if re.search(r"TRACK|TREAD", lab) and not re.search(r"TRACTION", lab):
        both = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(?:in\.?)?\s*/\s*(\d+(?:\.\d+)?)\s*(?:in\.?)?\s*", value)
        if re.search(r"FRONT\s*/\s*REAR|FRONT/REAR", lab) and both:
            if not INCH.search(uctx + " " + value):
                review.append({"page": entry.page, "row": entry.original, "reason": "track: unit not stated"})
                return
            out.append(("track_front_in", num(both.group(1)), entry, value))
            out.append(("track_rear_in", num(both.group(2)), entry, value))
        elif "FRONT" in lab and "REAR" not in lab:
            numeric_fact("track_front_in", value, uctx, INCH, "inches", entry, out, review)
        elif "REAR" in lab and "FRONT" not in lab:
            numeric_fact("track_rear_in", value, uctx, INCH, "inches", entry, out, review)
        else:
            review.append({"page": entry.page, "row": entry.original, "reason": "track: front/rear not readable"})
        return

    # weights / capacities / volumes
    if re.search(r"CURB", lab):
        numeric_fact("curb_weight_lb", value, uctx, LBS, "lbs", entry, out, review)
        return
    if re.search(r"TOWING|TRAILER", lab):
        if NUM_RE.search(value):
            numeric_fact("towing_lb", value, uctx, LBS, "lbs", entry, out, review)
        return
    if re.search(r"FUEL( TANK)?( CAPACITY)?|FUEL TANK", lab) and not re.search(
            r"ECONOMY|SYSTEM|DELIVERY|INJECT|RECOMMENDED|TYPE|FILLER|DOOR|CAP\b", lab):
        if "CAPACIT" in ctxu or "TANK" in lab or GAL.search(uctx + value):
            numeric_fact("fuel_tank_gal", value, uctx, GAL, "gallons", entry, out, review)
        return
    if re.search(r"SEATING|SEATS\b|PASSENGERS\b", lab) and "VOLUME" not in lab and "HEATED" not in lab:
        if re.fullmatch(r"\d{1,2}", value):
            out.append(("seats", int(value), entry, value))
        return
    if re.search(r"PASSENGER", lab) and re.search(r"VOLUME|COMPARTMENT|^PASSENGER$", lab + " " + sub + " " + sec):
        numeric_fact("passenger_volume_cu_ft", value, uctx, CUFT, "cu. ft.", entry, out, review)
        return
    if re.search(r"CARGO|TRUNK", lab) and not re.search(r"COVER|NET|LIGHT|AREA LIGHT|HOOK|TRAY|SCREEN|OPENING|MAT", lab):
        if re.search(r"MAX|FOLDED|SEATS? DOWN|BEHIND (1ST|FIRST|FRONT|FR\b)", lab):
            numeric_fact("cargo_max_cu_ft", value, uctx, CUFT, "cu. ft.", entry, out, review)
        else:
            numeric_fact("cargo_cu_ft", value, uctx, CUFT, "cu. ft.", entry, out, review)
        return


KEY_WORDS = re.compile(
    r"(?i)horsepower|\bpower\b|torque|displacement|bore|compression|valve|injection|fuel|transmission|"
    r"suspension|brake|steering|turning|\btires?\b|\bwheels?\b|wheelbase|length|width|height|track|tread|"
    r"clearance|curb|weight|cargo|volume|seat|tow|motor|engine|output|\bhp\b|lb\.?-?\s?ft")
GEARBOX = re.compile(r"(?i)\w+\s*-?\s*speed\b|\bCVT\b|\bIVT\b|\bDCT\b|dual[- ]?clutch|variable transmission|"
                     r"reduction gear")
MOTOR_ROW = re.compile(r"(?i)synchronous motor|electric motor|traction motor|drive motor|motor type|permanent magnet")
KW_FIRST = re.compile(r"(?i)^\s*\d+(?:\.\d+)?\s*kW\b")
GARBLED = re.compile(r"(?:(?<!\S)\S ){4,}\S(?!\S)")
GLYPH = re.compile(r"^[\ue000-\uf8ff\s]+$")
MOTOR_CTX = re.compile(r"(?i)\bMOTOR\b|\bELECTRIC\b(?!AL)|\bBATTERY\b")
SELF_ENGINE = re.compile(r"(?i)\b\d\.\d\s*-?\s*(L|liter|litre)\b.*\b(cylinder|cyl|I4|V6|inline)|\(\s*[\d,]+\s*cc\s*\)")


def self_describing(entry_page, texts, engine_text, section, sub, out_entries):
    """Values that carry their own unit, inside one cell line: hp, lb-ft, cc, bore x stroke."""
    for text, quotes in texts:
        out_entries.append((text, quotes))


# ---------------------------------------------------------------------------------------------
# Document parser
# ---------------------------------------------------------------------------------------------
class DocParser:
    def __init__(self, pdf_path: Path, pages_text: list[str]):
        self.pdf_path = pdf_path
        self.texts = [PageText(text) for text in pages_text]
        self.entries: list[Entry] = []
        self.review: list[dict] = []
        self.engine_subs: list[str] = []

    # -- helpers --------------------------------------------------------------------------
    def body_size(self, rows) -> float:
        sizes = Counter()
        for cells in rows:
            for cell in cells:
                for line in cell.lines:
                    sizes[round(line.size, 1)] += len(line.text)
        return sizes.most_common(1)[0][0] if sizes else 10.0

    def parse(self) -> None:
        seen_pages = set()
        state = {"section": "", "sub": "", "leaves": [], "prev_header": None, "last_label": "", "engine": ""}
        with pdfplumber.open(self.pdf_path) as pdf:
            for number, page in enumerate(pdf.pages, start=1):
                key = self.texts[number - 1].norm if number - 1 < len(self.texts) else ""
                if key and key in seen_pages:
                    continue  # the same table printed again on the next page (clipped print-outs)
                seen_pages.add(key)
                rows = page_rows(page)
                body = self.body_size([row.cells for row in rows])
                for row in rows:
                    self.row(number, row, body, state)

    def header_cells(self, row: Row, body: float, state) -> tuple[str, list[Cell]] | None:
        """(lead text, column-name cells) when the row names the columns, else None."""
        cells = row.cells
        filled = [c for c in cells if c.text.strip()]
        if not filled:
            return None
        lead: Cell | None = None
        prev_leaves = state["prev_header"] or []
        if not row.first_missing and cells[0].text.strip():
            lead, names = cells[0], filled[1:]
        elif filled and SECTION_RE.search(disp(filled[0].text)) and (
                upper_title(filled[0].text) or filled[0].size > body + 0.8):
            lead, names = filled[0], filled[1:]
        elif prev_leaves and filled[0].x1 <= min(leaf.x0 for leaf in prev_leaves) + 2:
            lead, names = filled[0], filled[1:]  # e.g. "(in)" under a section title
        else:
            names = filled
        if not names or not all(trim_like(c.text) for c in names):
            return None
        lead_text = disp(lead.text) if lead else ""
        larger = max(c.size for c in names) > body + 0.8 or all(c.bold for c in names)
        prev = state["prev_header"] is not None
        if len(names) > 1 and len({disp(c.text) for c in names}) == 1 and not larger and not prev:
            return None  # the same text in every column is a value, not column names
        if not lead_text:
            empty_first = not row.first_missing and not cells[0].text.strip()
            if larger or prev or empty_first:
                return "", names
            return None
        if prev and re.fullmatch(r"\(.*\)", lead_text):
            return lead_text, names  # "(in)" under a section title
        lead_upper_section = upper_title(lead_text) and SECTION_RE.search(lead_text) and not UNIT_RE.search(lead_text)
        lead_larger = (lead.size > body + 0.8 or lead.bold) and len(lead_text) <= 45 and not UNIT_RE.search(lead_text)
        if lead_upper_section or lead_larger or larger:
            return lead_text, names
        # "Engine Lineup | 2.5L (All ICE Models) | 1.6T (HEV/PHEV)": a section name over distinct names
        if SECTION_RE.search(lead_text) and len(names) >= 2 and len({disp(c.text) for c in names}) == len(names):
            return lead_text, names
        return None

    @staticmethod
    def split_cell(cell: Cell, leaves: list[Leaf]) -> list[Cell]:
        """Columns inside one ruled cell: word groups separated by wide gaps, aligned by x."""
        start = min((leaf.x0 for leaf in leaves), default=None)
        groups: dict[tuple, list] = {}
        label_cols: list[float] = []
        for line in cell.lines:
            for text, x0, x1 in line.segments:
                piece = Cell(x0, x1, line.top, line.top + line.size)
                if start is not None and (x0 + x1) / 2 >= start - 1:
                    hit = tuple(i for i, leaf in enumerate(leaves) if covers(piece, leaf))
                    if not hit:
                        nearest = min(range(len(leaves)), key=lambda i: abs((leaves[i].x0 + leaves[i].x1) / 2 - piece.center))
                        hit = (nearest,)
                    key = ("v",) + hit
                else:
                    col = next((c for c in label_cols if abs(c - x0) <= 15), None)
                    if col is None:
                        label_cols.append(x0)
                        col = x0
                    key = ("l", col)
                groups.setdefault(key, []).append(Line(text, line.top, x0, x1, line.size, [(text, x0, x1)]))
        cells = []
        for lines in groups.values():
            lines.sort(key=lambda l: l.top)
            cells.append(Cell(min(l.x0 for l in lines), max(l.x1 for l in lines),
                              min(l.top for l in lines), max(l.top + l.size for l in lines), lines))
        cells.sort(key=lambda c: c.x0)
        return cells

    def row(self, page: int, row: Row, body: float, state) -> None:
        cells = row.cells
        filled = [c for c in cells if c.text.strip()]
        if not filled:
            return
        if len(filled) == 1 and any(len(line.segments) >= 2 for line in filled[0].lines):
            parts = self.split_cell(filled[0], state["leaves"])
            if len(parts) >= 2:
                row = Row(parts, False)
                cells = filled = parts
        header = self.header_cells(row, body, state)
        if header:
            lead_text, names = header
            new = [Leaf(disp(c.text), c.x0, c.x1) for c in names]
            prev = state["prev_header"]
            if prev is not None:
                merged, used = [], set()
                for upper in prev:
                    below = [leaf for leaf in new if covers(Cell(upper.x0, upper.x1, 0, 0), leaf)]
                    if not below:
                        merged.append(upper)
                        continue
                    for leaf in below:
                        used.add(id(leaf))
                        same = leaf.label == upper.label or upper.label in leaf.label
                        merged.append(Leaf(leaf.label if same else f"{upper.label} {leaf.label}", leaf.x0, leaf.x1))
                merged += [leaf for leaf in new if id(leaf) not in used]
                merged.sort(key=lambda leaf: leaf.x0)
                state["leaves"] = merged
                if lead_text:
                    state["sub"] = disp(f"{state['sub']} {lead_text}") if lead_text.startswith("(") else lead_text
            else:
                labels = [leaf.label for leaf in new]
                older = state["leaves"]
                if len(set(labels)) < len(labels) and older and len(older) < len(new):
                    # repeated names ("Limited" under ICE, HEV and PHEV): prefix the column group of
                    # the previous header when every column sits under exactly one of its columns
                    groups = []
                    for leaf in new:
                        hit = [o for o in older if o.x0 - 2 <= (leaf.x0 + leaf.x1) / 2 <= o.x1 + 2]
                        groups.append(hit[0] if len(hit) == 1 else None)
                    if all(groups):
                        new = [Leaf(leaf.label if g.label in leaf.label else f"{g.label} {leaf.label}", leaf.x0, leaf.x1)
                               for g, leaf in zip(groups, new)]
                state["leaves"] = new
                if lead_text:
                    if upper_title(lead_text) and SECTION_RE.search(lead_text):
                        state["section"], state["sub"] = lead_text, ""
                    else:
                        state["sub"] = lead_text
                state["engine"] = ""
            state["prev_header"] = state["leaves"]
            return
        state["prev_header"] = None
        leaves = state["leaves"]
        start = min((l.x0 for l in leaves), default=None)

        # single filled cell: a title, a sub-heading, or label/value split by a wide gap
        lone_value = len(filled) == 1 and start is not None and filled[0].center >= start - 1 and row.first_missing
        if len(filled) == 1 and not lone_value:
            cell = filled[0]
            if any(len(line.segments) >= 2 for line in cell.lines):
                self.single_cell(page, cell, state)
                return
            text = disp(cell.text)
            if TITLE_RE.search(text) and (upper_title(text) or cell.size > body + 0.8):
                if upper_title(text) and len(text) < 45 and SECTION_RE.search(text):
                    state["section"], state["sub"] = text, ""
                else:
                    state["sub"] = text
                state["engine"] = ""
                return
            if "TRANSMISSION" in (state["section"] + " " + state["sub"]).upper() and re.search(
                    r"(?i)speed|cvt|ivt|dct|automatic|manual", text):
                self.add_entry(page, state, "", "Transmission", text, None, [text], text)
                return
            # an engine heading inside the ENGINE block: "2.4L (SE/SEL/Sport/Limited)"
            if re.search(r"(?i)engine", state["section"] + " " + state["sub"]) and re.match(
                    r"(?i)^\d\.\d\s*[LT]?\b|^(smartstream|theta|nu|gamma|kappa|lambda)\b", text) and len(text) < 60:
                state["engine"] = text
                self.engine_subs.append(text)
                return
            if len(text) < 60:
                state["sub"] = text
                state["engine"] = ""  # a new block ends the engine heading
            return

        # label cells left of the first column, value cells under the columns
        if start is not None:
            label_cells = [c for c in filled if c.center < start - 1 and not any(covers(c, l) for l in leaves)]
            value_cells = [c for c in filled if c not in label_cells]
        else:
            label_cells, value_cells = filled[:1], filled[1:]
        if not value_cells:
            if len(label_cells) >= 2:
                # a group label, an item and nothing under the columns
                label_cells, value_cells = label_cells[:-1], label_cells[-1:]
            else:
                state["sub"] = disp(" ".join(c.text for c in label_cells))[:80]
                return
        inherited = ""
        if row.first_missing or (label_cells and cells[0] not in label_cells and not cells[0].text.strip()):
            inherited = state["last_label"]  # the label cell of the row above spans this row
        if not label_cells:
            group, sub_cell = inherited, None
            span = state.get("label_cell") if row.first_missing else None
        else:
            parts = [disp(c.text) for c in label_cells[:-1]]
            group = disp(" ".join(filter(None, [inherited] + parts)))
            sub_cell = label_cells[-1]
            span = sub_cell
            state["label_cell"] = sub_cell
            if not inherited:
                state["last_label"] = disp(label_cells[0].text)
        line_label = self.merged_label_line(span, sub_cell is None, value_cells)
        self.data_row(page, state, leaves, group, sub_cell, value_cells, cells, line_label)

    @staticmethod
    def merged_label_line(span: Cell | None, inherited: bool, value_cells: list[Cell]) -> str | None:
        """A label cell merged over several table rows lists one label per row: the line at the
        height of this row's value is its label ('Type' / 'Size (diameter, in)')."""
        if span is None or len(span.lines) < 2 or not value_cells or any(len(c.lines) != 1 for c in value_cells):
            return None
        if all(is_mark(c.text) for c in value_cells):
            return None  # S / O rows name their item with the whole label cell
        tops = [c.lines[0].top for c in value_cells]
        if max(tops) - min(tops) > 2.6:
            return None
        if not inherited and span.bottom <= max(c.bottom for c in value_cells) + 2:
            return None  # the label cell ends with this row: its lines are one wrapped label
        match = [line for line in span.lines if abs(line.top - tops[0]) <= 2.6]
        return disp(match[0].text) if len(match) == 1 else None

    def leaves_of(self, cell: Cell, leaves: list[Leaf]) -> list[Leaf]:
        return [leaf for leaf in leaves if covers(cell, leaf)]

    def engine_text_for(self, covered: list[Leaf], leaves: list[Leaf], state) -> str | None:
        if leaves and covered and len(covered) < len(leaves):
            return " / ".join(leaf.label for leaf in covered)
        if state["engine"]:
            return state["engine"]
        return None

    def data_row(self, page, state, leaves, group, sub_cell: Cell | None, value_cells: list[Cell], cells,
                 line_label: str | None = None) -> None:
        sub_lines = sub_cell.lines if sub_cell else []
        label_text = disp(sub_cell.text) if sub_cell else ""
        if line_label:
            values = [(cell, disp(cell.text), self.leaves_of(cell, leaves)) for cell in value_cells]
            row_text = disp(" ".join([group, line_label] + [text for _, text, _ in values]))
            self.emit_row(page, state, leaves, group, line_label, values, row_text, label_full=line_label, cell_texts=[])
            return
        row_text = " ".join(disp(c.text) for c in sorted([c for c in cells if c.text.strip()], key=lambda c: c.x0))
        # stacked cells: several value lines next to several label lines at the same height
        if sub_cell and len(sub_lines) > 1 and value_cells and all(is_mark(c.text) for c in value_cells) \
                and sum(1 for line in sub_lines if re.search(r"\S:\s*\S", line.text)) >= 2:
            self.colon_list(page, state, leaves, group, sub_cell, value_cells, row_text)
            return
        multi = [c for c in value_cells if len(c.lines) > 1]
        if multi and len(sub_lines) > 1:
            self.stacked(page, state, leaves, group, sub_cell, value_cells, row_text)
            return
        values = []
        for cell in value_cells:
            text = disp(cell.text)
            values.append((cell, text, self.leaves_of(cell, leaves)))
        self.emit_row(page, state, leaves, group, label_text, values, row_text,
                      label_full=" ".join(filter(None, [group, label_text])), cell_texts=[sub_cell.text if sub_cell else ""] + [c.text for c in value_cells])

    def emit_row(self, page, state, leaves, group, label, values, row_text, label_full, cell_texts) -> None:
        """One label with one value per value cell: collapse equal values, mark rows, engine_text."""
        if not values:
            return
        if any(GLYPH.match(v[1]) for v in values):
            self.review.append({"page": page, "row": row_text,
                                "reason": "columns holding a symbol glyph (reference to another column) not read"})
            values = [v for v in values if not GLYPH.match(v[1])]
        if any(GARBLED.search(v[1]) for v in values):
            self.review.append({"page": page, "row": row_text, "reason": "letter-spaced text in a value cell not read"})
            values = [v for v in values if not GARBLED.search(v[1])]
        if not values:
            return
        texts = [text for _, text, _ in values]
        joined_values = " ".join(texts)
        mark_row = all(is_mark(t) for t in texts)
        if mark_row:
            available = [(cell, t, cov) for cell, t, cov in values if disp(t).upper() in AVAILABLE]
            if not available:
                return
            covered = [leaf for _, _, cov in available for leaf in cov]
            if leaves and not covered:
                self.review.append({"page": page, "row": row_text, "reason": "S/O marks outside the header columns"})
                return
            optional = any(disp(t).upper() in {"O", "P", "OPT", "OPT."} for _, t, _ in available)
            if leaves and (len(covered) < len(leaves) or optional):
                engine = " / ".join(
                    f"{leaf.label}" + (" (O)" if disp(t).upper() == "O" else "") + (" (P)" if disp(t).upper() == "P" else "")
                    for _, t, cov in available for leaf in cov)
            else:
                engine = state["engine"] or None
            item = label
            self.add_entry(page, state, group, item, item, engine,
                           [f"{label} {joined_values}", row_text, label], row_text, mark_row=True)
            return
        by_text: dict[str, list] = defaultdict(list)
        for cell, text, cov in values:
            if disp(text).upper() in EMPTY_VALUES:
                continue
            by_text[text].append((cell, cov))
        if not by_text:
            return
        all_cover = [leaf for _, _, cov in values for leaf in cov]
        if len(by_text) == 1:
            text, cells = next(iter(by_text.items()))
            covered = [leaf for _, cov in cells for leaf in cov]
            if leaves and not covered:
                self.review.append({"page": page, "row": row_text, "reason": "value outside the header columns"})
                return
            engine = self.engine_text_for(covered, leaves, state)
            self.add_entry(page, state, group, label, text, engine,
                           [f"{label} {joined_values}", f"{label} {text}", row_text, text], row_text)
            return
        if not leaves:
            self.review.append({"page": page, "row": row_text, "reason": "several values without column labels"})
            return
        for text, cells in by_text.items():
            covered = [leaf for _, cov in cells for leaf in cov]
            if not covered:
                self.review.append({"page": page, "row": row_text, "reason": "value outside the header columns"})
                continue
            engine = " / ".join(leaf.label for leaf in covered) if len(covered) < len(leaves) else (state["engine"] or None)
            self.add_entry(page, state, group, label, text, engine,
                           [f"{label} {joined_values}", f"{label} {text}", row_text, text], row_text)
        del all_cover

    def colon_list(self, page, state, leaves, group, sub_cell: Cell, value_cells: list[Cell], row_text: str) -> None:
        """A label cell listing 'Name: value' lines for the columns marked S / O."""
        marked = [c for c in value_cells if disp(c.text).upper() in AVAILABLE]
        if not marked:
            return
        covered = [leaf for c in marked for leaf in self.leaves_of(c, leaves)]
        if leaves and not covered:
            self.review.append({"page": page, "row": row_text, "reason": "S/O marks outside the header columns"})
            return
        engine = self.engine_text_for(covered, leaves, state)
        items: list[list[str]] = []
        for n, line in enumerate(sub_cell.lines):
            text = disp(line.text)
            pair = re.match(r"(.+?):\s*(\S.*)$", text)
            if pair and not re.match(r"^\d", pair.group(1)):
                items.append([pair.group(1).strip(), pair.group(2).strip(), text])
            elif n == 0:
                items.append(["Engine" if SELF_ENGINE.search(text) else "", text, text])
            elif items:
                items[-1][1] = f"{items[-1][1]} {text}"  # the line wraps inside the label cell
                items[-1][2] = f"{items[-1][2]} {text}"
        desc = next((value for label, value, _ in items if label == "Engine"), "")
        if desc:
            # the engine named on the first line, with the columns it is marked for
            engine = f"{desc} ({engine})" if engine else desc
        for label, value, line in items:
            if label:
                self.add_entry(page, state, group, label, value, engine, [line, value], line)

    @staticmethod
    def pair_lines(sub_lines: list[Line], cell: Cell) -> dict[int, str] | None:
        """Label line index -> value text for one value cell, or None when the lines do not pair."""
        tol = 2.6
        result: dict[int, list] = {}
        current = None
        aligned = True
        for line in cell.lines:
            match = [i for i, lab in enumerate(sub_lines) if abs(lab.top - line.top) <= tol]
            if len(match) == 1 and match[0] not in result:
                result[match[0]] = [line.text, line.top]
                current = match[0]
            else:
                aligned = False
                break
        if aligned and result:
            return {i: text for i, (text, _) in result.items()}
        lines = list(cell.lines)
        if len(lines) > len(sub_lines) and all(is_mark(l.text) for l in lines[:len(sub_lines)]):
            lines = lines[:len(sub_lines)]  # S / - marks followed by a caption ("16-in Alloy (SE)")

        def steady(labels: list[Line], values: list[Line]) -> bool:
            # the same vertical offset for every pair: both lists are evenly spaced (centred cells)
            offsets = [v.top - l.top for l, v in zip(labels, values)]
            return max(offsets) - min(offsets) <= 3.0

        if len(lines) == len(sub_lines) and steady(sub_lines, lines):
            return {i: line.text for i, line in enumerate(lines)}
        if len(lines) == len(sub_lines) - 1 and steady(sub_lines[1:], lines) and sub_lines[0].top < lines[0].top - tol:
            return {i + 1: line.text for i, line in enumerate(lines)}  # first label line heads the list
        return None

    def stacked(self, page, state, leaves, group, sub_cell: Cell, value_cells: list[Cell], row_text: str) -> None:
        """Label lines and value lines inside single cells: paired by height, else by order."""
        sub_lines = list(sub_cell.lines)
        if any(HP_RE.search(line.text) and "@" in line.text or TQ_RE.search(line.text) and "@" in line.text
               for cell in value_cells for line in cell.lines):
            self.engine_lineup(page, state, leaves, group, sub_cell, value_cells, row_text)
            return
        pairs: dict[int, list] = defaultdict(list)
        for cell in value_cells:
            if len(cell.lines) == 1 and not is_mark(cell.text):
                # one value next to a label of several lines: the label wraps
                pairs[-1].append((cell, cell.text))
                continue
            mapped = self.pair_lines(sub_lines, cell)
            if mapped is None:
                self.review.append({"page": page, "row": row_text,
                                    "reason": "stacked cell: value lines do not pair with the label lines: "
                                    + " | ".join(disp(l.text) for l in cell.lines)})
                continue
            for index, text in mapped.items():
                pairs[index].append((cell, text))
        if -1 in pairs:
            label = disp(sub_cell.text)
            values = [(cell, disp(text), self.leaves_of(cell, leaves)) for cell, text in pairs.pop(-1)]
            self.emit_row(page, state, leaves, group, label, values, row_text, label_full=label, cell_texts=[])
        if not pairs:
            return
        indices = sorted(pairs)
        title = group
        if indices[0] > 0:
            head = disp(" ".join(line.text for line in sub_lines[:indices[0]]))
            title = disp(f"{group} {head}")
        stack_group = ""
        for index in indices:
            label_line = sub_lines[index]
            label = disp(label_line.text)
            line_group = title
            if len(label_line.segments) >= 2:
                stack_group = disp(f"{title} {label_line.segments[0][0]}")
                label = disp(" ".join(seg[0] for seg in label_line.segments[1:]))
            if stack_group:
                line_group = stack_group
            values = [(cell, disp(text), self.leaves_of(cell, leaves)) for cell, text in pairs[index]]
            self.emit_row(page, state, leaves, line_group, label, values, row_text, label_full=label, cell_texts=[])

    def engine_lineup(self, page, state, leaves, group, sub_cell: Cell, value_cells: list[Cell], row_text: str) -> None:
        """An engine row: description lines on the left; S mark, hp and lb-ft lines under the columns."""
        fitted = [c for c in value_cells
                  if any(disp(l.text).upper() in AVAILABLE or HP_RE.search(l.text) or TQ_RE.search(l.text) for l in c.lines)]
        covered = [leaf for c in fitted for leaf in self.leaves_of(c, leaves)]
        engine = self.engine_text_for(covered, leaves, state)
        for n, line in enumerate(sub_cell.lines):
            text = disp(line.text)
            label = "Engine" if n == 0 and SELF_ENGINE.search(text) else "Engine detail"
            self.add_entry(page, state, group or "Engine", label, text, engine, [text, row_text], text)
        for cell in fitted:
            cell_engine = self.engine_text_for(self.leaves_of(cell, leaves), leaves, state)
            for line in cell.lines:
                text = disp(line.text)
                if HP_RE.search(text) or TQ_RE.search(text):
                    self.add_entry(page, state, group or "Engine", "Output", text, cell_engine, [text, row_text], text)

    def single_cell(self, page, cell: Cell, state) -> None:
        """A cell whose lines hold label and value separated by a wide gap."""
        leaves = state["leaves"]
        for line in cell.lines:
            if len(line.segments) < 2:
                text = disp(line.text)
                if re.search(r"(?i)speed|cvt|automatic", text) and "TRANSMISSION" in (state["section"] + state["sub"]).upper():
                    continue
                continue
            label = disp(line.segments[0][0])
            parts = line.segments[1:]
            values = []
            for text, x0, x1 in parts:
                seg_cell = Cell(x0, x1, line.top, line.top + line.size, [])
                values.append((seg_cell, disp(text), self.leaves_of(seg_cell, leaves)))
            row_text = disp(line.text)
            self.emit_row(page, state, leaves, "", label, values, row_text, label_full=label, cell_texts=[])

    def add_entry(self, page, state, group, label, value, engine, quotes, original, mark_row=False) -> None:
        if MOTOR_ROW.search(f"{group} {label}"):
            state["motor_block"] = (state["section"], state["sub"])
        in_motor = state.get("motor_block") == (state["section"], state["sub"])
        self.entries.append(Entry(page=page, section=state["section"], sub=state["sub"], group=group, label=label,
                                  value=value, engine_text=engine, quotes=quotes, original=disp(original),
                                  mark_row=mark_row, motor_ctx=in_motor))

    # -- facts ------------------------------------------------------------------------------
    def facts(self) -> tuple[list[dict], list[dict]]:
        raw: list[tuple] = []
        multi_engine = len(set(self.engine_subs)) > 1
        blocks: dict[tuple, list[str]] = defaultdict(list)
        for entry in self.entries:
            blocks[(entry.section, entry.sub)].append(disp(f"{entry.group} {entry.label}"))
        for entry in self.entries:
            unit_ctx = " | ".join(blocks[(entry.section, entry.sub)])
            map_entry(entry, multi_engine, raw, self.review, unit_ctx)
            self.self_described(entry, raw)
        facts, seen = [], set()
        for key, value, entry, value_text in raw:
            if value is None or value == "":
                continue
            quote = self.quote(entry, value_text)
            if quote is None:
                self.review.append({"page": entry.page, "row": entry.original,
                                    "reason": f"{key}: no verbatim quote found in the page text"})
                continue
            fact = {"key": key, "value": value, "page": entry.page, "quote": quote, "original": entry.original,
                    "engine_text": entry.engine_text, "row": disp(" ".join(filter(None, [entry.group, entry.label])))}
            ident = (key, json.dumps(value), entry.engine_text, fact["row"])
            if ident in seen:
                continue
            seen.add(ident)
            facts.append(fact)
        # review only rows that could hold one of the fact keys (feature tables are not listed)
        self.review = [item for item in self.review if KEY_WORDS.search(item["row"]) or ":" in item["reason"][:40]]
        return facts, self.review

    def self_described(self, entry: Entry, raw: list) -> None:
        """hp / lb-ft / cc / bore x stroke written inside the label or value text of an entry."""
        if entry.mark_row:
            texts = [entry.label]
        else:
            texts = [entry.label, entry.value]
        ctx = disp(f"{entry.section} {entry.sub} {entry.group} {entry.label}").upper()
        motor = bool(MOTOR_CTX.search(ctx)) and "MOTOR MOUNT" not in ctx and "STEERING" not in ctx
        combined = bool(re.search(r"COMBINED|SYSTEM", ctx))
        for text in texts:
            text = disp(text)
            if not text:
                continue
            if not motor and not combined and not re.search(r"(?i)horsepower|power|torque", entry.label):
                for hp in HP_RE.finditer(text):
                    if hp.group(2) or "@" in text:
                        raw.append(("power_hp", num(hp.group(1)), entry, text))
                        if hp.group(2):
                            raw.append(("power_rpm", hp.group(2).replace(" ", ""), entry, text))
                if not re.search(r"(?i)torque", entry.label):
                    for tq in TQ_RE.finditer(text):
                        if tq.group(2) or "@" in text:
                            raw.append(("torque_lb_ft", num(tq.group(1)), entry, text))
                            if tq.group(2):
                                raw.append(("torque_rpm", tq.group(2).replace(" ", ""), entry, text))
            if combined and not motor and re.search(r"(?i)combined (horse)?power|system (horse)?power", text):
                hp = HP_RE.search(text)
                if hp and not re.search(r"(?i)horsepower|power", entry.label):
                    raw.append(("system_power_hp", num(hp.group(1)), entry, text))
            if not re.search(r"(?i)displacement", entry.label):
                for cc in CC_RE.finditer(text):
                    raw.append(("engine_displacement_cc", num(cc.group(1)), entry, text))
            bore = re.search(r"(?i)bore\s*(&|and)\s*stroke\s*(\((mm|in\.?)\))?\s*:\s*([\d.]+)\s*[xX×]\s*([\d.]+)", text)
            if bore and not re.search(r"(?i)bore", entry.label):
                unit = (bore.group(3) or "").lower()
                if unit.startswith("mm"):
                    raw.append(("bore_stroke_mm", f"{bore.group(4)} x {bore.group(5)}", entry, text))
                elif unit.startswith("in"):
                    raw.append(("bore_stroke_in", f"{bore.group(4)} x {bore.group(5)}", entry, text))
            if SELF_ENGINE.search(text) and re.search(r"(?i)\d\.\d\s*-?\s*L\b|liter", text) \
                    and re.search(r"(?i)engine|lineup|powertrain", ctx) and len(text) < 160 \
                    and not re.search(r"(?i)\bhp\b|\blb", text):
                desc = re.split(r"(?i)\s*(?:bore\s*(?:&|and)\s*stroke|displacement\s*:)", text)[0].strip().rstrip(",;")
                raw.append(("engine_description", desc, entry, desc))

    def quote(self, entry: Entry, value_text: str) -> str | None:
        page = self.texts[entry.page - 1] if entry.page - 1 < len(self.texts) else None
        if page is None:
            return None
        value_text = norm_ws(value_text)
        candidates = []
        for cand in entry.quotes + [value_text]:
            cand = norm_ws(cand)
            if cand and value_text and norm_key(value_text) in norm_key(cand) and cand not in candidates:
                candidates.append(cand)
        for cand in candidates:
            found = page.find(cand)
            if found:
                return found
        return None


def norm_key(text: str) -> str:
    return "".join(c.translate(FOLD).lower() for c in (text or "") if not c.isspace())


# ---------------------------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------------------------
def load_rows(host: str) -> dict[str, list[dict]]:
    path = MANIFEST_DIR / f"{host}.csv"
    docs: dict[str, list[dict]] = defaultdict(list)
    if not path.exists():
        return docs
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["doc_type"] == "press_specifications" and row["status"] == "ok" and row["sha256"]:
                docs[row["sha256"]].append(row)
    return docs


def pagetext(sha: str) -> list[str]:
    with gzip.open(RAW_ROOT / "pagetext" / f"{sha}.json.gz", "rt", encoding="utf-8") as handle:
        return json.load(handle)["pages"]


def build(host: str, rows: list[dict]) -> tuple[Path, dict]:
    short, publisher = HOSTS[host]
    first = rows[0]
    sha = first["sha256"]
    lines = sorted({row["line"] for row in rows})
    years = sorted({int(row["year"]) for row in rows})
    line = BY_KEY[first["line"]]
    key = f"press-{short}-{line.slug}-{first['year']}-{sha[:8]}"
    pages = pagetext(sha)
    parser = DocParser(RAW_ROOT / first["path"], pages)
    parser.parse()
    facts, review = parser.facts()
    doc = {
        "doc": {
            "key": key, "make": line.make, "lines": lines, "years": years, "doc_type": "press_specifications",
            "title": first["title"], "path": str(RAW_ROOT / first["path"]), "url": first["url"], "page_url": "",
            "sha256": sha, "retrieved_at": first["retrieved_at"], "tier": "A", "source_type": "PRESS_RELEASE",
            "publisher": publisher, "authenticity": "OFFICIAL_PUBLISHER",
        },
        "extractor": EXTRACTOR,
        "pages": len(pages),
        "edition_market": "US",
        "status": "ok" if facts else "no_facts",
        "engine_codes": [],
        "review": dedupe(review),
        "facts": facts,
    }
    out = WORK / line.make / "extracted" / f"{key}.json"
    return out, doc


def dedupe(items: list[dict]) -> list[dict]:
    seen, out = set(), []
    for item in items:
        ident = json.dumps(item, sort_keys=True)
        if ident not in seen:
            seen.add(ident)
            out.append(item)
    return out


def verify(paths: list[Path], sample: int = 5) -> int:
    """Every quote is found in its page text; print a random sample of facts for a manual check."""
    bad, total, all_facts = 0, 0, []
    for path in paths:
        doc = json.loads(path.read_text(encoding="utf-8"))
        pages = pagetext(doc["doc"]["sha256"])
        normalised = [norm_ws(p) for p in pages]
        for fact in doc["facts"]:
            total += 1
            if norm_ws(fact["quote"]) not in normalised[fact["page"] - 1]:
                bad += 1
                print(f"QUOTE NOT FOUND {path.name} p{fact['page']} {fact['key']}: {fact['quote'][:80]}")
            all_facts.append((path.name, fact))
    print(f"verify: {total} facts, {bad} quotes not found")
    for name, fact in random.sample(all_facts, min(sample, len(all_facts))):
        print(f"SAMPLE {name} p{fact['page']} {fact['key']}={fact['value']!r} engine_text={fact['engine_text']!r} "
              f"row={fact['row']!r} quote={fact['quote'][:120]!r}")
    return bad


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=list(HOSTS), action="append")
    parser.add_argument("--only", help="process documents whose stored file name contains this text")
    parser.add_argument("--dry", action="store_true", help="print, do not write")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    written = []
    per_key: Counter = Counter()
    for host in args.host or list(HOSTS):
        docs = load_rows(host)
        print(f"== {host}: {len(docs)} documents")
        for sha, rows in sorted(docs.items(), key=lambda item: item[1][0]["path"]):
            if args.only and args.only not in rows[0]["path"]:
                continue
            if not rows[0]["path"].lower().endswith(".pdf"):
                print(f"skipped (not a PDF, no page text): {rows[0]['path']}")
                continue
            out, doc = build(host, rows)
            counts = Counter(f["key"] for f in doc["facts"])
            per_key.update(counts)
            print(f"{out.name}: {len(doc['facts'])} facts, {len(doc['review'])} review | "
                  + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
            if args.dry:
                for fact in doc["facts"]:
                    print(f"   p{fact['page']} {fact['key']}={fact['value']!r} [{fact['engine_text']}] <{fact['row']}>")
                for item in doc["review"]:
                    print(f"   REVIEW p{item['page']} {item['reason']}: {item['row'][:100]}")
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
            written.append(out)
    print("facts per key: " + ", ".join(f"{k}={v}" for k, v in sorted(per_key.items())))
    if args.verify and written:
        return 1 if verify(written) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Tire sizes and cold tire pressures from the tire tables of the US mycarusermanual.com editions
of Volkswagen and BMW (owner's decision 2026-10-04: "tables may be read by coordinates; what is
ambiguous is not written").

The site serves each manual page as absolutely positioned text blocks (scripts/extract_mcum_facts.py).
A tire table is rebuilt from the block coordinates:

BMW (two page columns; read left column, then right column, page after page of one section)
- the table header is the line "Tire size | Pressure specifications in bar/PSI"; the first value
  column is the front axle and the second the rear axle (rows "Front: … 2.3 / 33 -" and
  "Rear: … - 2.6 / 38" show the order);
- a size cell wraps over 2-3 lines ("225/55 R 17 97 H" + "A/S"); a cell may list several sizes
  that share the pressures printed at the top of the cell; a "Front:"/"Rear:" (or "F.:"/"R.:")
  cell may carry two pressure lines, one per size, in order;
- the model heading ("530i, 530i xDrive") printed before a table names the designations it is for
  (one fact per designation); the speed section headings ("Tire pressure values up to / over
  100 mph/160 km/h") say which tables hold the everyday pressures: pressures are kept only from the
  "up to 100 mph/160 km/h" tables and carry that as a condition; "over 100 mph" tables give sizes
  only; emergency-wheel rows are skipped (no field for a spare tire);
- a designation that another line of the registry claims (the "M5" tables of a manual filed under
  the 5 Series line) is not written to this line.

VW (one column)
- header "Model | Size designation | Tire pressure (psi / kPa / bar)" (or "Engine", "Drive train");
  the label cell of the first column spans its rows and is printed at their middle (or at the
  first row); rows are bound to labels by a partition in which every label lies within its rows
  and no label gets the same tire size twice; a row that two such partitions bind differently is
  not written; tables marked "Applicable only in Canada" are skipped; compact/temporary spare rows
  are skipped;
- one pressure per tire size (the table has no front/rear split): written as the front and the
  rear pressure, kPa as printed (checked against bar x 100 and psi).

Every quote is a verbatim span of the page text extract_mcum_facts builds (the text of the blocks
of the row); the model heading and the speed heading are kept as further cites of the fact.

The pass is called by scripts/extract_mcum_facts.py for these two makes; run alone it adds the tire
facts to the existing data_work/<make>/extracted/mcum-*.json documents (replacing earlier tire
facts) after checking that the page texts are the ones the document was built from.

  uv run --no-project --with pdfplumber --with pypdfium2 python scripts/extract_mcum_tires.py [volkswagen|bmw] [--dry-run]
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import html as htmlmod
import itertools
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_mcum_facts import BLOCK, EM_TO_PT, PAGE_SPLIT, words_of  # noqa: E402
from extract_manual_facts import norm  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import BY_KEY, LINES, MAKES  # noqa: E402

TIRE_MAKES = {"volkswagen", "bmw"}
TIRE_PASS = "tires-1"
LAYOUT = "mcum_tire_table"

PRESSURE = re.compile(r"^(\d\.\d)\s*/\s*(\d{2})$")
TAIL_PRESSURE = re.compile(r"^(.*?)\s*(\d\.\d\s*/\s*\d{2})$")
SIZE_CORE = re.compile(r"\d{3}/\d{2}\s?Z?R\s?\d{2}(?!\d)")
GLUED = re.compile(r"^(\d{3}/\d{2})(Z?R)(\d{2})(\d{2,3})([A-Z])(XL)?$")
POSITION = re.compile(r"^(Front:|Rear:|F\.:|R\.:)\s*")
SPARE_START = re.compile(r"^(?:Emergency\b|T ?\d{3}/\d{2})")
FRAGMENT = re.compile(r"^(?:[0-9A-Z+/().★*-]+|Std|xl)(?: (?:[0-9A-Z+/().★*-]+|Std|xl))*$")
BMW_HEADER = re.compile(r"^(?:Tire size|Pressure specifica.*|tions in bar/PSI|in bar/PSI|bar/PSI|Specifications(?: in.*)?|in bar/PSI with"
                        r"|bar/PSI with(?: cold)?|cold tires|tires|PSI with cold tires|kilopascal with cold)$")
BMW_PRESSURE_TEXT = re.compile(r"^(?:Speed up to a max\. of|\d+ mph / \d+ km/h|tions in bar/PSI|in bar/PSI|bar/PSI|Pressure specifica.*)$")
SPEED_HEAD = re.compile(r"^Tire (?:inflation )?pressures?(?: values)?\s+(?:(?P<up>up)\s+to|(?P<over>over)|at max\. speeds (?P<above>above))\s+"
                        r"100 mph/\s?160 km/h$")
SUBCONDITION = re.compile(r"^(?:With|Without) (?:high-speed tuning feature|speed limiter|M Driver's Package):?$")
DESIG = (r"(?:X\d\s)?(?:M?\d{3}(?:i|d|e|Li|Le|Ld|xe)|M\d{2}i|M\d(?:\sCS|\sCompetition)?|[xs]Drive\d{2}[ied])"
         r"(?:\s(?:xDrive|sDrive))?")
HEADING = re.compile(rf"^(?P<list>{DESIG}(?:,\s?{DESIG})*)(?P<comma>,)?(?:\s(?P<equipment>M Sport))?$")
DESIG_RE = re.compile(DESIG)

# VW
VW_SIZE_HEAD = re.compile(r"^(?:Size designation|Tire size|Tire dimensions)$")
VW_LABEL_HEAD = re.compile(r"^(?:Model|Engine|Drive train)$")
VW_UNIT = re.compile(r"\b(psi|kpa|bar)\b", re.I)
VW_END = re.compile(r"^(?:Applicable only|Details|Manual,|Monitoring|Tread|The |xl = |If |Fig\.|NOTICE|WARNING|Replacing)")
MARKET = re.compile(r"^Applicable only in (the United States|Canada)$")
VW_SPARE_LABEL = re.compile(r"spare", re.I)


# ---- pages ----------------------------------------------------------------------------------------
def positioned_words(part: str) -> tuple[list[dict], str]:
    """words_of() of scripts/extract_mcum_facts.py, with each block's offset in the page text."""
    words, chunks, offset = [], [], 0
    for left, top, inner in BLOCK.findall(part):
        text = norm(htmlmod.unescape(re.sub(r"<[^>]+>", "", inner)))
        if not text:
            continue
        x0, y0 = float(left) * EM_TO_PT, float(top) * EM_TO_PT
        words.append({"text": text, "x0": x0, "top": y0, "start": offset, "end": offset + len(text)})
        chunks.append(text)
        offset += len(text) + 1
    return words, " ".join(chunks)


def edition_pages(site_make: str, model: str, body: str, years: str) -> tuple[list[dict], str]:
    """The edition's pages in the order and numbering of extract_mcum_facts.main(), and the
    sha256 it computes for the edition (the page text store key)."""
    with (WORK / "_mcum" / "manifest.csv").open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["http_status"] == "200" and r["body"]
                and (r["make"], r["model"], r["body"], r["years"]) == (site_make, model, body, years)]
    folder = RAW_ROOT / "_mcum" / site_make / model / f"{body}_{years}"
    pages, digests = [], []
    for row in sorted(rows, key=lambda r: r["section"]):
        name = row["section"] or "_index"
        path = folder / f"{name}.html.gz"
        if not path.exists():
            path = folder / f"{name}.html"
        if not path.exists():
            continue
        raw = gzip.decompress(path.read_bytes()).decode("utf-8") if path.suffix == ".gz" else path.read_text(encoding="utf-8")
        digests.append(row["sha256"])
        parts = PAGE_SPLIT.split(raw)
        parts = parts[1:] if len(parts) > 1 else parts
        parsed = [positioned_words(p) for p in parts]
        ocr_path = folder / f"{name}.ocr.json"
        if ocr_path.exists() and sum(len(t) for _, t in parsed) < 200:
            for ocr_page in json.loads(ocr_path.read_text(encoding="utf-8"))["pages"]:
                pages.append({"number": len(pages) + 1, "section": name, "url": row["url"], "words": None, "text": ocr_page["text"]})
            continue
        for part, (words, text) in zip(parts, parsed, strict=True):
            if text != words_of(part)[1]:
                raise RuntimeError(f"{folder} {name}: page text differs from extract_mcum_facts.words_of")
            pages.append({"number": len(pages) + 1, "section": name, "url": row["url"], "words": words, "text": text})
    return pages, hashlib.sha256("".join(digests).encode()).hexdigest()


def lines_of(words: list[dict], tol: float = 1.5) -> list[dict]:
    """Blocks grouped into lines by top (sorted by x within a line)."""
    out = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if out and abs(out[-1]["top"] - w["top"]) <= tol:
            out[-1]["blocks"].append(w)
        else:
            out.append({"top": w["top"], "blocks": [w]})
    for line in out:
        line["blocks"].sort(key=lambda w: w["x0"])
        line["text"] = " ".join(b["text"] for b in line["blocks"])
    return out


def span(page: dict, blocks: list[dict]) -> str:
    """The verbatim page-text span covering the blocks."""
    return page["text"][min(b["start"] for b in blocks): max(b["end"] for b in blocks)]


def kpa_of_bar(bar: str) -> int:
    value = Decimal(bar) * 100
    if value != value.to_integral_value():
        raise ValueError(bar)
    return int(value)


def clean_size(text: str) -> str:
    text = re.sub(r"M\s*\+\s*S", "M+S", " ".join(text.split()))
    glued = GLUED.match(text)
    if glued:  # "245/40R2099YXL": the same characters, spaced as the other rows print them
        a, r, rim, load, speed, xl = glued.groups()
        text = f"{a} {r} {rim} {load} {speed}" + (f" {xl}" if xl else "")
    return text


# ---- line membership --------------------------------------------------------------------------------
def claimed_elsewhere(designation: str, line_key: str) -> str | None:
    """Another line of the registry whose EPA model pattern names this designation while the
    document's own line does not ("M5" in a manual filed under the 5 Series line)."""
    own = BY_KEY[line_key]
    if re.search(own.epa_include, designation) and not (own.epa_exclude and re.search(own.epa_exclude, designation)):
        return None
    for other in LINES:
        if other.make == own.make and other.key != line_key and other.epa_include not in (r".*", ".*"):
            if re.search(other.epa_include, designation):
                return other.key
    if own.epa_exclude and re.search(own.epa_exclude, designation):
        return "excluded from " + line_key
    return None


# ---- BMW ---------------------------------------------------------------------------------------------
def bmw_columns(page: dict) -> list[list[dict]]:
    words = [w for w in page["words"] if 30 < w["top"] < 560]
    return [lines_of([w for w in words if w["x0"] < 200]), lines_of([w for w in words if w["x0"] >= 200])]


class Entry:
    def __init__(self, page, top, position):
        self.page, self.top, self.position = page, top, position
        self.parts, self.blocks = [], []
        self.pressures = []  # [(front block|None, rear block|None, merged text|None, top)]
        self.spare = False

    @property
    def size(self) -> str:
        return clean_size(" ".join(self.parts))

    def has_size(self) -> bool:
        return bool(SIZE_CORE.search(" ".join(self.parts)))


def bmw_tables(pages: list[dict]) -> list[dict]:
    """Every BMW tire table of the edition: [{section, condition, subcondition, heading, groups,
    unresolved}] where groups are lists of (entry, (front, rear)) and unresolved lists entries
    whose pressures could not be bound."""
    tables = []
    by_section = defaultdict(list)
    for page in pages:
        if page["words"]:
            by_section[page["section"]].append(page)
    for section, sec_pages in by_section.items():
        state = {"speed": None, "speed_cite": None, "heading": None, "sub": None, "sub_cite": None, "prev": None}
        table = None
        for page in sec_pages:
            for col in bmw_columns(page):
                seg = None  # the table segment of this column
                for line in col:
                    texts = [b["text"] for b in line["blocks"]]
                    if table is not None:
                        consumed = bmw_table_line(table, seg, page, line)
                        if consumed == "header" and seg is None:
                            seg = new_segment(table, page, line)
                            continue
                        if consumed:
                            if seg is None and consumed != "ignore":
                                table["problems"].append(f"p.{page['number']}: rows without a header in this column: {line['text']!r}")
                            continue
                        close_table(table, tables)
                        table, seg = None, None
                    # outside a table
                    if "Tire size" in texts and any(t.startswith("Pressure specifica") for t in texts):
                        table = {"section": section, "condition": state["speed"], "speed_cite": state["speed_cite"],
                                 "heading": state["heading"], "sub": state["sub"], "sub_cite": state["sub_cite"],
                                 "segments": [], "problems": [], "page": page["number"]}
                        seg = new_segment(table, page, line)
                        continue
                    text = line["text"]
                    joined = f"{state['prev']['text']} {text}" if state["prev"] else text
                    speed = SPEED_HEAD.match(joined) or SPEED_HEAD.match(text)
                    if speed:
                        kind = "up to" if speed.group("up") else "over"
                        state.update(speed=kind, heading=None, sub=None, sub_cite=None,
                                     speed_cite={"page": page["number"], "quote": span(page, (state["prev"]["blocks"] if speed.re is SPEED_HEAD and speed.string == joined and state["prev"] else []) + line["blocks"])})
                        state["prev"] = None
                        continue
                    head = HEADING.match(text)
                    if head and state["prev"] and HEADING.match(state["prev"]["text"]) and state["prev"]["text"].endswith(","):
                        head = HEADING.match(joined)
                        blocks = state["prev"]["blocks"] + line["blocks"]
                    else:
                        blocks = line["blocks"]
                    if head and not head.group("comma"):
                        state.update(heading={"designations": DESIG_RE.findall(head.group("list")), "equipment": head.group("equipment"),
                                              "text": head.group(0), "page": page["number"], "quote": span(page, blocks)},
                                     sub=None, sub_cite=None)
                    elif SUBCONDITION.match(text):
                        state.update(sub=text.rstrip(":"), sub_cite={"page": page["number"], "quote": span(page, line["blocks"])})
                    state["prev"] = line
                if table is not None and seg is None and not table["segments"]:
                    pass
        if table is not None:
            close_table(table, tables)
    return tables


def new_segment(table, page, line) -> dict:
    blocks = line["blocks"]
    size_x = next(b["x0"] for b in blocks if b["text"] == "Tire size")
    front_x = next(b["x0"] for b in blocks if b["text"].startswith("Pressure specifica"))
    seg = {"page": page, "size_x": size_x, "front_x": front_x, "entries": [], "lines": []}
    table["segments"].append(seg)
    return seg


def bmw_table_line(table, seg, page, line) -> str | bool:
    """Feed one column line to the open table: 'header', 'row', 'ignore' or False (the table ends)."""
    texts = [b["text"] for b in line["blocks"]]
    if "Tire size" in texts and any(t.startswith("Pressure specifica") for t in texts):
        return "header"
    if seg is None:
        return False
    size_blocks = [b for b in line["blocks"] if b["x0"] < seg["front_x"] - 5]
    value_blocks = [b for b in line["blocks"] if b["x0"] >= seg["front_x"] - 5]
    if not size_blocks and not value_blocks:
        return "ignore"
    tokens = []
    for b in value_blocks:
        if PRESSURE.match(b["text"]) or b["text"] in ("-", "–"):
            tokens.append(b)
        elif not BMW_PRESSURE_TEXT.match(b["text"]):
            return False
    merged = None
    entry_text = None
    if size_blocks:
        if len(size_blocks) > 1:
            return False
        sb = size_blocks[0]
        text = sb["text"]
        if BMW_HEADER.match(text):
            if tokens:
                table["problems"].append(f"p.{page['number']}: values on a header line: {line['text']!r}")
            return "row" if not tokens else "row"
        if text.startswith("Emergency wheel: Speed up to a max. of"):
            text = "Emergency wheel:"
        tail = TAIL_PRESSURE.match(text)
        if tail and not text.startswith("T "):
            entry_text, merged = tail.group(1), tail.group(2)
        elif tail:
            entry_text, merged = tail.group(1), tail.group(2)
        else:
            entry_text = text
        position = POSITION.match(entry_text)
        current = seg["entries"][-1] if seg["entries"] else None
        starts = bool(position or SPARE_START.match(entry_text) or re.match(r"^(?:HL )?\d{3}/\d{2}", entry_text))
        label_only = current is not None and not current.has_size()
        if starts and not (label_only and not position and not SPARE_START.match(entry_text) and not current.spare) \
                and not (label_only and current.spare and re.match(r"^T ?\d{3}/\d{2}", entry_text)):
            entry = Entry(page, line["top"], (position.group(1) if position else None))
            entry.spare = bool(SPARE_START.match(entry_text))
            rest = entry_text[position.end():] if position else entry_text
            if rest:
                entry.parts.append(rest)
            entry.blocks.append(sb)
            seg["entries"].append(entry)
        elif current is not None and (FRAGMENT.match(entry_text) or entry_text in ("wheel:",) or SIZE_CORE.search(entry_text)):
            current.parts.append(entry_text)
            current.blocks.append(sb)
            if entry_text == "wheel:":
                current.spare = True
        else:
            return False
    if merged or tokens:
        front = rear = None
        merged_block = size_blocks[0] if merged else None
        for b in tokens:
            if b["x0"] - seg["front_x"] < 25:
                if front is not None or merged:
                    table["problems"].append(f"p.{page['number']}: two front values on one line: {line['text']!r}")
                    return "row"
                front = b
            else:
                if rear is not None:
                    table["problems"].append(f"p.{page['number']}: two rear values on one line: {line['text']!r}")
                    return "row"
                rear = b
        seg["lines"].append({"top": line["top"], "front": front, "rear": rear, "merged": merged, "merged_block": merged_block})
    return "row"


def close_table(table, tables):
    tables.append(table)


def value_of(item) -> str | None:
    """'2.3 / 33', '-' or None for one pressure slot of a pressure line."""
    if item is None:
        return None
    return item if isinstance(item, str) else item["text"]


def bind_pressures(table) -> tuple[list[tuple], list[tuple]]:
    """(rows, unresolved): rows are (entry, front text, rear text, blocks of the values)."""
    rows, unresolved = [], []
    for seg in table["segments"]:
        entries = seg["entries"]
        if not entries:
            continue
        lines = {id(e): [] for e in entries}
        orphan = []
        for pl in seg["lines"]:
            owner = None
            for e in entries:
                if e.top <= pl["top"] + 1.0:
                    owner = e
            if owner is None:
                orphan.append(pl)
            else:
                lines[id(owner)].append(pl)
        # a cell: an entry with pressure lines and the entries after it that have none
        groups = []
        for e in entries:
            if lines[id(e)] or not groups:
                groups.append([e])
            else:
                groups[-1].append(e)
        for group in groups:
            pls = [pl for e in group for pl in lines[id(e)]]
            if not pls:
                unresolved += [(e, "no pressure line for the cell") for e in group]
                continue
            if len(pls) == 1 and not any(e.position for e in group):
                pairs = [(e, pls[0]) for e in group]
            elif len(pls) == len(group):
                pairs = list(zip(group, pls, strict=True))
            else:
                unresolved += [(e, f"{len(group)} sizes and {len(pls)} pressure lines in one cell") for e in group]
                continue
            for e, pl in pairs:
                front = pl["merged"] if pl["merged"] else value_of(pl["front"])
                rear = value_of(pl["rear"])
                vblocks = [b for b in (pl["front"], pl["rear"], pl["merged_block"]) if b]
                rows.append((e, front, rear, vblocks))
        if orphan:
            table["problems"].append(f"p.{seg['page']['number']}: {len(orphan)} pressure line(s) above the first size of the column")
    return rows, unresolved


def bmw_facts(make: str, line_keys: list[str], pages: list[dict]) -> tuple[list[dict], list[dict]]:
    facts, skipped = [], []
    tables = bmw_tables(pages)
    for table in tables:
        rows, unresolved = bind_pressures(table)
        heading = table["heading"]
        where = f"p.{table['page']} ({table['section']})"
        for problem in table["problems"]:
            skipped.append({"where": where, "row": None, "reason": "table layout: " + problem})
        for e, reason in unresolved:
            if not e.spare:
                skipped.append({"where": f"p.{e.page['number']} ({table['section']})", "row": e.size, "reason": reason})
        # staggered pairs: a Front entry followed by a Rear entry
        ordered = [r for r in rows]
        partner = {}
        for i, (e, *_rest) in enumerate(ordered):
            if e.position in ("Front:", "F.:"):
                nxt = ordered[i + 1][0] if i + 1 < len(ordered) else None
                if nxt is not None and nxt.position in ("Rear:", "R.:"):
                    partner[id(e)] = nxt
                    partner[id(nxt)] = e
        for e, front, rear, vblocks in rows:
            page = e.page
            loc = f"p.{page['number']} ({table['section']})"
            row_text = f"{e.position + ' ' if e.position else ''}{e.size} | {front or ''} | {rear or ''}"
            if e.spare:
                skipped.append({"where": loc, "row": row_text, "reason": "emergency wheel row: no field for a spare tire (skipped)"})
                continue
            if not e.has_size():
                skipped.append({"where": loc, "row": row_text, "reason": "no complete tire size in the cell"})
                continue
            if heading is None:
                skipped.append({"where": loc, "row": row_text, "reason": "no model heading before the table"})
                continue
            if e.position and id(e) not in partner:
                skipped.append({"where": loc, "row": row_text, "reason": "front/rear size without its pair"})
                continue
            if e.position:
                other = partner[id(e)]
                fr = (e, other) if e.position in ("Front:", "F.:") else (other, e)
                tires = [f"front {fr[0].size}", f"rear {fr[1].size}"]
                tire_value = ", ".join(tires)
                size_blocks = fr[0].blocks + fr[1].blocks
            else:
                tires = [e.size]
                tire_value = e.size
                size_blocks = e.blocks
            # value checks
            want = {"front": front, "rear": rear}
            if e.position in ("Front:", "F.:"):
                ok = front and PRESSURE.match(front) and rear in ("-", "–")
                want = {"front": front}
            elif e.position in ("Rear:", "R.:"):
                ok = rear and PRESSURE.match(rear) and front in ("-", "–")
                want = {"rear": rear}
            else:
                ok = front and rear and PRESSURE.match(front) and PRESSURE.match(rear)
            pressures_ok = bool(ok)
            for slot, text in want.items():
                if text and PRESSURE.match(text):
                    bar, psi = PRESSURE.match(text).groups()
                    if abs(float(bar) * 14.5038 - int(psi)) > 1.5:
                        pressures_ok = False
            row_full = f"{heading['text'] if heading else '?'} | {row_text}"
            cites = [{"page": page["number"], "quote": span(page, size_blocks + vblocks), "role": "table row"},
                     {"page": heading["page"], "quote": heading["quote"], "role": "model heading"}]
            if table["speed_cite"]:
                cites.append({**table["speed_cite"], "role": "speed section heading"})
            if table["sub_cite"]:
                cites.append({**table["sub_cite"], "role": "table sub-heading"})
            for designation in heading["designations"]:
                for lk in line_keys:
                    other = claimed_elsewhere(designation, lk)
                    if other:
                        skipped.append({"where": loc, "row": f"{designation} | {row_text}", "line": lk,
                                        "reason": f"designation {designation} belongs to {other}, not to {lk}"})
                        continue
                    base = {"page": page["number"], "row": row_full, "engine_text": None, "variant": designation,
                            "source_layout": LAYOUT, "section_url": page["url"], "line": lk, "section": table["section"],
                            "cites": cites}
                    extra = {"equipment": heading["equipment"]} if heading["equipment"] else {}
                    facts.append({**base, "key": "tires", "value": tire_value, "unit": None, "label": "tire size",
                                  "quote": span(page, size_blocks), "original": tire_value,
                                  **({"applicability_extra": extra} if extra else {})})
                    if table["condition"] != "up to":
                        skipped.append({"where": loc, "row": f"{designation} | {row_text}", "line": lk, "kind": "pressure",
                                        "reason": "pressures of a table for speeds over 100 mph/160 km/h (size kept)"
                                        if table["condition"] == "over" else "no speed section heading before the table (size kept)"})
                        continue
                    if not pressures_ok:
                        skipped.append({"where": loc, "row": f"{designation} | {row_text}", "line": lk, "kind": "pressure",
                                        "reason": "pressure cells do not fit the row (front/rear slots or bar/PSI check)"})
                        continue
                    condition = "up to 100 mph/160 km/h" + (f"; {table['sub']}" if table["sub"] else "")
                    for slot, text in want.items():
                        bar, psi = PRESSURE.match(text).groups()
                        facts.append({**base, "key": f"tire_pressure_{slot}_kpa", "value": kpa_of_bar(bar), "unit": "kPa",
                                      "label": f"cold tire pressure, {slot}", "quote": span(page, size_blocks + vblocks),
                                      "original": f"{text} (bar / PSI)",
                                      "note": f"printed {bar} bar / {psi} psi with cold tires; kPa = 100 x bar",
                                      "applicability_extra": {"tires": tires, "condition": condition, **extra}})
    return facts, skipped


# ---- VW ----------------------------------------------------------------------------------------------
def vw_numbers(text: str) -> list[str]:
    return [t for t in re.split(r"[\s/]+", text) if re.fullmatch(r"\d+(?:[.,]\d)?", t)]


def vw_tables(pages: list[dict]) -> list[dict]:
    tables = []
    by_section = defaultdict(list)
    for page in pages:
        if page["words"]:
            by_section[page["section"]].append(page)
    for section, sec_pages in by_section.items():
        market = None
        open_table = None  # the table of the previous page still open at the page end
        for page in sec_pages:
            lines = [ln for ln in lines_of([w for w in page["words"] if w["top"] < 805])]
            i = 0
            table = None
            while i < len(lines):
                line = lines[i]
                m = MARKET.match(line["text"])
                if m:
                    market = "US" if m.group(1) == "the United States" else "CA"
                    open_table = None
                size_head = next((b for b in line["blocks"] if VW_SIZE_HEAD.match(b["text"])), None)
                if size_head is not None and table is None:
                    label_head = next((b for b in line["blocks"] if VW_LABEL_HEAD.match(b["text"])), None)
                    # the units: on this line or the next two
                    units, unit_x = [], None
                    j = i
                    for k in range(i, min(i + 3, len(lines))):
                        found = [(b["x0"], u.lower()) for b in lines[k]["blocks"] if b["x0"] > size_head["x0"] for u in VW_UNIT.findall(b["text"])]
                        if found:
                            units = [u for _, u in sorted(found, key=lambda t: t[0])]
                            unit_x = min(x for x, _ in found)
                            j = k
                            break
                    if not units:
                        i += 1
                        continue
                    table = {"section": section, "page": page, "market": market, "size_x": size_head["x0"], "unit_x": unit_x,
                             "units": units, "label_kind": label_head["text"] if label_head else None,
                             "label_x": label_head["x0"] if label_head else None, "entries": [], "values": [], "labels": [],
                             "continues": open_table if (open_table and open_table["label_kind"] == (label_head["text"] if label_head else None)) else None,
                             "header_quote": span(page, line["blocks"])}
                    tables.append(table)
                    i = j + 1
                    continue
                if table is not None:
                    if any(len(b["text"]) > 40 or VW_END.match(b["text"]) for b in line["blocks"]):
                        table = None
                        open_table = None
                        i += 1
                        continue
                    # the psi / kPa / bar cells of one row may be printed as separate blocks on the
                    # same line: they are one value line (numbers in column order)
                    value_blocks = [b for b in line["blocks"] if b["x0"] >= table["unit_x"] - 15 and vw_numbers(b["text"])]
                    if value_blocks:
                        value_blocks.sort(key=lambda b: b["x0"])
                        table["values"].append({"top": line["top"], "block": value_blocks[0], "blocks": value_blocks,
                                                "nums": [n for b in value_blocks for n in vw_numbers(b["text"])],
                                                "x": value_blocks[0]["x0"]})
                    for b in line["blocks"]:
                        if b["x0"] >= table["unit_x"] - 15:
                            continue
                        elif b["x0"] >= table["size_x"] - 15:
                            if SIZE_CORE.search(b["text"]) or re.match(r"^T\d{3}/\d{2}", b["text"]):
                                table["entries"].append({"top": line["top"], "end": line["top"], "blocks": [b], "parts": [b["text"]]})
                            elif table["entries"] and re.fullmatch(r"[A-Za-z]{1,3}", b["text"]) and line["top"] - table["entries"][-1]["end"] < 20:
                                table["entries"][-1]["parts"].append(b["text"])
                                table["entries"][-1]["blocks"].append(b)
                                table["entries"][-1]["end"] = line["top"]
                            else:
                                table["problems"] = table.get("problems", []) + [f"unread size cell {b['text']!r}"]
                        else:
                            table["labels"].append({"top": line["top"], "block": b})
                i += 1
            open_table = table  # still open at the page end: the next page may continue it
    return tables


def vw_label_units(table) -> list[dict]:
    units = []
    for item in sorted(table["labels"], key=lambda t: t["top"]):
        if units and item["top"] - units[-1]["tops"][-1] <= 16:
            units[-1]["tops"].append(item["top"])
            units[-1]["blocks"].append(item["block"])
        else:
            units.append({"tops": [item["top"]], "blocks": [item["block"]]})
    for u in units:
        u["center"] = sum(u["tops"]) / len(u["tops"])
        u["text"] = " ".join(b["text"] for b in u["blocks"])
    return units


def vw_partitions(entries, labels, carry) -> list[list[int]]:
    """Every binding of the entries to the labels (in order) where each label's rows are
    contiguous, the label lies within its rows and no label gets one tire size twice; with a
    carried label (the previous page's last label) the rows above the first label may continue it."""
    n, m = len(entries), len(labels)
    groups = ([carry] if carry else []) + labels
    out = []
    first = 0 if carry else 1
    for cuts in itertools.combinations(range(1, n), len(groups) - 1):
        bounds = [0, *cuts, n]
        ok = True
        assign = []
        for g, label in enumerate(groups):
            rows = entries[bounds[g]: bounds[g + 1]]
            if label is carry and carry:
                sizes = list(carry["sizes"]) + [r["size"] for r in rows]
            else:
                if not rows or not (rows[0]["top"] - 3 <= label["center"] <= rows[-1]["end"] + 3):
                    ok = False
                    break
                sizes = [r["size"] for r in rows]
            if len(sizes) != len(set(sizes)):
                ok = False
                break
            assign += [g] * len(rows)
        if ok:
            out.append(assign)
    if carry and n:  # the carried label may also have no rows on this page
        for cuts in itertools.combinations(range(1, n), len(labels) - 1) if labels else [()]:
            pass
    del first, m
    return out


def vw_drive(text: str) -> str | None:
    if re.search(r"all-wheel|4MOTION|four-wheel", text, re.I):
        return "AWD"
    if re.search(r"front[- ]wheel drive|\bFWD\b", text, re.I):
        return "FWD"
    return None


def vw_engine(text: str) -> str | None:
    disp = re.search(r"(\d\.\d)\s?[lL]\b", text)
    if not disp:
        return None
    return f"{disp.group(1)}L" + (" TDI" if re.search(r"\bTDI\b", text) else "")


def vw_facts(make: str, line_keys: list[str], pages: list[dict]) -> tuple[list[dict], list[dict]]:
    facts, skipped = [], []
    tables = vw_tables(pages)
    for table in tables:
        page = table["page"]
        loc = f"p.{page['number']} ({table['section']})"
        for problem in table.get("problems", []):
            skipped.append({"where": loc, "row": None, "reason": "table layout: " + problem})
        entries = table["entries"]
        for e in entries:
            e["size"] = clean_size(" ".join(e["parts"]))
        # values: the value line within the size cell's lines
        for e in entries:
            e["value"] = None
            hits = [v for v in table["values"] if e["top"] - 2 <= v["top"] <= e["end"] + 2]
            if len(hits) == 1:
                e["value"] = hits[0]
            else:
                e["value_problem"] = f"{len(hits)} value lines for the row"
        labels = vw_label_units(table) if table["label_kind"] else []
        carry = None
        prev = table["continues"]
        if prev is not None and prev.get("last_label") is not None and entries and (not labels or entries[0]["top"] < labels[0]["center"] - 3):
            carry = prev["last_label"]
        if table["label_kind"]:
            parts = vw_partitions(entries, labels, carry)
            groups = ([carry] if carry else []) + labels
            for idx, e in enumerate(entries):
                choices = {p[idx] for p in parts}
                e["label"] = groups[choices.pop()] if len(choices) == 1 else None
                e["label_problem"] = None if e["label"] else (f"{len(choices)} possible model/engine cells" if choices else "no consistent reading of the model/engine column")
            table["last_label"] = entries[-1]["label"] if entries and entries[-1]["label"] else (labels[-1] if labels else carry)
            if table["last_label"] is not None:
                last = table["last_label"]
                # a label carried to the next page keeps the page and the words it was printed with
                where = {} if last is carry else {"page": page["number"], "quote": span(page, last["blocks"])}
                table["last_label"] = {**last, **where, "sizes": [e["size"] for e in entries if e.get("label") is last]
                                       + (list(last.get("sizes", [])) if last is carry else [])}
        else:
            for e in entries:
                e["label"], e["label_problem"] = None, None
        for e in entries:
            label = e["label"]
            label_text = label["text"] if label else None
            row_text = f"{label_text or '(no model column)'} | {e['size']} | " + (" ".join(e["value"]["nums"]) if e["value"] else "?")
            if table["market"] == "CA":
                skipped.append({"where": loc, "row": row_text, "reason": "table marked 'Applicable only in Canada'"})
                continue
            if e["size"].startswith("T") or (label_text and VW_SPARE_LABEL.search(label_text)) or "spare" in e["size"]:
                skipped.append({"where": loc, "row": row_text, "reason": "compact/temporary spare wheel row: no field for a spare tire (skipped)"})
                continue
            if table["label_kind"] and label is None:
                skipped.append({"where": loc, "row": row_text, "reason": e["label_problem"]})
                continue
            if e["value"] is None:
                skipped.append({"where": loc, "row": row_text, "reason": e.get("value_problem", "no values")})
                continue
            nums = e["value"]["nums"]
            if len(nums) != len(table["units"]):
                skipped.append({"where": loc, "row": row_text, "reason": f"{len(nums)} values for the units {table['units']}"})
                continue
            vals = dict(zip(table["units"], nums, strict=True))
            kpa = int(vals["kpa"]) if "kpa" in vals else (kpa_of_bar(vals["bar"]) if "bar" in vals else None)
            problems = []
            if kpa is None:
                problems.append("no kPa or bar value")
            if "bar" in vals and kpa is not None and kpa_of_bar(vals["bar"].replace(",", ".")) != kpa:
                problems.append(f"bar {vals['bar']} x 100 != {kpa} kPa")
            if "psi" in vals and kpa is not None and abs(int(vals["psi"]) * 6.89476 - kpa) > 10:
                problems.append(f"psi {vals['psi']} does not fit {kpa} kPa")
            if problems:
                skipped.append({"where": loc, "row": row_text, "reason": "; ".join(problems)})
                continue
            printed = " / ".join(f"{vals[u]} {u if u != 'kpa' else 'kPa'}" for u in table["units"])
            row_blocks = e["blocks"] + e["value"].get("blocks", [e["value"]["block"]]) + (label["blocks"] if label else [])
            label_pages_ok = label is None or label is not carry
            quote_blocks = row_blocks if label_pages_ok else e["blocks"] + e["value"].get("blocks", [e["value"]["block"]])
            cites = [{"page": page["number"], "quote": span(page, quote_blocks), "role": "table row"}]
            if label is not None and label is carry:
                cites.append({"page": carry["page"], "quote": carry["quote"], "role": "model/engine cell (previous page)"})
            applicability = {}
            fact_variant, fact_drive = None, None
            if label is not None:
                kind = table["label_kind"]
                if kind == "Engine":
                    engine = vw_engine(label_text)
                    if engine is None:
                        skipped.append({"where": loc, "row": row_text, "reason": "engine cell without a displacement"})
                        continue
                    applicability["engine"] = engine
                    # a gas engine of the same displacement as a TDI of this table: not the TDI
                    siblings = {vw_engine(g["text"]) for g in labels + ([carry] if carry else [])} | set(table.get("engines_before", []))
                    if " TDI" not in engine and f"{engine} TDI" in siblings:
                        applicability["engine_except"] = f"{engine} TDI"
                    fact_drive = vw_drive(label_text)
                    sibling_texts = [g["text"] for g in labels + ([carry] if carry else [])]
                    if fact_drive is None and any(t != label_text and t.startswith(label_text) and vw_drive(t) == "AWD" for t in sibling_texts):
                        fact_drive = "FWD"  # the table lists the same engine with 4MOTION separately
                    applicability["engine_label"] = label_text
                else:
                    fact_variant = label_text
                    fact_drive = vw_drive(label_text)
            for lk in line_keys:
                base = {"page": page["number"], "row": row_text, "engine_text": None, "source_layout": LAYOUT,
                        "section_url": page["url"], "line": lk, "section": table["section"], "cites": cites,
                        **({"variant": fact_variant} if fact_variant else {}), **({"drive": fact_drive} if fact_drive else {})}
                facts.append({**base, "key": "tires", "value": e["size"], "unit": None, "label": "tire size",
                              "quote": span(page, e["blocks"]), "original": e["size"],
                              **({"applicability_extra": dict(applicability)} if applicability else {})})
                for slot in ("front", "rear"):
                    facts.append({**base, "key": f"tire_pressure_{slot}_kpa", "value": kpa, "unit": "kPa",
                                  "label": f"cold tire pressure, {slot}", "quote": cites[0]["quote"], "original": printed,
                                  "note": f"printed {printed} for cold tires; the table gives one pressure per tire size "
                                          f"(no front/rear split), written for the front and the rear axle",
                                  "applicability_extra": {**applicability, "tires": [e["size"]]}})
        if table["label_kind"] == "Engine":
            nxt = [t for t in tables if t.get("continues") is table]
            for t in nxt:
                t["engines_before"] = [vw_engine(g["text"]) for g in labels]
    return facts, skipped


# ---- the pass ------------------------------------------------------------------------------------
def scope_key(f: dict) -> str:
    return json.dumps([f["line"], f["key"], f.get("variant"), f.get("drive"), f.get("applicability_extra", {})], sort_keys=True)


def tire_facts(make: str, line_keys: list[str], pages: list[dict]) -> tuple[list[dict], list[dict]]:
    """Facts and skipped rows of one edition (pages as edition_pages() returns them)."""
    facts, skipped = (bmw_facts if make == "bmw" else vw_facts)(make, line_keys, pages)
    # one table printed in two sections ("mobility" and "mobility--wheels-and-tires"): the copy in
    # the more specific section is kept
    best = {}
    for f in facts:
        k = scope_key(f) + json.dumps(f["value"])
        rank = (-f["section"].count("--"), -len(f["section"]), f["page"])
        if k not in best or rank < best[k][0]:
            best[k] = (rank, f)
    facts = [f for _, f in best.values()]
    # one scope with two different pressures in this edition: not written
    values = defaultdict(set)
    for f in facts:
        if f["key"] != "tires":
            values[scope_key(f)].add(f["value"])
    conflicted = {k for k, v in values.items() if len(v) > 1}
    for f in facts:
        if f["key"] != "tires" and scope_key(f) in conflicted:
            skipped.append({"where": f"p.{f['page']} ({f['section']})", "row": f["row"], "line": f["line"], "kind": "pressure",
                            "reason": f"{f['key']} {f['value']}: the edition gives this scope {sorted(values[scope_key(f)])}"})
    facts = [f for f in facts if f["key"] == "tires" or scope_key(f) not in conflicted]
    facts.sort(key=lambda f: (f["page"], f["key"], str(f.get("variant")), json.dumps(f.get("applicability_extra", {}), sort_keys=True)))
    # skipped rows that are only the second printed copy of a written row
    written_rows = {(f["row"].split(" | ", 1)[-1]) for f in facts}
    for s in skipped:
        if s.get("row") and s["row"].split(" | ", 1)[-1] in written_rows and "copy" not in s["reason"]:
            s["duplicate_of_written_row"] = True
    for f in facts:
        f.pop("section", None)
    return facts, skipped


def check_quotes(facts: list[dict], pages: list[dict]) -> list[str]:
    problems = []
    for f in facts:
        for cite in [{"page": f["page"], "quote": f["quote"]}] + f.get("cites", []):
            if cite["quote"] not in pages[cite["page"] - 1]["text"]:
                problems.append(f"{f['key']} {f['value']}: quote not on p.{cite['page']}: {cite['quote'][:80]!r}")
    return problems


def tire_pass(make: str, line_keys: list[str], site_make: str, model: str, body: str, years: str,
              page_texts: list[str] | None = None) -> tuple[list[dict], list[dict]]:
    """Called by extract_mcum_facts.main(): the edition's tire facts, after checking that the
    pages are numbered as extract_mcum_facts numbered them."""
    pages, _sha = edition_pages(site_make, model, body, years)
    if page_texts is not None and [p["text"] for p in pages] != list(page_texts):
        raise RuntimeError(f"{site_make}/{model}/{body}/{years}: page numbering differs from extract_mcum_facts")
    facts, skipped = tire_facts(make, line_keys, pages)
    bad = check_quotes(facts, pages)
    if bad:
        raise RuntimeError("tire quotes not found on their pages: " + "; ".join(bad[:5]))
    for f in facts:
        f.pop("line", None) if len(line_keys) == 1 else None
    return facts, skipped


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    only = {a for a in argv if not a.startswith("--")} or TIRE_MAKES
    markets = json.loads((WORK / "_mcum" / "edition_markets.json").read_text(encoding="utf-8"))
    slug_to_make = {v["mcum"]: k for k, v in MAKES.items() if v.get("mcum")}
    for key, info in sorted(markets.items()):
        site_make, model, body, years = key.split("/")
        make = slug_to_make.get(site_make)
        if make not in only or make not in TIRE_MAKES or info.get("market") != "US":
            continue
        target = WORK / make / "extracted" / f"mcum-{model}-{body}-{years}.json"
        if not target.exists():
            continue
        doc = json.loads(target.read_text(encoding="utf-8"))
        pages, sha = edition_pages(site_make, model, body, years)
        if sha != doc["doc"]["sha256"] or len(pages) != doc["pages"]:
            print(f"{target.name}: raw pages differ from the document (sha/page count); re-run extract_mcum_facts.py", flush=True)
            return 1
        with gzip.open(RAW_ROOT / "pagetext" / f"{sha}.json.gz", "rt", encoding="utf-8") as handle:
            stored = json.load(handle)["pages"]
        if stored != [p["text"] for p in pages]:
            print(f"{target.name}: page texts differ from the page text store", flush=True)
            return 1
        line_keys = doc["doc"]["lines"]
        facts, skipped = tire_facts(make, line_keys, pages)
        bad = check_quotes(facts, pages)
        if bad:
            print(target.name, "QUOTE PROBLEMS:", bad[:10], flush=True)
            return 1
        if len(line_keys) == 1:
            for f in facts:
                f.pop("line", None)
        counts = defaultdict(int)
        for f in facts:
            counts[f["key"]] += 1
        print(f"{target.name}: {dict(counts)} skipped {len(skipped)} "
              f"(of which second copies of written rows {sum(1 for s in skipped if s.get('duplicate_of_written_row'))})", flush=True)
        if dry:
            continue
        doc["facts"] = [f for f in doc["facts"] if f.get("source_layout") != LAYOUT] + facts
        doc["tire_skipped"] = skipped
        if f"+{TIRE_PASS}" not in doc["extractor"]:
            doc["extractor"] += f"+{TIRE_PASS}"
        target.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

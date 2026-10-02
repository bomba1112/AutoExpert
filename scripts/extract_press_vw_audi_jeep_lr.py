"""Parse the stored US press spec documents of media.vw.com, media.audiusa.com, media.jlr.com
(and media.stellantisnorthamerica.com, if it ever has stored documents) into the per-document
JSON files of data_work/_shared/press/FORMAT.md.

Input: the manifests data_work/_shared/manifest_press/<host>.csv written by
scripts/collect_press_vw_audi_jeep_lr.py (rows doc_type=press_specifications, status=ok), the raw
documents under RAW_ROOT and their page text RAW_ROOT/pagetext/<sha256>.json.gz.

How tables are read (no values are typed by hand; everything comes from the stored documents):
  PDF   pdfplumber text lines (the same lines as the stored page text) with character positions.
        Per page: the left margin (label column) is the most common x of line starts; the value
        columns come from the column-heading line(s) above the first section heading (VW/Audi:
        "Jetta 2.0L | Jetta 1.8T | ..." or "2.0T FWD | ..."; JLR: "2020 RANGE ROVER (DIESEL) 3.0L
        TC V6 254HP | ..."). Columns are left-aligned (VW/Audi: column starts) or centred (JLR:
        midpoints between column centres). Every character right of the label column is put into
        the column it lies in, so each value is paired with its column heading (engine_text).
        A line starting at the left margin opens a row (label); following lines without a label
        continue the row (wrapped values); upper-case label-only lines are section headings;
        short value-only lines such as "Automatic (8-Speed)" / "Manual Automatic" right above a
        row are sub-headings. A phrase running across column borders is a merged cell: across all
        columns -> one value for all columns (engine_text null), across some -> review.
  Word  (JLR 2015 .doc/.docx) table rows as stored by the collector (pagetext "rows"): a row
        [label, v1, v2, ...] under a heading row ["", col1, col2, ...]; a row with one value under
        several column headings is a merged cell for all columns.
Each fact carries the verbatim quote (the text line(s) of its row in the stored page text), the
row label, the column heading (engine_text) and the published cell (original). Numbers are parsed
only; units are taken from the label or the value and never converted (a value whose unit cannot be
seen goes to review). Rows that cannot be read unambiguously go to "review".

Run:
  uv run --no-project --with pdfplumber --with pypdfium2 python scripts/extract_press_vw_audi_jeep_lr.py
  options: --host <host> (repeatable), --verify (only check quotes of the written files)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

EXTRACTOR = "press-vw-audi-jeep-lr-1"
MANIFEST_DIR = WORK / "_shared" / "manifest_press"
HOSTS = {
    "media.vw.com": ("vw", "Volkswagen of America Media Site (media.vw.com)"),
    "media.audiusa.com": ("audiusa", "Audi of America Media Site (media.audiusa.com)"),
    "media.stellantisnorthamerica.com": ("stellantis", "Stellantis North America Media (media.stellantisnorthamerica.com)"),
    "media.jlr.com": ("jlr", "JLR Media, North America edition (media.jlr.com)"),
}


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


# =============================================================================================
# table rows
# =============================================================================================
@dataclass
class TRow:
    page: int
    section: str
    label: str
    cells: list[str]            # one per column; one cell when the table has a single column
    columns: list[str]          # column headings ([] = one unnamed column)
    quote: str                  # verbatim text line(s) of the row
    spanning: bool = False      # one value for all columns
    partial: bool = False       # merged across some columns only
    sub: str = ""               # sub-heading above the row (e.g. "Automatic (8-Speed)")
    sub_cells: list[str] = field(default_factory=list)
    nested: bool = False        # sub-heading splits the columns further (values not per column)
    sub_quote: str = ""         # text line of the sub-heading
    word: bool = False          # row of a Word table (cell paragraphs are separate items)


SECTION_RE = re.compile(r"^[^a-z]*[A-Z]{3,}[^a-z]*$")
TITLE_RE = re.compile(r"(?i)^(technical spec(ification)?s?|tech specs?|specifications|spec sheet\d*|(19|20)\d\d\b.*)$")
# headings of the spec tables in Audi press kits ("Engineering/Performance", "Exterior Measurements")
SECTION_TITLE_RE = re.compile(
    r"(?i)^(engineering\s*/\s*performance|engine\s+design|transmission\s*/\s*drivetrain|"
    r"body\s*/\s*suspension(\s*/\s*chassis)?|exterior\s+measurements|interior\s+measurements|"
    r"wheels\s+(and|&)\s+tires|technical\s+specifications)$")
SUBHEAD_CELL_RE = re.compile(
    r"(?i)^((\d{1,2}-speed\s+)?(manual|automatic|dsg|s tronic|tiptronic)(\s*\(\d{1,2}-speed\))?|"
    r"(1st|2nd|3rd|front|rear) row|front|rear|fwd|awd|4motion|quattro|"
    r"front-wheel drive|all-wheel drive)$")


@dataclass
class PLine:
    text: str
    top: float
    bottom: float
    chars: list[dict]


def _words(chars: list[dict], text: str | None = None) -> list[tuple[float, float, str, list[dict]]]:
    """Words of a line. With the line text (pdfplumber's, = the stored page text) the characters
    are walked along the text, so the words are exactly those of the page text; otherwise runs of
    non-blank characters with gaps of at most 3 pt."""
    if text is not None:
        seq = [c for c in chars if c["text"].strip()]
        groups: list[list[dict]] = []
        cur_w: list[dict] = []
        i = j = 0
        ok = True
        while i < len(text):
            if text[i].isspace():
                if cur_w:
                    groups.append(cur_w)
                    cur_w = []
                i += 1
                continue
            if j < len(seq) and seq[j]["text"] and text.startswith(seq[j]["text"], i):
                cur_w.append(seq[j])
                i += len(seq[j]["text"])
                j += 1
            else:
                ok = False
                break
        if cur_w:
            groups.append(cur_w)
        if ok and j == len(seq):
            return [(g[0]["x0"], g[-1]["x1"], "".join(c["text"] for c in g), g) for g in groups]
    out: list[tuple[float, float, str, list[dict]]] = []
    cur: list[dict] = []
    for ch in chars:
        if not ch["text"].strip():
            if cur:
                out.append((cur[0]["x0"], cur[-1]["x1"], "".join(c["text"] for c in cur), cur))
                cur = []
            continue
        if cur and ch["x0"] - cur[-1]["x1"] > 3:
            out.append((cur[0]["x0"], cur[-1]["x1"], "".join(c["text"] for c in cur), cur))
            cur = []
        cur.append(ch)
    if cur:
        out.append((cur[0]["x0"], cur[-1]["x1"], "".join(c["text"] for c in cur), cur))
    return out


def _cells(words, gap: float) -> list[tuple[float, float, str]]:
    """Words joined into cells; a gap wider than `gap` separates cells."""
    cells: list[list] = []
    for x0, x1, text, _ in words:
        if cells and x0 - cells[-1][1] <= gap:
            cells[-1][1] = x1
            cells[-1][2] += " " + text
        else:
            cells.append([x0, x1, text])
    return [tuple(c) for c in cells]


def _join(parts: list[tuple[float, float, str, bool]]) -> str:
    """Column text from word parts; a part that starts a word is preceded by a space."""
    out = ""
    for _, _, text, starts_word in parts:
        if out and starts_word:
            out += " "
        out += text
    return out.strip()


class PageTable:
    """Rows of one PDF page."""

    def __init__(self, page_no: int, lines: list[PLine]):
        self.page_no = page_no
        self.lines = [ln for ln in lines if ln.chars and ln.text.strip()]
        self.words = [_words(ln.chars, ln.text) for ln in self.lines]
        sizes = [c.get("size", 9) for ln in self.lines for c in ln.chars if c["text"].strip()]
        self.font = Counter(round(s) for s in sizes).most_common(1)[0][0] if sizes else 9
        self.gap = max(6.0, 0.9 * self.font)  # cell gap
        self.x_left = self._left_margin()
        self.columns: list[str] = []
        self.zones: list[tuple[float, float]] = []
        self.centers: list[float] = []
        self.aligned = "left"
        self.header_end = 0
        self._columns()

    def _left_margin(self) -> float | None:
        """x of the label column: the most common start of lines that hold a label and a value
        (a wide gap after the first cell); else the smallest frequent line start."""
        labelled = Counter()
        for words in self.words:
            cells = _cells(words, self.gap)
            if len(cells) >= 2:
                labelled[round(cells[0][0])] += 1
        if labelled and labelled.most_common(1)[0][1] >= 3:
            top = labelled.most_common(1)[0][0]
            return min(x for x in labelled if abs(x - top) <= 3)
        starts = Counter(round(w[0][0]) for w in self.words if w)
        if not starts:
            return None
        best = starts.most_common(1)[0][1]
        cands = [x for x, n in starts.items() if n >= max(3, best * 0.3)] or [starts.most_common(1)[0][0]]
        return min(cands)

    def at_left(self, x: float) -> bool:
        return self.x_left is not None and abs(x - self.x_left) <= 4

    def outdented(self, x: float) -> bool:
        return self.x_left is not None and x < self.x_left - 4

    def _columns(self) -> None:
        heads: list[list] = []  # per heading line: the words right of the label column
        end = len(self.words)
        for i, words in enumerate(self.words):
            cells = _cells(words, self.gap)
            if not cells:
                continue
            first = cells[0]
            if self.at_left(first[0]) or self.outdented(first[0]):
                if SECTION_RE.match(first[2]) and not TITLE_RE.match(first[2]):
                    end = i
                    break
                if TITLE_RE.match(first[2]) or (i <= 2 and len(cells) == 1) or (
                        self.outdented(first[0]) and len(cells) >= 2
                        and not any(re.search(r"\d\s*(in|mm|lbs?|kg|cu|hp|rpm|@)|^[\s\d.,/:$x-]+$", c[2]) for c in cells[1:])):
                    heads.append([w for w in words if w[0] > first[1] + self.gap])
                    continue
                end = i
                break
            heads.append(list(words))
        self.header_end = end
        heads = [h for h in heads if h]
        if heads:
            self.set_columns(heads, end)
        else:
            start = self.single_value_start(self.words[end:])
            if start is not None:
                self.zones = [(start - 0.8, 1e9)]

    def single_value_start(self, data: list) -> float | None:
        """Start x of a single left-aligned value column: where the values of the labelled lines
        start (first word after the wide gap behind the label). Centred values (Audi press kits)
        have no common start: None (then the first cell of a line at the left margin is the label
        and the rest of the line is the value)."""
        starts = []
        for words in data:
            if not words or not self.at_left(words[0][0]):
                continue
            for a, b in zip(words, words[1:]):
                if b[0] - a[1] > self.gap:
                    starts.append(b[0])
                    break
        if len(starts) < 3:
            return None
        counts = Counter(round(x) for x in starts)
        top = counts.most_common(1)[0][0]
        near_top = [x for x in starts if abs(round(x) - top) <= 2]
        if len(near_top) >= 0.6 * len(starts):
            return min(near_top)
        return None  # centred values: label = first cell of a line at the left margin, rest = value

    def set_columns(self, heads: list[list], data_from: int) -> None:
        """Columns from heading lines (lists of words right of the label column): the heading line
        split into the most cells fixes the columns; words of other heading lines go to the
        column whose centre is nearest. Zones: left-aligned columns (values start at the column
        start) or centred columns (midpoints between the centres)."""
        anchor = max((_cells(h, self.gap) for h in heads), key=len)
        centers = [(a + b) / 2 for a, b, _ in anchor]
        cols = [[a, b, []] for a, b, _ in anchor]
        for line_words in heads:
            parts: dict[int, list[str]] = {}
            for w in line_words:
                k = min(range(len(centers)), key=lambda j: abs((w[0] + w[1]) / 2 - centers[j]))
                parts.setdefault(k, []).append(w[2])
            for k, texts in parts.items():
                cols[k][2].append(" ".join(texts))
        self.columns = [norm(" ".join(c[2])) for c in cols]
        data = self.words[data_from:]
        if len(cols) == 1:
            # one heading (e.g. "Jetta GLI"): the value column is found from the data lines
            start = self.single_value_start(data)
            self.aligned = "left"
            self.zones = [(start - 0.8, 1e9)] if start is not None else []
            return
        # left-aligned columns: most value cells of a column start exactly at the heading's x
        starts = [c[0] for c in cols]
        left_ok = True
        for k, x in enumerate(starts):
            hi = starts[k + 1] - 5 if k + 1 < len(starts) else 1e9
            lo = x - (starts[k] - starts[k - 1]) / 2 if k else x - 40
            cells = [c for words in data[:40] for c in _cells(words, self.gap) if lo <= c[0] < hi]
            at_start = sum(1 for c in cells if abs(c[0] - x) <= 1.5)
            if len(cells) < 3 or at_start < 0.5 * len(cells):
                left_ok = False
                break
        self.aligned = "left" if left_ok else "center"
        if self.aligned == "left":
            starts = [c[0] for c in cols]
            self.zones = [(starts[k] - 0.8, (starts[k + 1] - 0.8) if k + 1 < len(starts) else 1e9)
                          for k in range(len(starts))]
        else:
            centers = [(c[0] + c[1]) / 2 for c in cols]
            self.centers = centers
            width = (centers[1] - centers[0]) if len(centers) > 1 else (cols[0][1] - cols[0][0]) * 2
            bounds = [centers[0] - width / 2] + [(centers[k] + centers[k + 1]) / 2 for k in range(len(centers) - 1)]
            self.zones = [(bounds[k], bounds[k + 1] if k + 1 < len(bounds) else 1e9) for k in range(len(bounds))]

    def zone_of(self, x: float) -> int:
        if not self.zones or x < self.zones[0][0]:
            return -1
        for k, (a, b) in enumerate(self.zones):
            if a <= x < b:
                return k
        return len(self.zones) - 1

    def split(self, line_words):
        """-> label cells, text per value column, all value text of the line, merged-all, merged-partial."""
        n = max(1, len(self.zones))
        if not self.zones:
            cells = _cells(line_words, self.gap)
            if cells and self.at_left(cells[0][0]):
                value = norm(" ".join(c[2] for c in cells[1:]))
                return [cells[0]], [value], value, False, False
            value = norm(" ".join(c[2] for c in cells))
            return [], [value], value, False, False
        zone0 = self.zones[0][0]
        label_limit = zone0 if self.aligned == "left" else (self.zones[0][0] + min(self.zones[0][1], 1e5)) / 2
        label_words, value_words = [], []
        for word in line_words:
            center = (word[0] + word[1]) / 2
            if not value_words and (center < zone0 or (
                    label_words and center < label_limit and word[0] - label_words[-1][1] <= self.gap)):
                label_words.append(word)
            else:
                value_words.append(word)
        if self.aligned == "center" and len(self.centers) == n:
            return self._split_centered(label_words, value_words, n)
        col_parts: list[list[tuple[float, float, str, bool]]] = [[] for _ in range(n)]
        merged_runs: list[set[int]] = []
        run: set[int] = set()
        prev = None  # (zone, x1)
        for x0, x1, text, chars in value_words:
            groups: list[tuple[int, list[dict]]] = []
            for c in chars:
                z = max(self.zone_of((c["x0"] + c["x1"]) / 2), 0)
                if groups and groups[-1][0] == z:
                    groups[-1][1].append(c)
                else:
                    groups.append((z, [c]))
            for gi, (z, cs) in enumerate(groups):
                gx0 = cs[0]["x0"]
                if prev is not None and prev[0] != z:
                    gap = gx0 - prev[1]
                    starts_col = self.aligned == "left" and abs(gx0 - (self.zones[z][0] + 0.8)) <= 1.6
                    if self.aligned == "center":
                        flowing = gi > 0 or gap <= self.gap * 0.75
                    else:
                        flowing = not starts_col and (gi > 0 or gap <= 3.5)
                    if flowing:
                        run |= {prev[0], z}
                    elif run:
                        merged_runs.append(run)
                        run = set()
                col_parts[z].append((gx0, cs[-1]["x1"], "".join(c["text"] for c in cs), gi == 0))
                prev = (z, cs[-1]["x1"])
        if run:
            merged_runs.append(run)
        texts = [_join(parts) for parts in col_parts]
        line_value = norm(" ".join(w[2] for w in value_words))
        label_cells = _cells(label_words, self.gap)
        merged_all = any(len(r) == n and n > 1 for r in merged_runs)
        merged_part = any(1 < len(r) < n for r in merged_runs)
        if self.aligned == "center" and n > 2 and value_words:
            used = [k for k, parts in enumerate(col_parts) if parts]
            single_phrase = (len(merged_runs) == 1 and set(used) <= merged_runs[0]) or len(used) == 1
            if single_phrase:
                left = self.zones[0][0]
                right = self.zones[-1][0] + (self.zones[-1][0] - self.zones[-2][0])
                mid = (value_words[0][0] + value_words[-1][1]) / 2
                if abs(mid - (left + right) / 2) <= (right - left) * 0.2:
                    merged_all, merged_part = True, False
        return label_cells, texts, line_value, merged_all, merged_part

    def _split_centered(self, label_words, value_words, n):
        """Centred columns: the value words form cells (separated by wide gaps); each cell goes to
        the column whose centre is nearest. One cell in the middle of a table of 3+ columns is
        one value for all columns; two cells in one column, or a cell wider than a column, is an
        unclear row (merged)."""
        label_cells = _cells(label_words, self.gap)
        line_value = norm(" ".join(w[2] for w in value_words))
        texts = [""] * n
        if not value_words:
            return label_cells, texts, line_value, False, False
        centers = self.centers
        step = (centers[1] - centers[0]) if n > 1 else 1e9
        left, right = centers[0] - step / 2, centers[-1] + step / 2
        cells = _cells(value_words, self.gap)
        if n > 2 and len(cells) == 1:
            a, b, text = cells[0]
            if abs((a + b) / 2 - (left + right) / 2) <= (right - left) * 0.2:
                return label_cells, [text] + [""] * (n - 1), line_value, True, False
        merged_part = False
        for a, b, text in cells:
            k = min(range(n), key=lambda j: abs((a + b) / 2 - centers[j]))
            if texts[k] or b - a > step * 1.15:
                merged_part = True
            texts[k] = (texts[k] + " " + text).strip()
        return label_cells, texts, line_value, False, merged_part

    def _cell_texts(self, i: int, values_only: bool = False) -> list[str]:
        """Cells of line i per column (words of the stored text; cells split at wide gaps)."""
        out = []
        words = self.words[i]
        for k in range(max(1, len(self.zones))):
            in_zone = [w for w in words if (not self.zones or self.zone_of((w[0] + w[1]) / 2) == k)]
            out += [c[2] for c in _cells(in_zone, self.gap)]
        if not self.zones and not values_only:
            out = [c[2] for c in _cells(words, self.gap)]
        return out

    def _is_subhead(self, i: int, values_only: bool = False) -> bool:
        cells = self._cell_texts(i, values_only)
        return bool(cells) and all(SUBHEAD_CELL_RE.match(norm(c)) for c in cells)

    def _nested(self, i: int) -> bool:
        return len(self._cell_texts(i, True)) > max(1, len(self.zones))

    def _heading_line(self, i: int):
        """In-table heading such as "Engineering/Performance  A4 40 TFSI  A4 45TFSI ..." or an
        upper-case section heading: -> (title, heading words right of the title) or None."""
        cells = _cells(self.words[i], self.gap)
        if not cells:
            return None
        first = cells[0]
        if not (self.at_left(first[0]) or self.outdented(first[0])):
            return None
        title = first[2]
        rest = [w for w in self.words[i] if w[0] > first[1] + 0.1]
        if SECTION_RE.match(title) and len(title) >= 3:
            return title, rest
        if (SECTION_TITLE_RE.match(title) or self.outdented(first[0])) and len(cells) >= 2 \
                and not any(re.search(r"\d\s*(in|mm|lbs?|kg|cu|hp|rpm|@)", c[2]) for c in cells[1:]) \
                and not any(re.match(r"^[\s\d.,/:x-]+$", c[2]) for c in cells[1:]):
            return title, rest
        if self.outdented(first[0]) and len(cells) == 1:
            return title, []
        return None

    def rows(self) -> list[TRow]:
        out: list[TRow] = []
        section = ""
        sub, sub_cells, nested, sub_quote = "", [], False, ""
        cur: dict | None = None
        pending: list[tuple] = []  # value lines that belong to the label line below them
        last_bottom = None

        def close():
            nonlocal cur
            if cur is not None:
                cells = ["\n".join(norm(x) for x in c.split("\n") if norm(x)) for c in cur["cells"]]
                if cur["spanning"]:
                    cells = ["\n".join(x for x in cur["full"] if x)]
                out.append(TRow(self.page_no, section, norm(cur["label"]), cells, list(cur["columns"]),
                                norm(" ".join(cur["quote"])), cur["spanning"], cur["partial"] and not cur["spanning"],
                                cur["sub"], cur["sub_cells"], cur["nested"], cur["sub_quote"]))
            cur = None

        def new_row(label, texts, value, m_all, m_part, line, main_label):
            return {"label": label, "cells": list(texts), "full": [value], "quote": [line.text],
                    "spanning": m_all, "partial": m_part, "sub": sub, "sub_cells": list(sub_cells),
                    "nested": nested, "sub_quote": sub_quote, "main": main_label, "columns": list(self.columns)}

        def add_values(row, texts, value, m_all, m_part, line, front=False):
            for k, t in enumerate(texts):
                if t and k < len(row["cells"]):
                    if front:
                        row["cells"][k] = (t + "\n" + row["cells"][k]) if row["cells"][k] else t
                    else:
                        row["cells"][k] = (row["cells"][k] + "\n" + t) if row["cells"][k] else t
            if front:
                row["full"].insert(0, value)
                row["quote"].insert(0, line.text)
            else:
                row["full"].append(value)
                row["quote"].append(line.text)
            row["spanning"] = row["spanning"] or m_all
            row["partial"] = row["partial"] or m_part

        def gap(a: PLine, b: PLine) -> float:
            return b.top - a.bottom

        def owns_next_label(i: int) -> bool:
            """Value line i (and value lines right below it) sit closer to the label line that
            follows than to the line above: a vertically centred label (Audi press kits)."""
            if i == 0:
                return False
            above = gap(self.lines[i - 1], self.lines[i])
            j = i
            while j + 1 < len(self.lines):
                label_cells = self.split(self.words[j + 1])[0]
                inner = gap(self.lines[j], self.lines[j + 1])
                if inner > above - 1.5:
                    return False
                if label_cells and self.at_left(label_cells[0][0]):
                    return not SECTION_RE.match(label_cells[0][2])
                if label_cells:
                    return False
                j += 1
            return False

        for i in range(self.header_end, len(self.lines)):
            line, words = self.lines[i], self.words[i]
            heading = self._heading_line(i)
            if heading is not None:
                close()
                pending = []
                section = heading[0]
                sub, sub_cells, nested, sub_quote = "", [], False, ""
                if heading[1]:
                    if self.zones and all(SUBHEAD_CELL_RE.match(norm(c[2])) for c in _cells(heading[1], self.gap)):
                        texts = self.split(words)[1]
                        sub, sub_cells, sub_quote = norm(" | ".join(t for t in texts if t)), texts, line.text
                        nested = self._nested(i)
                    else:
                        self.set_columns([heading[1]], i + 1)
                last_bottom = line.bottom
                continue
            label_cells, texts, value, m_all, m_part = self.split(words)
            has_values = any(texts)
            main = label_cells[0] if label_cells and self.at_left(label_cells[0][0]) else None
            subs = label_cells[1:] if main else label_cells
            line_h = max(1.0, line.bottom - line.top)
            near = last_bottom is not None and (line.top - last_bottom) <= 1.3 * line_h
            next_is_label = False
            if i + 1 < len(self.lines):
                next_is_label = bool(self.split(self.words[i + 1])[0])
            if not label_cells and has_values and next_is_label and self._is_subhead(i):
                close()
                pending = []
                sub, sub_cells, sub_quote = norm(" | ".join(t for t in texts if t)), texts, line.text
                nested = self._nested(i)
                last_bottom = line.bottom
                continue
            if main and cur is not None and near and main[2].startswith("(") and has_values:
                # label continued on the next line together with more values: "(cu ft)  Behind Row 2: 31.8"
                cur["label"] += " " + " ".join(c[2] for c in label_cells)
                add_values(cur, texts, value, m_all, m_part, line)
                last_bottom = line.bottom
                continue
            if main:
                if cur is not None and not has_values and near and not pending and not SECTION_RE.match(main[2]):
                    cur["label"] += " " + " ".join(c[2] for c in label_cells)  # label continued
                    cur["quote"].append(line.text)
                    last_bottom = line.bottom
                    continue
                close()
                cur = new_row(" ".join(c[2] for c in label_cells), texts, value, m_all, m_part, line, main[2])
                for p_texts, p_value, p_all, p_part, p_line in reversed(pending):
                    add_values(cur, p_texts, p_value, p_all, p_part, p_line, front=True)
                pending = []
                last_bottom = line.bottom
                continue
            if subs and cur is not None:
                parent = cur.get("main", cur["label"])
                close()
                pending = []
                cur = new_row(parent + " " + " ".join(c[2] for c in subs), texts, value, m_all, m_part, line, parent)
                last_bottom = line.bottom
                continue
            if has_values and not line.text.lstrip().startswith("*") and (pending or owns_next_label(i)):
                close()
                pending.append((texts, value, m_all, m_part, line))
                last_bottom = line.bottom
                continue
            if has_values and cur is not None and near and not line.text.lstrip().startswith("*"):
                add_values(cur, texts, value, m_all, m_part, line)
                last_bottom = line.bottom
                continue
            close()
            pending = []
            last_bottom = line.bottom
        close()
        return out


def pdf_rows(path: Path, page_texts: list[str]) -> tuple[list[TRow], list[dict]]:
    import pdfplumber

    rows: list[TRow] = []
    notes: list[dict] = []
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            lines = [PLine(ln["text"], ln["top"], ln["bottom"], ln["chars"])
                     for ln in page.extract_text_lines(return_chars=True, strip=True)]
            stored = norm(page_texts[pno - 1]) if pno - 1 < len(page_texts) else ""
            if norm(" ".join(ln.text for ln in lines)) != stored:
                notes.append({"page": pno, "row": "", "reason": "page lines differ from the stored page text"})
            rows.extend(PageTable(pno, lines).rows())
    return rows, notes


def word_rows(rows: list[list[str]]) -> list[TRow]:
    out: list[TRow] = []
    columns: list[str] = []
    section = ""
    for row in rows:
        quote = "\t".join(c.replace("\n", " ") for c in row)
        if len(row) >= 3 and not row[0].strip() and any(c.strip() for c in row[1:]):
            columns = [norm(c) for c in row[1:]]
            continue
        values = list(row[1:])
        if len(row) == 1 or not any(v.strip() for v in values):
            text = norm(row[0])
            if text and len(text) < 60:
                section = text
            continue
        label = norm(row[0])
        n = max(1, len(columns))
        if len(values) == n:
            out.append(TRow(1, section, label, values, list(columns), quote, word=True))
        elif len(values) == 1:
            out.append(TRow(1, section, label, values, list(columns), quote, spanning=n > 1, word=True))
        else:
            out.append(TRow(1, section, label, values, list(columns), quote, partial=True, word=True))
    return out


# =============================================================================================
# facts
# =============================================================================================
NUM = r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
WORD_NUMBERS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}
DASH_ONLY = re.compile(r"^[\s\-–—]*$|^(n/?a|--)$", re.I)
QUAL_RE = re.compile(r"^\s*([A-Za-z][\w.&/ -]{0,30}?)\s*:\s+(.*)$")
UNIT_WORDS = r"(?i)\b(mm|kg|m|l|cu|kw|nm|cc|in|ft|lbs?|deg|gal|gallons?|liters?|litres?|mph|kph|sec|hp|ps)\b"
TIRE_RE = re.compile(r"\b(?:P|LT)?\d{3}/\d{2}\s?Z?R\s?F?\d{2}(?:\s?\d{2,3}(?:/\d{2,3})?\s?[A-Z]{1,2}\b|\s[A-Z]\b|\s?\(\w Rated\))?")
TORQUE_UNIT = r"lb[s.]*\s*[-·]?\s*ft|ft[.\s]*-?\s*lbs?"


def to_num(text: str):
    value = float(text.replace(",", ""))
    return int(value) if value.is_integer() and "." not in text else value


def segments(cell: str) -> list[tuple[str | None, str]]:
    """Split a cell into (qualifier, text) parts: one per line; "LWB: 122.8 in." -> ("LWB", ...);
    "196.9 / 204.7 (LWB)" -> (None, "196.9"), ("LWB", "204.7"); a trailing "(S)" -> qualifier."""
    out: list[tuple[str | None, str]] = []
    for part in [p.strip() for p in (cell or "").split("\n") if p.strip()]:
        pieces = re.split(r"\s+(?=(?:LWB|SWB|SVR|Std\.?|Opt\.?|Optional|Standard)\s*:)", part)
        for piece in pieces:
            m = QUAL_RE.match(piece)
            qual, text = (m.group(1), m.group(2)) if m and not re.match(NUM, m.group(1)) else (None, piece)
            pair = re.match(rf"^(.*?\d)\s+/\s+({NUM}\*?)\s*\(([^()]+)\)$", text)
            if pair and not re.search(UNIT_WORDS, pair.group(3)):
                out.append((qual, pair.group(1)))
                out.append(((qual + "; " if qual else "") + pair.group(3), pair.group(2)))
                continue
            w = re.match(rf"^(?P<v>{NUM}(?:\s*[a-z.]{{1,4}})?)\s+(?P<q>(?:w/|with)\s+.+)$", text, re.I)
            if w and not qual:
                out.append((w.group("q"), w.group("v")))
                continue
            t = re.search(r"\(([^()]*[A-Za-z][^()]*)\)\s*$", text)
            if t and not re.search(UNIT_WORDS, t.group(1)) and t.start() > 0:
                qual = (qual + "; " if qual else "") + t.group(1)
                text = text[:t.start()].strip()
            out.append((qual, text))
    return out


@dataclass
class Ctx:
    facts: list = field(default_factory=list)
    review: list = field(default_factory=list)


def column_views(row: TRow) -> list[tuple[str | None, str]]:
    """(engine_text, cell) per column of a row; one value for all columns -> engine_text None."""
    if row.partial:
        return []
    if row.spanning or len(row.cells) == 1:
        return [(None, row.cells[0] if row.cells else "")]
    return [(row.columns[k] if k < len(row.columns) and len(row.columns) > 1 else None, cell)
            for k, cell in enumerate(row.cells)]


def add_fact(ctx: Ctx, row: TRow, key: str, value, engine: str | None, original: str, qual: str | None = None,
             row_label: str | None = None, quote: str | None = None) -> None:
    if not plausible(key, value):
        review(ctx, row, f"{key}: implausible value {value!r} for '{original[:80]}' (table probably mis-read)")
        return
    label = row_label or row.label
    if row.sub and not row.nested:
        label += f" [{row.sub}]"
    if row.spanning and len(row.columns) > 1:
        label += " [one value for all columns]"
    if qual:
        label += f" [{qual}]"
    ctx.facts.append({"key": key, "value": value, "page": row.page, "quote": quote or row.quote,
                      "original": norm(original), "engine_text": engine, "row": label})


# Physical plausibility bounds of the parsed numbers (US units). A number outside them is not a
# fact but a sign of a mis-read table (e.g. a value split across two columns); it goes to review.
PLAUSIBLE = {
    "power_hp": (40, 1200), "system_power_hp": (40, 1500), "torque_lb_ft": (40, 1300),
    "engine_displacement_cc": (500, 8500), "turning_circle_ft": (25, 50), "wheel_size_in": (13, 24),
    "length_in": (120, 260), "width_in": (55, 95), "height_in": (40, 90), "wheelbase_in": (80, 170),
    "track_front_in": (45, 80), "track_rear_in": (45, 80), "ground_clearance_in": (3, 16),
    "curb_weight_lb": (1500, 9000), "cargo_cu_ft": (2, 120), "cargo_max_cu_ft": (10, 200),
    "passenger_volume_cu_ft": (40, 200), "fuel_tank_gal": (5, 50), "seats": (2, 9), "towing_lb": (500, 20000),
}


def plausible(key: str, value) -> bool:
    if key in PLAUSIBLE and isinstance(value, (int, float)):
        lo, hi = PLAUSIBLE[key]
        return lo <= value <= hi
    if key == "compression_ratio":
        m = re.match(r"^([\d.]+):1$", str(value))
        return bool(m) and 6 <= float(m.group(1)) <= 25
    if key in ("power_rpm", "torque_rpm"):
        nums = [float(x.replace(",", "")) for x in re.findall(r"[\d,]+", str(value))]
        return bool(nums) and all(500 <= x <= 9500 for x in nums)
    return True


def review(ctx: Ctx, row: TRow, reason: str) -> None:
    ctx.review.append({"page": row.page, "row": row.label, "reason": reason, "quote": row.quote[:300]})


IN_UNITS = {"in": r"(?<![a-z])(in\.?|inch(es)?|\"|”)(?![a-z])", "mm": r"(?<![a-z])mm(?![a-z])"}
LB_UNITS = {"lb": r"(?<![a-z])lbs?\.?(?![a-z])", "kg": r"(?<![a-z])kg(?![a-z])"}
CUFT_UNITS = {"cuft": r"cu\.?\s*f(ee)?t\.?|cubic\s+feet|ft3|ft³", "l": r"(?<![a-z])(liters?|litres?|l)(?![a-z])"}
GAL_UNITS = {"gal": r"(?<![a-z])gal(lons?)?\.?(?![a-z])", "l": r"(?<![a-z])(liters?|litres?|l)(?![a-z])"}
FT_UNITS = {"ft": r"(?<![a-z])(ft|feet)\.?(?![a-z])", "m": r"(?<![a-z])m(?![a-z])"}
HP_UNITS = {"hp": r"(?<![a-z])(hp|horsepower)(?![a-z])", "kw": r"(?<![a-z])kw(?![a-z])"}


def label_unit(label: str, units: dict) -> str | None:
    """Unit named first in the label: "Length (in/mm)" -> in, "Turning circle ft (m)" -> ft."""
    best = None
    for unit, pattern in units.items():
        m = re.search(pattern, label, re.I)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), unit)
    return best[1] if best else None


def number_in(text: str, label: str, units: dict, want: str):
    """The number of `text` in unit `want`: explicit ("2.93 in 74.5 mm", "4,918 lbs. (2,231 kg)")
    or, for a bare leading number, from the label's first unit ("105.7/2686" under "(in/mm)")."""
    m = re.search(rf"({NUM})\s*(?:{units[want]})", text, re.I)
    if m:
        return to_num(m.group(1))
    if any(re.search(p, text, re.I) for u, p in units.items() if u != want):
        if not re.match(rf"^\s*(?:from\s+)?{NUM}\s*(/|$|\()", text, re.I):
            return None
    if label_unit(label, units) == want:
        m = re.match(rf"^\s*(?:from\s+)?({NUM})\s*(?:/\s*{NUM}|\(\s*{NUM}\s*\w*\s*\))?\s*$", text, re.I)
        if m:
            return to_num(m.group(1))
    return None


def numeric(ctx: Ctx, row: TRow, key: str, units: dict, want: str, keep_qual=None, skip_qual=None) -> None:
    for engine, cell in column_views(row):
        if not cell or DASH_ONLY.match(cell):
            continue
        loose = [x for x in cell.split("\n") if x.strip() and not re.search(r"\d", x)]
        if loose:
            review(ctx, row, f"{key}: cell has a text line without a number ({'; '.join(loose)[:60]}); not paired")
            continue
        for qual, text in segments(cell):
            if re.match(r"^\(\s*[\d.,]+\s*(mm|kg|l|m)\s*\)$", text, re.I):
                continue  # metric equivalent on its own line, e.g. "(1,580 kg)"
            if not text or DASH_ONLY.match(text):
                continue
            if qual and skip_qual and re.search(skip_qual, qual, re.I):
                continue
            if qual and keep_qual is not None and not re.search(keep_qual, qual, re.I) \
                    and not re.match(r"(?i)^(w/|with)\s+(?!.*mirror)", qual):
                review(ctx, row, f"{key}: value for '{qual}' ({text}) not taken")
                continue
            if "*" in text:
                review(ctx, row, f"{key}: value with a footnote marker '{text}'")
                continue
            value = number_in(text, row.label, units, want)
            if value is None:
                review(ctx, row, f"{key}: no value in {want} readable in '{text}'")
                continue
            add_fact(ctx, row, key, value, engine, f"{row.label} {text}", qual)
    if row.partial:
        review(ctx, row, f"{key}: merged cell over some columns")


def text_fact(ctx: Ctx, row: TRow, key: str, first_paragraph: bool = False, row_label=None) -> None:
    for engine, cell in column_views(row):
        if not cell or DASH_ONLY.match(cell):
            continue
        value = cell.split("\n")[0] if (first_paragraph and row.word) else cell
        if not row.word:  # wrapped lines: a word broken after a hyphen continues on the next line
            value = re.sub(r"(?<=[A-Za-z])-\n(?=[a-z])", "-", value)
        value = norm(re.sub(r"(\d)-\s+(in\b)", r"\1-\2", norm(value)))
        if value:
            add_fact(ctx, row, key, value, engine, f"{row.label} {cell}", None, row_label)
    if row.partial:
        review(ctx, row, f"{key}: merged cell over some columns")


def power_torque(ctx: Ctx, row: TRow, key: str) -> None:
    rpm_key = "power_rpm" if key == "power_hp" else "torque_rpm"
    for engine, cell in column_views(row):
        if not cell or DASH_ONLY.match(cell):
            continue
        for qual, text in segments(cell):
            if not text or DASH_ONLY.match(text):
                continue
            if "*" in text:
                review(ctx, row, f"{key}: value with a footnote marker '{text}'")
                continue
            both = text + " " + row.label
            if key == "torque_lb_ft" and not re.search(TORQUE_UNIT, both, re.I):
                review(ctx, row, f"{key}: torque unit lb-ft not stated for '{text}'")
                continue
            if key == "power_hp" and not re.search(r"(?i)\b(hp|horsepower|bhp)\b", both):
                review(ctx, row, f"{key}: unit hp not stated for '{text}'")
                continue
            if re.match(r"^\(\s*[\d.,]+\s*(kw|nm|ps)\s*\)$", text, re.I):
                continue  # metric equivalent on its own line, e.g. "(185 kW)"
            m = re.match(rf"^\s*({NUM})\s*(?:hp|bhp|{TORQUE_UNIT})?\.?\s*(?:@|at)\s*({NUM}(?:\s*[-–—]\s*{NUM})?)\s*(?:rpm)?",
                         text, re.I)
            if m:
                add_fact(ctx, row, key, to_num(m.group(1)), engine, f"{row.label} {text}", qual)
                add_fact(ctx, row, rpm_key, re.sub(r"\s+", "", m.group(2)).replace("—", "-"), engine, f"{row.label} {text}", qual)
                continue
            m = re.match(rf"^\s*({NUM})\s*(?:hp|bhp|{TORQUE_UNIT})?\.?\s*$", text, re.I)
            if m:
                add_fact(ctx, row, key, to_num(m.group(1)), engine, f"{row.label} {text}", qual)
                continue
            review(ctx, row, f"{key}: cannot read '{text}'")
    if row.partial:
        review(ctx, row, f"{key}: merged cell over some columns")


def displacement(ctx: Ctx, row: TRow) -> None:
    for engine, cell in column_views(row):
        text = norm(cell)
        if not text or DASH_ONLY.match(text):
            continue
        m = re.search(rf"({NUM})\s*cc\b", text, re.I)
        bare = re.match(rf"^\s*({NUM})\s*$", text)
        if m:
            add_fact(ctx, row, "engine_displacement_cc", to_num(m.group(1)), engine, f"{row.label} {text}")
        elif bare and re.search(r"(?i)\bcc\b", row.label):
            add_fact(ctx, row, "engine_displacement_cc", to_num(bare.group(1)), engine, f"{row.label} {text}")
        else:
            review(ctx, row, f"engine_displacement_cc: no cc value in '{text}'")


def bore_stroke(ctx: Ctx, row: TRow) -> None:
    for engine, cell in column_views(row):
        text = norm(cell)
        if not text or DASH_ONLY.match(text):
            continue
        m = re.search(rf"({NUM})\s*(?:x|/)\s*({NUM})\s*(mm|in)?", text)
        if not m:
            review(ctx, row, f"bore_stroke: cannot read '{text}'")
            continue
        unit = m.group(3) or label_unit(row.label, {"mm": r"\bmm\b", "in": r"\(in\.?\)|\bin\.?\b"})
        if unit is None:
            review(ctx, row, f"bore_stroke: unit not stated for '{text}'")
            continue
        add_fact(ctx, row, f"bore_stroke_{unit}", f"{m.group(1)} x {m.group(2)}", engine, f"{row.label} {text}")
        d = re.match(rf"^\s*{NUM}\s*x\s*{NUM}\s*/\s*({NUM})\s*$", text)
        if d and re.search(r"(?i)/\s*displacement\s*\(cc\)", row.label):
            add_fact(ctx, row, "engine_displacement_cc", to_num(d.group(1)), engine, f"{row.label} {text}")
        m2 = re.search(rf"\(\s*({NUM})\s*(?:x|/)\s*({NUM})\s*\)", text[m.end():])
        if m2 and unit == "mm" and re.search(r"\(in\)", row.label):
            add_fact(ctx, row, "bore_stroke_in", f"{m2.group(1)} x {m2.group(2)}", engine, f"{row.label} {text}")


def bore_and_stroke_rows(ctx: Ctx, bore: TRow, stroke: TRow) -> None:
    """Separate rows "Bore 3.25 in 82.5 mm" / "Stroke 3.65 in 92.8 mm" or "Bore (mm) 82.5" /
    "Stroke (mm) 92.8" on adjacent lines -> bore_stroke_<unit> "82.5 x 92.8"."""
    joined = TRow(bore.page, bore.section, "Bore / Stroke", [], bore.columns, bore.quote + " " + stroke.quote,
                  bore.spanning, bore.partial or stroke.partial, bore.sub, bore.sub_cells, bore.nested)
    b_views, s_views = column_views(bore), column_views(stroke)
    if len(b_views) != len(s_views) or not b_views:
        review(ctx, bore, "bore_stroke: bore and stroke rows do not pair up")
        return
    for (engine, b), (_, s) in zip(b_views, s_views):
        b, s = norm(b), norm(s)
        for unit in ("in", "mm"):
            mb = re.search(rf"({NUM})\s*{unit}\b", b)
            ms = re.search(rf"({NUM})\s*{unit}\b", s)
            if not (mb and ms) and label_unit(bore.label, {unit: rf"\b{unit}\b"}) == unit \
                    and label_unit(stroke.label, {unit: rf"\b{unit}\b"}) == unit:
                mb = re.match(rf"^({NUM})\s*(\([^()]*\))?$", b)
                ms = re.match(rf"^({NUM})\s*(\([^()]*\))?$", s)
            if mb and ms:
                add_fact(ctx, joined, f"bore_stroke_{unit}", f"{mb.group(1)} x {ms.group(1)}", engine,
                         f"{bore.label} {b}; {stroke.label} {s}")


def compression(ctx: Ctx, row: TRow) -> None:
    for engine, cell in column_views(row):
        text = norm(cell)
        if not text or DASH_ONLY.match(text):
            continue
        m = re.search(rf"({NUM})\s*:\s*1\b", text)
        if m:
            add_fact(ctx, row, "compression_ratio", f"{m.group(1)}:1", engine, f"{row.label} {text}")
        elif re.match(rf"^\s*({NUM})\s*$", text) and (re.search(r":\s*1\)?\s*$", row.label)
                                                       or re.match(r"(?i)^compression\s*ratio\s*$", row.label)):
            add_fact(ctx, row, "compression_ratio", f"{text.strip()}:1", engine, f"{row.label} {text}")
        else:
            review(ctx, row, f"compression_ratio: cannot read '{text}'")


def tires_wheels(ctx: Ctx, row: TRow, tires: bool, wheels: bool) -> None:
    for engine, cell in column_views(row):
        if not cell:
            continue
        seen_t, seen_w = set(), set()
        for ln in [x for x in re.sub(r"(\d)-\s*\n\s*", r"\1-", cell).split("\n") if x.strip()]:
            if re.search(r"(?i)\bspare\b", ln):
                review(ctx, row, f"tires/wheels: spare wheel line not taken ({ln[:60]})")
                continue
            if tires:
                for m in TIRE_RE.finditer(ln):
                    size = norm(m.group(0))
                    if size not in seen_t:
                        seen_t.add(size)
                        add_fact(ctx, row, "tires", size, engine, f"{row.label} {ln}")
            if wheels:
                sizes = re.findall(r"\b(\d{2}(?:\.\d)?)\s*(?:-|\s)?(?:in\b|inch\b|\"|”)", ln)
                sizes += re.findall(r"\b(\d{2})\s*x\s*\d{1,2}(?:\.\d+)?\s*J?\s*(?:in\b|-in\b|\"|”|inch)", ln)
                sizes += re.findall(r"J\s*x\s*(\d{2})\s*(?:\"|”|in\b|-in\b)", ln)
                for s in sizes:
                    if s not in seen_w and 13 <= float(s) <= 24:
                        seen_w.add(s)
                        add_fact(ctx, row, "wheel_size_in", to_num(s), engine, f"{row.label} {ln}")
    if row.partial:
        review(ctx, row, "tires/wheels: merged cell over some columns")


def track_pair(ctx: Ctx, row: TRow) -> None:
    for engine, cell in column_views(row):
        text = norm(cell)
        m = re.match(rf"^\s*({NUM})\s*/\s*({NUM})\s*(in\.?|\")", text)
        if not m and label_unit(row.label, IN_UNITS) == "in":
            m = re.match(rf"^\s*({NUM})\s*/\s*({NUM})\s*(\(.*\))?$", text)
        if m:
            add_fact(ctx, row, "track_front_in", to_num(m.group(1)), engine, f"{row.label} {text}", "front")
            add_fact(ctx, row, "track_rear_in", to_num(m.group(2)), engine, f"{row.label} {text}", "rear")
        elif text:
            review(ctx, row, f"track: cannot read '{text}'")


def front_rear(ctx: Ctx, row: TRow) -> None:
    """'Front: ... Rear: ...' per column (JLR "Brake Type", "Brake Diameter (in)", Audi "Brake Construction")."""
    for engine, cell in column_views(row):
        parts = re.split(r"(?i)\b(front|rear)\s*:\s*", norm(cell))
        if len(parts) < 3:
            if norm(cell):
                review(ctx, row, f"brakes: no Front:/Rear: parts in '{norm(cell)}'")
            continue
        for side, text in zip(parts[1::2], parts[2::2]):
            text = text.strip().rstrip(";,")
            if text and not DASH_ONLY.match(text):
                add_fact(ctx, row, f"{side.lower()}_brakes", text, engine, f"{row.label} {side}: {text}", side)
    if row.partial:
        review(ctx, row, "brakes: merged cell over some columns")


def combined_brakes(ctx: Ctx, row: TRow) -> None:
    """VW "Brakes": '... 11.3 x 1.0-in vented front discs and 10.7 x 0.4-in solid rear discs'."""
    for engine, cell in column_views(row):
        text = re.sub(r"(\d)-\s+(in\b)", r"\1-\2", norm(cell))
        found = False
        for side in ("front", "rear"):
            m = re.search(rf"\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?-?\s*in\.?\s+(?:[a-z]+\s+){{0,2}}{side}\s+(?:discs?|drums?)",
                          text, re.I) or re.search(
                rf"\d+(?:\.\d+)?-?\s*(?:in|inch)\.?\s+{side}\b(?:\s+(?:brake\s+)?(?:discs?|drums?))?", text, re.I)
            if m:
                found = True
                add_fact(ctx, row, f"{side}_brakes", norm(m.group(0)), engine, f"{row.label} {text}", side)
        if not found and text:
            review(ctx, row, f"brakes: front/rear not separable in '{text[:120]}'")
    if row.partial:
        review(ctx, row, "brakes: merged cell over some columns")


def transmission_from_sub(ctx: Ctx, row: TRow) -> None:
    """VW: the sub-heading right above "Transmission Gear Ratios" names the transmission per column."""
    if not row.sub or row.nested or not row.sub_quote:
        return
    if re.search(r"(?i)\b(2nd|3rd|[4-9]th|10th|reverse|final)\b", row.label) and not re.search(r"(?i)\b1st\b", row.label):
        return  # only the first gear-ratio row, right under the heading
    for k, cell in enumerate(row.sub_cells or [row.sub]):
        cell = norm(cell)
        if not cell:
            continue
        engine = row.columns[k] if len(row.columns) > 1 and k < len(row.columns) else None
        ctx.facts.append({"key": "transmission_description", "value": cell, "page": row.page,
                          "quote": norm(row.sub_quote + " " + row.quote), "original": cell, "engine_text": engine,
                          "row": "Transmission (heading over the gear ratios)"})


def cargo(ctx: Ctx, row: TRow) -> None:
    label = row.label
    for engine, cell in column_views(row):
        segs = segments(cell)
        # "Cargo Volume Behind Row 2/ Behind Row 1 (cu. ft.)" with "27.6 / 56.9"
        conds = re.findall(r"(?i)behind\s+(?:row\s*\d|(?:1st|2nd|3rd)\s+row)", label)
        if len(conds) == 2 and len(segs) == 1:
            nums = re.findall(rf"({NUM})", segs[0][1])
            if len(nums) == 2 and re.match(rf"^\s*{NUM}\s*/\s*{NUM}\s*$", segs[0][1]):
                segs = [(conds[0], nums[0]), (conds[1], nums[1])]
        two_conditions = bool(re.search(r"(?i)\b(fixed|up|upright)\b", label) and re.search(r"(?i)\b(folded|down)\b", label))
        if two_conditions and len(segs) == 1 and len(re.findall(NUM, segs[0][1])) == 1 and not segs[0][0]:
            review(ctx, row, f"cargo: one value '{segs[0][1]}' under a label naming two conditions")
            continue
        for qual, text in segs:
            if not text or DASH_ONLY.match(text):
                continue
            where = qual or label
            if re.search(r"(?i)behind\s+(the\s+)?(1st|first)\s+row|behind\s+row\s*1\b|seat\w*\s+(folded|down)|folded|maximum|\bmax\b", where):
                key = "cargo_max_cu_ft"
            elif re.search(r"(?i)behind\s+(the\s+)?(2nd|second|3rd|third)\s+row|behind\s+row\s*[23]\b|seat\w*\s+(up|upright|in\s+place)", where):
                key = "cargo_cu_ft"
            elif not qual and re.search(r"(?i)^(trunk|cargo|luggage|loadspace)\s+(volume|capacity|space)\b(?!.*\b(under|cover|floor)\b)", label):
                key = "cargo_cu_ft"
            else:
                review(ctx, row, f"cargo: condition not clear for '{text}'")
                continue
            if "*" in text:
                review(ctx, row, f"{key}: value with a footnote marker '{text}'")
                continue
            value = number_in(text, label, CUFT_UNITS, "cuft")
            if value is None:
                review(ctx, row, f"{key}: no cu ft value readable in '{text}'")
                continue
            add_fact(ctx, row, key, value, engine, f"{label} {text}", qual)
    if row.partial:
        review(ctx, row, "cargo: merged cell over some columns")


def seats(ctx: Ctx, row: TRow) -> None:
    for engine, cell in column_views(row):
        text = norm(cell)
        if not text or DASH_ONLY.match(text):
            continue
        m = re.match(r"^(\d{1,2})(\s*(seats|passengers))?$", text, re.I)
        if m:
            add_fact(ctx, row, "seats", int(m.group(1)), engine, f"{row.label} {text}")
        elif text.lower() in WORD_NUMBERS:
            add_fact(ctx, row, "seats", WORD_NUMBERS[text.lower()], engine, f"{row.label} {text}")
        else:
            review(ctx, row, f"seats: cannot read '{text}'")


def simple_text_key(key: str, first_paragraph: bool = False):
    return lambda ctx, row: text_fact(ctx, row, key, first_paragraph)


# label rules: (label regex, section regex or None, handler); the first matching rule is used
RULES = [
    (r"^(max(imum)?\.?\s+|peak\s+)?(net\s+)?(horse\s*power|power|output)\b(?!-to)(?!.*(electric|motor|system|combined|total))",
     None, lambda c, r: power_torque(c, r, "power_hp")),
    (r"^(total\s+)?system\s+(power|output|horsepower)|^(combined|total)\s+(system\s+)?(power|output|horsepower)", None,
     lambda c, r: numeric(c, r, "system_power_hp", HP_UNITS, "hp")),
    (r"^(max(imum)?\.?\s+|peak\s+)?(net\s+)?torque\b(?!.*(electric|motor|system|combined|total))", None,
     lambda c, r: power_torque(c, r, "torque_lb_ft")),
    (r"^(max(imum)?\.?\s+)?electric\s+motor\s+(power|output)|^electric\s+motor$", None, simple_text_key("electric_motor")),
    (r"^(total\s+)?displacement\b", None, displacement),
    (r"^bore\s*(/|x|and)\s*stroke", None, bore_stroke),
    (r"^compression(\s*ratio)?", None, compression),
    (r"^valve\s*(train|gear)\b", None, simple_text_key("valvetrain")),
    (r"^(fuel\s*(system|injection|delivery)|injection(\s+system)?|fuel\s*/\s*induction|induction\s*/\s*fuel\s*injection)\b", None,
     simple_text_key("injection")),
    (r"^(engine(\s*type)?|type)$", r"(?i)^engine\b(?!.*design)", simple_text_key("engine_description")),
    (r"^engine(\s*type)?$", None, simple_text_key("engine_description")),
    (r"^(transmission(\s+type)?|gearbox)$", None, simple_text_key("transmission_description", True)),
    (r"^transmission\s+gear\s+ratios", None, transmission_from_sub),
    (r"^front\s+suspension\b", None, simple_text_key("front_suspension", True)),
    (r"^rear\s+suspension\b", None, simple_text_key("rear_suspension", True)),
    (r"^front\s+(brakes?|discs?)\b", None, simple_text_key("front_brakes")),
    (r"^rear\s+(brakes?|discs?)\b", None, simple_text_key("rear_brakes")),
    (r"^brakes?\s+(type|diameter|size|construction)\b", None, front_rear),
    (r"^brakes$", None, combined_brakes),
    (r"^steering(\s+(type|system))?$", None, simple_text_key("steering")),
    (r"^type$", r"(?i)steering", simple_text_key("steering")),
    (r"^turning\s+(circle|diameter)(?!.*lock)", None,
     lambda c, r: numeric(c, r, "turning_circle_ft", FT_UNITS, "ft", keep_qual=r"^(LWB|SWB|SVR|Std|Standard)")),
    (r"^(wheels?\s*(/|and|&)\s*tires?|wheel\s+and\s+tire\s+size|tires?\s*(/|and|&)\s*wheels?)\b", None,
     lambda c, r: tires_wheels(c, r, True, True)),
    (r"^tires?\b", None, lambda c, r: tires_wheels(c, r, True, False)),
    (r"^wheels?\b", None, lambda c, r: tires_wheels(c, r, False, True)),
    (r"^(overall\s+)?length\b(?!.*\b(load|cargo|between|bed|floor)\b)", None,
     lambda c, r: numeric(c, r, "length_in", IN_UNITS, "in",
                          keep_qual=r"^(LWB|SWB|SVR|Std|Standard|Dynamic|Pure|Prestige|HSE|SE|S)\b")),
    (r"^(overall\s+)?width\b(?!.*(mirrors?\s+(folded|out)|with\s+mirrors|including\s+mirrors|between|arch|load|cargo|opening))", None,
     lambda c, r: numeric(c, r, "width_in", IN_UNITS, "in", keep_qual=r"^excluding\s+mirrors",
                          skip_qual=r"including\s+mirrors|with\s+mirrors|w/\s*mirrors|mirrors\s+(folded|out)")),
    (r"^(overall\s+)?height\b(?!.*(off-?road|access|load|cargo|opening|step|lift))", None,
     lambda c, r: numeric(c, r, "height_in", IN_UNITS, "in",
                          keep_qual=r"^(LWB|SWB|SVR|Std|Standard|Coupe|5-Door|Convertible)\b", skip_qual=r"access|off-?road")),
    (r"^wheelbase\b", None,
     lambda c, r: numeric(c, r, "wheelbase_in", IN_UNITS, "in", keep_qual=r"^(LWB|SWB|Std|Standard)\b")),
    (r"^track\s*,?\s*\(?\s*front\s*/\s*rear\)?", None, track_pair),
    (r"^(front\s+track|track,?\s+front)\b", None, lambda c, r: numeric(c, r, "track_front_in", IN_UNITS, "in")),
    (r"^(rear\s+track|track,?\s+rear)\b", None, lambda c, r: numeric(c, r, "track_rear_in", IN_UNITS, "in")),
    (r"^(min(imum)?\.?\s+)?(ground|running)\s+clearance(?!.*off-?road)", None,
     lambda c, r: numeric(c, r, "ground_clearance_in", IN_UNITS, "in",
                          keep_qual=r"^(standard|std|normal|LWB|SWB)\b", skip_qual=r"off-?road|access")),
    (r"^(base\s+)?curb\s*weight\b", None, lambda c, r: numeric(c, r, "curb_weight_lb", LB_UNITS, "lb", keep_qual=r".")),
    (r"^(trunk|cargo|luggage|loadspace)\s*(volume|capacity|space)|^cargo\b", None, cargo),
    (r"^passenger\s*volume\b", None, lambda c, r: numeric(c, r, "passenger_volume_cu_ft", CUFT_UNITS, "cuft")),
    (r"^fuel\s+(tank|capacity)\b", None, lambda c, r: numeric(c, r, "fuel_tank_gal", GAL_UNITS, "gal")),
    (r"^(seating(\s*capacity)?|seats|number\s+of\s+seats)\b", None, seats),
    (r"^(max(imum)?\.?\s+)?(towing|trailer\s+towing)(\s+capacity)?\b|^braked\s+trailer\b|"
     r"^(?!.*unbraked)(max(imum)?\.?\s+)?(permissible\s+)?(braked\s+)?towable\s+mass", None,
     lambda c, r: numeric(c, r, "towing_lb", LB_UNITS, "lb", keep_qual=r"^braked", skip_qual=r"unbraked|tongue")),
]
COMPILED = [(re.compile(p, re.I), re.compile(s) if s else None, h) for p, s, h in RULES]


def facts_from_rows(rows: list[TRow]) -> Ctx:
    ctx = Ctx()
    prev_label = ""
    skip = set()
    for i, row in enumerate(rows):
        if i in skip:
            continue
        label = re.sub(r"(?<=[A-Za-z)])[\d¹²³*]+$", "", row.label).strip()  # footnote digits "Systems3"
        if label != row.label:
            row = TRow(**{**row.__dict__, "label": label})
        matched = next(((p, s, h) for p, s, h in COMPILED
                        if p.search(label) and (s is None or s.search(row.section or ""))), None)
        if re.match(r"(?i)^bore\b", label) and i + 1 < len(rows) and re.match(r"(?i)^stroke\b", rows[i + 1].label) \
                and rows[i + 1].page == row.page and not re.search(r"(?i)stroke", label):
            if row.nested:
                review(ctx, row, "bore/stroke under a sub-heading that splits the columns; not paired")
            else:
                bore_and_stroke_rows(ctx, row, rows[i + 1])
            skip.add(i + 1)
            continue
        if re.match(r"(?i)^(front|rear)$", label) and re.match(r"(?i)^suspension\b", prev_label):
            text_fact(ctx, row, f"{label.lower()}_suspension", True, row_label=f"{prev_label} - {row.label}")
            continue
        if not re.match(r"(?i)^(front|rear)$", label):
            prev_label = label
        if matched is None:
            if re.search(r"(?i)wheels|tires", row.section or "") and (TIRE_RE.search(label) or re.search(r"\bx\s*\d{2}\s*[\"”]", label)):
                tires_wheels(ctx, TRow(**{**row.__dict__, "cells": [row.label], "columns": [], "spanning": False,
                                          "partial": False}), True, True)
            continue
        if row.nested and matched[2] is not transmission_from_sub:
            review(ctx, row, "values under a sub-heading that splits the columns; not paired")
            continue
        if row.partial and not row.word:
            review(ctx, row, "merged cell over some columns; not paired")
            continue
        if row.partial and row.word:
            review(ctx, row, "Word row with fewer cells than column headings; not paired")
            continue
        matched[2](ctx, row)
    return ctx


# =============================================================================================
# documents
# =============================================================================================
def manifest_rows(host: str) -> list[dict]:
    path = MANIFEST_DIR / f"{host}.csv"
    if not path.exists():
        return []
    last: dict[str, dict] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            last[row["url"]] = row
    return [r for r in last.values() if r.get("doc_type") == "press_specifications" and r.get("status") == "ok"
            and r.get("path")]


def load_pagetext(sha: str) -> dict:
    with gzip.open(RAW_ROOT / "pagetext" / f"{sha}.json.gz", "rt", encoding="utf-8") as handle:
        return json.load(handle)


def quote_ok(quote: str, page_text: str) -> bool:
    return norm(quote) in norm(page_text)


# The document must name its line somewhere (the site's item title can be wrong, e.g. the JLR
# item "2018 Discovery Sport Technical Specs (US)" holds the spec sheet of the 2018 Discovery).
LINE_NAMES = {
    "volkswagen/jetta": r"\b(Jetta|GLI)\b", "volkswagen/passat": r"\bPassat\b",
    "volkswagen/tiguan": r"\bTiguan\b", "volkswagen/atlas": r"\bAtlas\b", "volkswagen/arteon": r"\bArteon\b",
    "volkswagen/touareg": r"\bTouareg\b",
    "audi/a3": r"\b(A3|S3|RS ?3)\b", "audi/a4": r"\b(A4|S4|allroad)\b", "audi/a5": r"\b(A5|S5|RS ?5)\b",
    "audi/a6": r"\b(A6|S6|RS ?6)\b", "audi/q3": r"\bQ3\b", "audi/q5": r"\bS?Q5\b", "audi/q7": r"\bS?Q7\b",
    "jeep/grand-cherokee": r"(?i)grand\s+cherokee", "jeep/cherokee": r"(?i)(?<!grand )cherokee",
    "jeep/compass": r"(?i)\bcompass\b",
    "land-rover/range-rover": r"(?i)range\s+rover(?!\s+(sport|evoque|velar))",
    "land-rover/range-rover-sport": r"(?i)range\s+rover\s+sport",
    "land-rover/range-rover-evoque": r"(?i)evoque", "land-rover/discovery-sport": r"(?i)discovery\s+sport|\bLR2\b",
}


def extract_doc(host: str, row: dict) -> dict:
    short, publisher = HOSTS[host]
    sha = row["sha256"]
    raw = RAW_ROOT / row["path"]
    pt = load_pagetext(sha)
    pages = pt["pages"]
    line_slug = row["line"].split("/", 1)[1]
    key = f"press-{short}-{line_slug}-{row['year']}-{sha[:8]}"
    review_items: list[dict] = []
    if "rows" in pt:
        trows = word_rows(pt["rows"])
    else:
        trows, notes = pdf_rows(raw, pages)
        review_items += notes
    ctx = facts_from_rows(trows)
    facts = []
    for fact in ctx.facts:
        page_text = pages[fact["page"] - 1] if fact["page"] - 1 < len(pages) else ""
        fact.pop("_sub_quote", None)
        if not quote_ok(fact["quote"], page_text):
            review_items.append({"page": fact["page"], "row": fact["row"],
                                 "reason": f"quote not found in the page text; {fact['key']}={fact['value']} dropped"})
            continue
        facts.append(fact)
    # de-duplicate identical facts (same key, value, engine, page, row)
    seen = set()
    unique = []
    for fact in facts:
        ident = (fact["key"], json.dumps(fact["value"]), fact["engine_text"], fact["page"], fact["row"])
        if ident not in seen:
            seen.add(ident)
            unique.append(fact)
    review_items += ctx.review
    year = int(row["year"])
    text_years = sorted({int(y) for y in re.findall(r"\b(20[12]\d)\b", " ".join(pages[:1])[:400])})
    if text_years and year not in text_years:
        review_items.append({"page": 1, "row": "model year",
                             "reason": f"manifest year {year} (from the document title on the site) not named at the "
                                       f"top of the document, which names {text_years}"})
    status = "ok" if unique else ("no_text" if not norm(" ".join(pages)) else "no_spec_rows")
    name = LINE_NAMES.get(row["line"])
    if unique and name and not re.search(name, " ".join(pages)):
        review_items.insert(0, {"page": 1, "row": "model",
                                "reason": f"the document never names the line {row['line']} (pattern {name}); "
                                          f"its {len(unique)} facts are withheld (title on the site: {row['title']})"})
        unique = []
        status = "model_mismatch"
    if unique and text_years and year not in text_years:
        review_items.insert(0, {"page": 1, "row": "model year",
                                "reason": f"the document is headed with model year {text_years}, not {year}; "
                                          f"its {len(unique)} facts are withheld (title on the site: {row['title']})"})
        unique = []
        status = "year_mismatch"
    return {
        "doc": {
            "key": key,
            "make": row["make"],
            "lines": [row["line"]],
            "years": [year],
            "doc_type": "press_specifications",
            "title": row["title"],
            "path": str(raw),
            "url": row["url"],
            "page_url": "",
            "sha256": sha,
            "retrieved_at": row["retrieved_at"],
            "tier": "A",
            "source_type": "PRESS_RELEASE",
            "publisher": publisher,
            "authenticity": "OFFICIAL_PUBLISHER",
        },
        "extractor": EXTRACTOR,
        "pages": len(pages),
        "edition_market": "US",
        "status": status,
        "engine_codes": [],
        "review": review_items,
        "facts": unique,
    }


def out_path(doc: dict) -> Path:
    return WORK / doc["doc"]["make"] / "extracted" / f"{doc['doc']['key']}.json"


def verify(paths: list[Path]) -> tuple[int, int]:
    total = bad = 0
    for path in paths:
        doc = json.loads(path.read_text(encoding="utf-8"))
        pages = load_pagetext(doc["doc"]["sha256"])["pages"]
        for fact in doc["facts"]:
            total += 1
            if not quote_ok(fact["quote"], pages[fact["page"] - 1]):
                bad += 1
                print(f"  QUOTE NOT FOUND {path.name} {fact['key']} {fact['quote'][:80]}")
    return total, bad


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", action="append", choices=list(HOSTS))
    parser.add_argument("--verify", action="store_true", help="only verify the quotes of the written files")
    args = parser.parse_args(argv)
    hosts = args.host or list(HOSTS)
    written: list[Path] = []
    if args.verify:
        for host in hosts:
            short = HOSTS[host][0]
            for make in ("volkswagen", "audi", "jeep", "land-rover"):
                written += sorted((WORK / make / "extracted").glob(f"press-{short}-*.json"))
    else:
        for host in hosts:
            rows = manifest_rows(host)
            per_key: Counter = Counter()
            for row in rows:
                try:
                    doc = extract_doc(host, row)
                except Exception as exc:  # keep going; report the document
                    print(f"  ERROR {row['path']}: {exc!r}")
                    continue
                path = out_path(doc)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
                written.append(path)
                per_key.update(f["key"] for f in doc["facts"])
                print(f"  {doc['status']:>12} {len(doc['facts']):>4} facts {len(doc['review']):>3} review  {path.name}")
            print(f"== {host}: {len(rows)} documents; facts per key: {dict(sorted(per_key.items()))}")
    total, bad = verify(written)
    print(f"quote check: {total} facts, {bad} quotes not found in the page text")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

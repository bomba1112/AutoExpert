"""Shared reading of Teoalida databases (next-stage prompt, stage A).

The workbooks start with service rows (fill counters, ratios, "SAMPLE" notices) above the real
column names, so the header row is found by its content. Duplicate downloads ("(1)", "__1_")
are recognised by sha256 and read once. Written for the full databases as well as the samples:
nothing here depends on the sample's row counts or on which makes it contains.

  uv run --no-project --with openpyxl --with xlrd python scripts/teoalida_common.py   # inventory
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

TEO_RAW = RAW_ROOT / "teoalida"
MANIFEST = WORK / "_shared" / "manifest_teoalida.csv"
OUT = WORK / "_shared" / "teoalida"
FIELDS = ["file", "sha256", "bytes", "duplicate_of", "dataset", "sheets", "raw_document_id", "status", "note"]
# dataset name from the file name (the sample and the full database share it)
DATASETS = [
    ("ravenol", re.compile(r"^Ravenol", re.I)),
    ("ymm_trim_specs", re.compile(r"^Year-Make-Model-Trim-Specs", re.I)),
    ("ymm", re.compile(r"^Year-Make-Model-by", re.I)),
    ("tire_size", re.compile(r"^TireSize", re.I)),
    ("car_models_list", re.compile(r"^Car-Models-List", re.I)),
    ("car_nameplates", re.compile(r"^Car-Nameplates", re.I)),
    ("tuning", re.compile(r"^Tuning-Database", re.I)),
    ("light_bulbs", re.compile(r"^Light-Bulbs", re.I)),
    ("china", re.compile(r"^China-Car-Database", re.I)),
    ("japan", re.compile(r"^Japan-Car-Database", re.I)),
    ("europe", re.compile(r"^European-Car-Database", re.I)),
    ("uk", re.compile(r"^United-Kingdom-Car-Database", re.I)),
    ("spain", re.compile(r"^Spain-Car-Database", re.I)),
    ("india", re.compile(r"^India-Car-Database", re.I)),
]


def dataset_of(name: str) -> str | None:
    return next((d for d, p in DATASETS if p.search(name)), None)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


_CONTENT: dict[str, str] = {}


def content_sha(path: Path, sha: str) -> str:
    """Hash of every cell of every sheet: two downloads with different file bytes (metadata)
    but the same cells are one dataset."""
    if sha not in _CONTENT:
        digest = hashlib.sha256()
        for name in sheet_names(path):
            digest.update(name.encode("utf-8"))
            for row in sheet_rows(path, name):
                digest.update(json.dumps(row, default=str, ensure_ascii=False).encode("utf-8"))
        _CONTENT[sha] = digest.hexdigest()
    return _CONTENT[sha]


def inventory() -> list[dict]:
    """Every file in the Teoalida raw folder. The first file of a sha256 (or of identical cell
    content) is the one read; the others are recorded as duplicates."""
    seen, seen_content, out = {}, {}, []
    for path in sorted(TEO_RAW.iterdir(), key=lambda p: (len(p.name), p.name)):
        if not path.is_file():
            continue
        sha = sha256_file(path)
        row = {"file": path.name, "sha256": sha, "bytes": path.stat().st_size,
               "duplicate_of": seen.get(sha, ""), "dataset": dataset_of(path.name) or "", "note": ""}
        if row["duplicate_of"]:
            row["note"] = "same sha256"
        else:
            content = content_sha(path, sha)
            if content in seen_content:
                row["duplicate_of"], row["note"] = seen_content[content], "same cells, different file bytes"
            seen_content.setdefault(content, path.name)
        out.append(row)
        seen.setdefault(sha, path.name)
    return out


def unique_file(dataset: str) -> Path | None:
    """The single copy of a dataset to read (duplicates by sha256 skipped)."""
    for row in inventory():
        if row["dataset"] == dataset and not row["duplicate_of"]:
            return TEO_RAW / row["file"]
    return None


def _cells(row) -> list[str]:
    return [str(c).strip() if c is not None else "" for c in row]


CACHE = RAW_ROOT / "teoalida_cache"  # <sha256>.json.gz: every sheet's rows, written under uv
_BOOKS: dict[Path, dict] = {}


def _read_workbook(path: Path) -> dict:
    """{sheet: [rows]} with the spreadsheet libraries (run under uv with openpyxl and xlrd)."""
    if path.suffix.lower() == ".xls":
        import xlrd

        book = xlrd.open_workbook(path)
        return {sh.name: [[c.value if c.value != "" else None for c in sh.row(i)] for i in range(sh.nrows)]
                for sh in book.sheets()}
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    return {ws.title: [list(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}


def load_book(path: Path) -> dict:
    """The workbook's sheets, from the cache when it exists (no spreadsheet library needed)."""
    if path not in _BOOKS:
        sha = sha256_file(path)
        cached = CACHE / f"{sha}.json.gz"
        if cached.exists():
            with gzip.open(cached, "rt", encoding="utf-8") as handle:
                _BOOKS[path] = json.load(handle)["sheets"]
        else:
            sheets = json.loads(json.dumps(_read_workbook(path), default=str))
            CACHE.mkdir(parents=True, exist_ok=True)
            with gzip.open(cached, "wt", encoding="utf-8") as handle:
                json.dump({"file": path.name, "sha256": sha, "sheets": sheets}, handle, ensure_ascii=False)
            _BOOKS[path] = sheets
    return _BOOKS[path]


def sheet_rows(path: Path, sheet: str) -> list[tuple]:
    return [tuple(r) for r in load_book(path)[sheet]]


def sheet_names(path: Path) -> list[str]:
    return list(load_book(path))


def read_table(path: Path, sheet: str, required: list[str], valid=None) -> tuple[int, list[str], list[dict]]:
    """(header row number, column names, data rows). The header is the first row holding every
    `required` name. Repeated column names get "#2", "#3". A data row needs every required
    column filled; `valid(row)` drops service rows (counters, notices) below the header.
    Each row keeps its 1-based sheet row number in "_row"."""
    rows = sheet_rows(path, sheet)
    head_i = next((i for i, r in enumerate(rows) if r and all(k in _cells(r) for k in required)), None)
    if head_i is None:
        raise ValueError(f"{path.name}/{sheet}: header with {required} not found")
    head, counts = [], {}
    for name in _cells(rows[head_i]):
        counts[name] = counts.get(name, 0) + 1
        head.append(name if counts[name] == 1 else f"{name}#{counts[name]}")
    out = []
    for i, r in enumerate(rows[head_i + 1:], start=head_i + 2):
        d = {k: v for k, v in zip(head, r) if k}
        if any(d.get(k) in (None, "") for k in required):
            continue
        if valid is not None and not valid(d):
            continue
        d["_row"] = i
        out.append(d)
    return head_i + 1, head, out


def row_text(row: dict, columns: list[str]) -> str:
    """The row as cited text: "Column: value | Column: value" (the quote of every fact)."""
    return " | ".join(f"{c}: {row[c]}" for c in columns if row.get(c) not in (None, ""))


def write_pagetext(path: Path, sheet: str, required: list[str]) -> str:
    """Page text of one sheet for citations and the recheck: page N = sheet row N, written as
    "Column: value | …" in column order (rows above the header as their plain cells). Stored
    under the workbook's sha256 like the PDF page cache. Returns the sha256."""
    sha = sha256_file(path)
    rows = sheet_rows(path, sheet)
    head_row, head, _ = read_table(path, sheet, required)
    pages = []
    for i, r in enumerate(rows, start=1):
        if i <= head_row:
            pages.append(" | ".join(c for c in _cells(r) if c))
        else:
            pages.append(row_text(dict(zip(head, r)), [h for h in head if h]))
    target = RAW_ROOT / "pagetext" / f"{sha}.json.gz"
    with gzip.open(target, "wt", encoding="utf-8") as handle:
        json.dump({"sha256": sha, "file": path.name, "sheet": sheet, "pages": pages}, handle, ensure_ascii=False)
    return sha


def row_quote(row: dict, head: list[str], columns: list[str]) -> str:
    """The cited part of a row: every filled column from the first to the last of `columns` in
    sheet order, so the quote is a contiguous piece of the row's page text."""
    named = [h for h in head if h]
    idx = [named.index(c) for c in columns if c in named]
    return row_text(row, named[min(idx):max(idx) + 1])


def write_doc(make: str, dataset: str, key: str, lines: list[str], years: list[int], facts: list[dict],
              path: Path, sha: str, title: str, publisher: str, retrieved_at: str) -> Path:
    """A Teoalida document in the make's extracted folder, read by build_manual_facts.py like an
    owner's-manual extraction: tier B, SECONDARY_SPEC_DATABASE, registry teoalida."""
    doc = {
        "doc": {"key": key, "make": make, "lines": lines, "years": sorted(set(years)),
                "doc_type": "teoalida_specifications", "title": title, "path": str(path),
                "url": "", "page_url": "", "sha256": sha, "retrieved_at": retrieved_at,
                "tier": "B", "source_type": "SECONDARY_SPEC_DATABASE", "publisher": publisher,
                "authenticity": "SECONDARY", "registry": "teoalida", "edition": "US", "dataset": dataset},
        "extractor": f"teoalida-{dataset}-1", "pages": 1, "edition_market": "US", "status": "ok",
        "facts": facts, "review": [], "engine_codes": [],
    }
    target = WORK / make / "extracted" / f"{key}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return target


def clear_docs(dataset: str) -> int:
    """Remove the previous extraction of a dataset (every make) before writing it again."""
    n = 0
    for p in WORK.glob(f"*/extracted/teoalida-{dataset}-*.json"):
        p.unlink()
        n += 1
    return n


def write_manifest(rows: list[dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in FIELDS})


def read_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def descriptor(row: dict) -> bytes:
    """What raw_documents stores for a Teoalida file: the workbook stays in the raw store
    (C:\\AutoExpertData\\raw\\teoalida); the stored document names it by sha256 with its sheets."""
    path = TEO_RAW / row["file"]
    sheets = {}
    for name in sheet_names(path):
        sheets[name] = len(sheet_rows(path, name))
    return json.dumps({"file": row["file"], "sha256": row["sha256"], "bytes": row["bytes"],
                       "dataset": row["dataset"], "raw": f"rawstore:teoalida/{row['file']}",
                       "sheets": sheets}, ensure_ascii=False, indent=1).encode("utf-8")


if __name__ == "__main__":
    for r in inventory():
        print(r["dataset"] or "?", r["file"], r["sha256"][:12], "DUP of " + r["duplicate_of"] if r["duplicate_of"] else "")

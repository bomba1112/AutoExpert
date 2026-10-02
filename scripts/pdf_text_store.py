"""Per-page text of every downloaded PDF under RAW_ROOT, for parsing and quote validation.

For each PDF (RAW_ROOT/manuals/**, RAW_ROOT/official/**, RAW_ROOT/owner_supplied/**) writes
RAW_ROOT/pagetext/<sha256>.json.gz = {"sha256", "file", "pages": [...], "layout": [...]}:
  pages   pypdfium2 text per page (reading order, used for quotes)
  layout  pdftotext -layout text per page (column positions kept, used for tables)
Files already cached under the same sha256 are skipped. Pages without a text layer are
listed in "empty_pages" (candidates for OCR).

  uv run --no-project --with pypdfium2 python scripts/pdf_text_store.py [subdir ...]
"""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pypdfium2 as pdfium

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT  # noqa: E402

OUT = RAW_ROOT / "pagetext"
PDFTOTEXT = shutil.which("pdftotext")


def layout_pages(path: Path) -> list[str]:
    if not PDFTOTEXT:
        return []
    result = subprocess.run(
        [PDFTOTEXT, "-layout", "-enc", "UTF-8", str(path), "-"],
        capture_output=True,
        timeout=600,
    )
    if result.returncode != 0:
        return []
    return result.stdout.decode("utf-8", errors="replace").split("\f")


def cache(path: Path) -> str | None:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    target = OUT / f"{digest}.json.gz"
    if target.exists():
        return None
    try:
        pdf = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as exc:
        return f"{path.name}: unreadable ({exc})"
    pages = []
    for index in range(len(pdf)):
        page = pdf[index]
        pages.append(page.get_textpage().get_text_range())
        page.close()
    layout = layout_pages(path)
    record = {
        "sha256": digest,
        "file": path.relative_to(RAW_ROOT).as_posix(),
        "pages": pages,
        "layout": layout[: len(pages)] if layout else [],
        "empty_pages": [i + 1 for i, text in enumerate(pages) if len(text.strip()) < 20],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(target, "wt", encoding="utf-8") as handle:
        json.dump(record, handle)
    return f"{path.name}: {len(pages)} pages, {len(record['empty_pages'])} empty"


def main(argv) -> int:
    subdirs = argv or ["manuals", "official", "owner_supplied"]
    for sub in subdirs:
        for path in sorted((RAW_ROOT / sub).rglob("*.pdf")):
            message = cache(path)
            if message:
                print(message, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

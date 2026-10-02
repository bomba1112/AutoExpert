"""Inspect cached manual page text (RAW_ROOT/pagetext) while writing extractors.

  .venv/Scripts/python.exe scripts/manual_pages.py <file-substring> <regex> [--layout] [--max N]

Prints the pages of the first cached PDF whose path contains <file-substring> and whose text
matches <regex> (case-insensitive). Nothing is written.
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT  # noqa: E402


def records():
    for path in sorted((RAW_ROOT / "pagetext").glob("*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            yield json.load(handle)


def main(argv) -> int:
    needle, pattern = argv[0], re.compile(argv[1], re.I)
    layout = "--layout" in argv
    limit = int(argv[argv.index("--max") + 1]) if "--max" in argv else 3
    for rec in records():
        if needle.lower() not in rec["file"].lower():
            continue
        texts = rec["layout"] if layout and rec.get("layout") else rec["pages"]
        shown = 0
        for number, text in enumerate(texts, 1):
            if pattern.search(text):
                print(f"===== {rec['file']} page {number} =====")
                print(text[:4000])
                shown += 1
                if shown >= limit:
                    break
        return 0
    print("no cached file matches", needle)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

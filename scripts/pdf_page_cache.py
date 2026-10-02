"""Cache per-page text of every downloaded PDF for quote validation.

Writes data_work/<make>/raw/pagetext/<pdf stem>.json = {"sha256": ..., "pages": [text, ...]}
(git-ignored, because it is copied document text). Already cached files with the same
sha256 are skipped.

  uv run --no-project --with pypdfium2 python scripts/pdf_page_cache.py toyota
"""

import hashlib
import json
import sys
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]


def main(make):
    raw = ROOT / "data_work" / make / "raw"
    out = raw / "pagetext"
    out.mkdir(parents=True, exist_ok=True)
    for path in sorted(list(raw.glob("manuals/*.pdf")) + list(raw.glob("product_info/*.pdf"))):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        target = out / f"{path.stem}.json"
        if target.exists() and json.loads(target.read_text(encoding="utf-8"))["sha256"] == digest:
            continue
        pdf = pdfium.PdfDocument(str(path))
        pages = []
        for index in range(len(pdf)):
            page = pdf[index]
            pages.append(page.get_textpage().get_text_range())
            page.close()
        target.write_text(json.dumps({"sha256": digest, "pages": pages}), encoding="utf-8")
        print(path.name, len(pages))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "toyota")

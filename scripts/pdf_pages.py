"""Find and render owner-manual pages for visual verification of extracted numbers.

Runs with an ephemeral pypdfium2 (does not change the project environment):
  uv run --with pypdfium2 python scripts/pdf_pages.py find  <pdf> "<regex>"
  uv run --with pypdfium2 python scripts/pdf_pages.py text  <pdf> <page> [<page> ...]
  uv run --with pypdfium2 python scripts/pdf_pages.py render <pdf> <out_dir> <page> [...]
Pages are 1-based PDF page indices (not the printed page numbers).
"""

import re
import sys
from pathlib import Path

import pypdfium2 as pdfium


def page_text(pdf, index):
    page = pdf[index - 1]
    text = page.get_textpage().get_text_range()
    page.close()
    return text


def main(argv):
    command, path = argv[0], argv[1]
    pdf = pdfium.PdfDocument(path)
    if command == "find":
        pattern = re.compile(argv[2], re.I)
        for index in range(1, len(pdf) + 1):
            text = page_text(pdf, index)
            if pattern.search(text):
                first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
                print(index, "|", first[:80])
    elif command == "text":
        for index in map(int, argv[2:]):
            print(f"===== page {index} =====")
            print(page_text(pdf, index))
    elif command == "render":
        out = Path(argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for index in map(int, argv[3:]):
            image = pdf[index - 1].render(scale=1.6).to_pil()
            target = out / f"{Path(path).stem}_p{index}.png"
            image.save(target)
            print(target)
    print(f"pages={len(pdf)}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])

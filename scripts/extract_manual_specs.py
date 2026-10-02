"""Locate the specification chapter of owner-manual PDFs and record the edition market.

For every PDF in data_work/<make>/raw/manuals/ this writes:
  raw/spec_text/<stem>.txt        text of the specification pages with page markers
                                  (copied manual text stays in git-ignored raw/)
  manual_editions.json            per file: pages, spec page range, edition markers,
                                  detected market (tracked; no manual text)

Run with an ephemeral pypdfium2:
  uv run --no-project --with pypdfium2 python scripts/extract_manual_specs.py toyota
"""

import hashlib
import json
import re
import sys
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
START = re.compile(r"Maintenance data \(fuel, oil level, etc\.\)")
END = re.compile(r"^\s*(Customizable features|Items to initialize|Customization)\s*$", re.M)


def texts(pdf):
    for index in range(len(pdf)):
        page = pdf[index]
        yield index + 1, page.get_textpage().get_text_range()
        page.close()


def edition(all_text):
    markers = {
        "usa_mentions": len(re.findall(r"U\.S\.A\.", all_text)),
        "canada_mentions": len(re.findall(r"\bCanada\b", all_text)),
        "us_quarts": len(re.findall(r"\bqt\.", all_text)),
        "mph": len(re.findall(r"\bmph\b", all_text)),
        "ilsac": len(re.findall(r"\bILSAC\b", all_text)),
        "acea": len(re.findall(r"\bACEA\b", all_text)),
        "fmvss": len(re.findall(r"\bFMVSS\b", all_text)),
        "octane_87": len(re.findall(r"\b87\b[^\n]{0,40}Octane", all_text)),
    }
    us = markers["usa_mentions"] > 0 and markers["us_quarts"] > 0 and markers["mph"] > 0
    if us and markers["acea"] == 0:
        market = "US"
    elif markers["acea"] and not markers["us_quarts"]:
        market = "EU"
    else:
        market = "UNKNOWN"
    return markers, market


def main(make):
    base = ROOT / "data_work" / make
    out_dir = base / "raw" / "spec_text"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for path in sorted((base / "raw" / "manuals").glob("*.pdf")):
        pdf = pdfium.PdfDocument(str(path))
        pages = dict(texts(pdf))
        start = next(
            (i for i, t in pages.items() if i > len(pages) * 0.6 and START.search(t)), None
        )
        end = None
        if start:
            end = next((i for i, t in pages.items() if i > start and END.search(t)), None)
            end = (end - 1) if end else min(start + 30, len(pages))
            chunk = "\n".join(
                f"\n===== PDF page {i} =====\n{pages[i]}" for i in range(start, end + 1)
            )
            (out_dir / f"{path.stem}.txt").write_text(chunk, encoding="utf-8")
        markers, market = edition("\n".join(pages.values()))
        summary[path.name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "pages": len(pages),
            "spec_pages": [start, end],
            "edition_markers": markers,
            "edition_market": market,
        }
        print(path.name, len(pages), [start, end], market)
    (base / "manual_editions.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "toyota")

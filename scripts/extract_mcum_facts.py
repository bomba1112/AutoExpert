"""Fluids and capacities from mycarusermanual.com pages (Appendix E), US editions only.

The site serves each manual section as absolutely positioned text blocks (PDF rendered to
HTML: <div style="left:..em;top:..em">), not as HTML tables. The blocks are turned into
positioned "words" and run through the same row geometry and field rules as the PDF parser
(scripts/extract_manual_facts.py), so a label and its value are paired by the row they sit on.

Only generations classified US by scripts/classify_mcum.py are used. Values apply to the
generation's year range on the site; build_manual_facts.py lets a year-specific manual win
over them when they disagree (Appendix E.6).

Output: data_work/<make>/extracted/mcum-<model>-<body>-<years>.json (same format as the PDF
extractions; "pages" are the crawled sections in manifest order).

  .venv/Scripts/python.exe scripts/extract_mcum_facts.py
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import html as htmlmod
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_manual_facts import (  # noqa: E402
    EXTRACTOR,
    PageState,
    engine_codes,
    extract_page,
    group_rows,
    merge_values,
    norm,
    render,
    split_columns,
)
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import LINES, MAKES  # noqa: E402

EM_TO_PT = 12.0  # the row/column thresholds of the PDF parser are in points
CHAR_EM = 0.5
BLOCK = re.compile(r'<div class="stl_01" style="left:([\d.]+)em;top:([\d.]+)em;">(.*?)</div>', re.S)
PRIORITY = re.compile(r"specification|lubric|capacit|maintenance-data|fuel|fluid|engine-oil|oil", re.I)


PAGE_SPLIT = re.compile(r'<div class="stl_03">')


def pages_of(raw_html: str) -> list[tuple[list[dict], str]]:
    """One section holds several manual pages, each in its own container whose blocks
    restart at the top; they are parsed one page at a time."""
    parts = PAGE_SPLIT.split(raw_html)
    return [words_of(part) for part in (parts[1:] if len(parts) > 1 else parts)]


def words_of(raw_html: str) -> tuple[list[dict], str]:
    words, chunks = [], []
    for left, top, inner in BLOCK.findall(raw_html):
        text = norm(htmlmod.unescape(re.sub(r"<[^>]+>", "", inner)))
        if not text:
            continue
        x0, y0 = float(left) * EM_TO_PT, float(top) * EM_TO_PT
        words.append({"text": text, "x0": x0, "x1": x0 + len(text) * CHAR_EM * EM_TO_PT,
                      "top": y0, "bottom": y0 + EM_TO_PT})
        chunks.append(text)
    return words, " ".join(chunks)


def rows_of_words(words: list[dict]) -> list[list[dict]]:
    width = max((w["x1"] for w in words), default=600.0)
    return [merge_values([render(r) for r in group_rows(col)]) for col in split_columns(width, words) if col]


def main() -> int:
    markets = json.loads((WORK / "_mcum" / "edition_markets.json").read_text(encoding="utf-8"))
    with (WORK / "_mcum" / "manifest.csv").open(encoding="utf-8", newline="") as handle:
        manifest = [r for r in csv.DictReader(handle) if r["http_status"] == "200" and r["body"]]
    by_gen = defaultdict(list)
    for row in manifest:
        by_gen[(row["make"], row["model"], row["body"], row["years"])].append(row)
    slug_to_make = {v["mcum"]: k for k, v in MAKES.items() if v.get("mcum")}
    for (site_make, model, body, years), rows in sorted(by_gen.items()):
        info = markets.get(f"{site_make}/{model}/{body}/{years}", {})
        if info.get("market") != "US":
            continue
        make = slug_to_make.get(site_make)
        lines = [ln.key for ln in LINES if ln.make == make and model in ln.mcum]
        if not make or not lines:
            continue
        first, last = (int(x) for x in (years.split("-") + [years])[:2])
        folder = RAW_ROOT / "_mcum" / site_make / model / f"{body}_{years}"
        pages, sections, urls, digests = [], [], [], []
        result_facts, review = [], []
        state = PageState()
        for row in sorted(rows, key=lambda r: r["section"]):
            name = row["section"] or "_index"
            path = folder / f"{name}.html.gz"
            if not path.exists():
                path = folder / f"{name}.html"
            if not path.exists():
                continue
            raw = gzip.decompress(path.read_bytes()).decode("utf-8") if path.suffix == ".gz" else path.read_text(encoding="utf-8")
            digests.append(row["sha256"])
            for words, text in pages_of(raw):
                pages.append(text)
                sections.append(name)
                urls.append(row["url"])
                if not PRIORITY.search(name) or not words:
                    continue
                facts, rev = extract_page(len(pages), rows_of_words(words), text, state)
                for fact in facts:
                    fact["section_url"] = row["url"]
                result_facts += facts
                review += rev
        key = f"mcum-{model}-{body}-{years}"
        sha = hashlib.sha256("".join(digests).encode()).hexdigest()
        store = RAW_ROOT / "pagetext" / f"{sha}.json.gz"
        with gzip.open(store, "wt", encoding="utf-8") as handle:  # page texts for quote checks
            json.dump({"sha256": sha, "file": f"_mcum/{site_make}/{model}/{body}_{years}", "pages": pages,
                       "sections": sections, "urls": urls}, handle)
        doc = {
            "key": key, "make": make, "lines": lines,
            "years": [y for y in range(first, last + 1) if 2014 <= y <= 2026],
            "doc_type": "owners_manual", "title": f"{site_make} {model} {body} {years} owner's manual (mycarusermanual.com copy)",
            "path": str(folder), "url": urls[0] if urls else "", "page_url": "", "sha256": sha,
            "retrieved_at": rows[0]["retrieved_at"], "tier": "B", "source_type": "OWNER_MANUAL_COPY",
            "publisher": "factory owner's manual, copy hosted by mycarusermanual.com",
            "authenticity": "REVIEWED_MIRROR", "generation_range": True,
        }
        out = {"doc": doc, "extractor": EXTRACTOR + "+mcum", "pages": len(pages), "edition_market": "US",
               "edition_markers": info.get("markers"), "facts": result_facts, "review": review,
               "engine_codes": engine_codes(pages), "status": "ok"}
        target = WORK / make / "extracted" / f"{key}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(key, lines, doc["years"], len(result_facts), "facts", len(review), "review", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

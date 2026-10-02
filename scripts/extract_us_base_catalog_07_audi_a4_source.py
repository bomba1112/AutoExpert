"""Inspect exact Audi A4 technical source pages without touching the live DB."""

from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EXTRACTS = ROOT / ".localdata/us-base-catalog-07-source-extracts"
KEYS = ("technical specifications", "190 hp", "252 hp", "a4 (8w)", "a4 2.0 (190 hp)",
        "a4 2.0 (252 hp)", "2.0t ultra fwd", "engine code", "7-speed s tronic", "a4 2.0t")


def main() -> None:
    EXTRACTS.mkdir(parents=True, exist_ok=True)
    rows = json.loads((WORK / "acquisition-audi-a4.json").read_text(encoding="utf-8"))
    for row in rows:
        path = ROOT / row["path"]
        if row["media_type"] == "application/pdf":
            reader = PdfReader(path)
            pages = []
            hits = []
            for i, page in enumerate(reader.pages, start=1):
                try:
                    value = page.extract_text() or ""
                except (ZeroDivisionError, ValueError):
                    value = ""
                pages.append(value)
                if any(key in value.lower() for key in KEYS):
                    hits.append({"page": i, "preview": re.sub(r"\s+", " ", value)[:500]})
            (EXTRACTS / (row["name"] + ".json")).write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
            print(json.dumps({"name": row["name"], "pages": len(pages), "hits": hits[:12]}))
        else:
            soup = BeautifulSoup(path.read_bytes(), "html.parser")
            for el in soup.select("script, style, nav, footer, header"):
                el.decompose()
            value = soup.get_text(" ", strip=True)
            (EXTRACTS / (row["name"] + ".txt")).write_text(value, encoding="utf-8")
            positions = {key: value.lower().find(key) for key in ("a4 sedan", "a4 quattro manual", "six-speed manual", "252 hp")}
            print(json.dumps({"name": row["name"], "text_chars": len(value), "positions": positions}))


if __name__ == "__main__":
    main()

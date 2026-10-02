"""Extract archived Audi Q7 US brochure pages for source review."""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
OUT = ROOT / ".localdata/us-base-catalog-07-source-extracts"


def main() -> None:
    receipts = json.loads((WORK / "acquisition-audi-q7.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for receipt in receipts:
        pages = [page.extract_text(extraction_mode="layout") or "" for page in PdfReader(ROOT / receipt["path"]).pages]
        (OUT / f'{receipt["name"]}.json').write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"name": receipt["name"], "pages": len(pages), "chars": sum(map(len, pages))}))


if __name__ == "__main__":
    main()

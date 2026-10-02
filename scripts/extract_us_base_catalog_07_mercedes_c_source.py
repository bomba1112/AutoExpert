"""Extract privately cached official Mercedes C-Class brochure pages once."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".localdata/us-base-catalog-07-source-extracts"
RECEIPT = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work/acquisition-mercedes-c.json"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = []
    for row in json.loads(RECEIPT.read_text(encoding="utf-8")):
        if row["media_type"] != "application/pdf":
            continue
        start = time.perf_counter()
        path = OUT / f'{row["name"]}.json'
        pages = [page.extract_text() or "" for page in PdfReader(ROOT / row["path"]).pages]
        path.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
        summary.append({"name": row["name"], "pages": len(pages), "seconds": round(time.perf_counter() - start, 3)})
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Extract privately cached official BMW X1 technical-sheet pages once."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".localdata/us-base-catalog-07-source-extracts"
RECEIPT = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work/acquisition-bmw-x1.json"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = []
    for row in json.loads(RECEIPT.read_text(encoding="utf-8")):
        if row["media_type"] != "application/pdf":
            continue
        pages = [page.extract_text() or "" for page in PdfReader(ROOT / row["path"]).pages]
        (OUT / f'{row["name"]}.json').write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
        summary.append({"name": row["name"], "pages": len(pages)})
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

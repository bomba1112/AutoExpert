"""Extract every page once from independently acquired batch-07 PDFs."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".localdata/us-base-catalog-07-source-extracts"
RECEIPTS = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work/acquisition-receipts.json"


def main() -> None:
    PRIVATE.mkdir(parents=True, exist_ok=True)
    receipts = json.loads(RECEIPTS.read_text(encoding="utf-8"))
    summary = []
    for receipt in receipts:
        start = time.perf_counter()
        if receipt["media_type"] == "application/pdf":
            reader = PdfReader(ROOT / receipt["path"])
            pages = [page.extract_text() or "" for page in reader.pages]
        else:
            pages = [(ROOT / receipt["path"]).read_text(encoding="utf-8")]
        (PRIVATE / (receipt["name"] + ".json")).write_text(
            json.dumps(pages, ensure_ascii=False), encoding="utf-8"
        )
        summary.append(
            {
                "name": receipt["name"],
                "source_sha256": receipt["sha256"],
                "pages": len(pages),
                "seconds": round(time.perf_counter() - start, 3),
            }
        )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()

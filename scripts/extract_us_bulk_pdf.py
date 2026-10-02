"""Index selected source-backed PDF pages once per content hash and parser version."""

import argparse
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
VERSION = "pdfium-technical-page-index-1"
TOKENS = (
    "specifications",
    "technical specifications",
    "mechanical",
    "engine",
    "transmission",
    "drivetrain",
    "seating",
    "passenger",
    "wheelbase",
    "fuel tank",
    "dimensions",
    "tire",
    "suspension",
    "brake",
    "oil",
    "fluid",
    "capacity",
    "maintenance",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", default="us-bulk-data-08")
    args = parser.parse_args()
    out = ROOT / "deliverables/VerifiedData" / args.batch
    discovered = json.loads((out / "factory-source-discovery.json").read_text(encoding="utf-8"))
    ledger = json.loads(
        (ROOT / "deliverables/VerifiedData/base-catalog-acquisition.json").read_text(
            encoding="utf-8"
        )
    )
    receipts = {
        r["url"]: r
        for r in ledger
        if r.get("http_status") == 200 and r.get("sha256") and not r.get("error")
    }
    cache = ROOT / ".localdata/bulk08/pdf-pages"
    cache.mkdir(parents=True, exist_ok=True)
    rows, metrics = (
        [],
        {
            "documents": 0,
            "pages": 0,
            "page_candidates": 0,
            "cold_parses": 0,
            "cache_hits": 0,
            "quarantined": 0,
        },
    )
    started = time.perf_counter()
    for item in discovered["documents"]:
        receipt = receipts.get(item["url"])
        if not receipt:
            rows.append({**item, "status": "SOURCE_NOT_ACQUIRED"})
            metrics["quarantined"] += 1
            continue
        digest = receipt["sha256"]
        key = hashlib.sha256((digest + ":" + VERSION).encode()).hexdigest()
        destination = cache / (key + ".json")
        if destination.exists():
            pages = json.loads(destination.read_text(encoding="utf-8"))
            metrics["cache_hits"] += 1
        else:
            source = ROOT / ".localdata/verified-source-documents" / digest
            raw = source.read_bytes()
            if hashlib.sha256(raw).hexdigest() != digest or not raw.startswith(b"%PDF-"):
                rows.append({**item, "status": "SOURCE_HASH_OR_TYPE_MISMATCH", "sha256": digest})
                metrics["quarantined"] += 1
                continue
            pdf = pdfium.PdfDocument(raw)
            pages = []
            for page in pdf:
                textpage = page.get_textpage()
                pages.append(textpage.get_text_range())
                textpage.close()
                page.close()
            pdf.close()
            destination.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
            metrics["cold_parses"] += 1
        selected = []
        for number, text in enumerate(pages, start=1):
            compact = " ".join(text.split())
            found = [
                token
                for token in TOKENS
                if re.search(r"\b" + re.escape(token) + r"\b", compact, re.I)
            ]
            if len(found) >= 3:
                selected.append(
                    {
                        "page": number,
                        "signals": found,
                        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    }
                )
        row = {
            "make": item["make"],
            "model": item["model"],
            "model_year_candidate": item["year"],
            "source_url": item["url"],
            "source_sha256": digest,
            "parser_version": VERSION,
            "pages": len(pages),
            "page_candidates": selected,
            "extracted_sections": ["PAGE_TEXT", "TECHNICAL_PAGE_SIGNALS"],
            "unprocessed_sections": ["ROW_COLUMN_APPLICABILITY", "CONDITIONAL_NOTES"],
            "status": "EXTRACTED_NOT_VALIDATED",
        }
        rows.append(row)
        metrics["documents"] += 1
        metrics["pages"] += len(pages)
        metrics["page_candidates"] += len(selected)
    meaningful = [{k: v for k, v in row.items() if k not in {"status"}} for row in rows]
    result = {
        "batch_id": args.batch,
        "observed_at": datetime.now(UTC).isoformat(),
        "parser_version": VERSION,
        "metrics": metrics,
        "semantic_sha256": hashlib.sha256(
            json.dumps(meaningful, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "documents": rows,
        "published_facts": 0,
    }
    (out / "factory-pdf-extraction-index.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: result[k] for k in ("metrics", "semantic_sha256", "elapsed_seconds")},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

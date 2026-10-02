"""Screen every cached exception-group source for drive terminology, no promotion.

Only counts and page locators are saved. A token hit never proves exact trim,
engine or gearbox applicability; the reviewed claim manifests remain necessary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sqlite3
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-02/review-groups.jsonl"
OUT = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-03/drive-candidate-audit.json"
TERMS = {
    "FWD": re.compile(
        r"front[-‐ ]wheel drive|front engine[,/ ]+front[-‐ ]?(?:wheel )?drive|\bFWD\b", re.I
    ),
    "RWD": re.compile(r"rear[-‐ ]wheel drive|\bRWD\b", re.I),
    "AWD": re.compile(r"all[-‐ ]wheel drive|\bAWD\b|\bquattro\b|\bxDrive\b", re.I),
    "4WD": re.compile(r"four[-‐ ]wheel drive|\b4WD\b|\b4x4\b", re.I),
    "2WD": re.compile(r"two[-‐ ]wheel drive|\b2WD\b|\b4x2\b", re.I),
}
logging.getLogger("pypdf").setLevel(logging.CRITICAL)


def source_text(path: Path) -> list[tuple[int, str]]:
    data = path.read_bytes()
    if data.startswith(b"%PDF"):
        pdf = PdfReader(str(path), strict=False)
        return [(number, page.extract_text() or "") for number, page in enumerate(pdf.pages, 1)]
    return [
        (0, BeautifulSoup(data.decode("utf-8", "replace"), "html.parser").get_text(" ", strip=True))
    ]


def run(db_path: Path = ROOT / "autoexpert.db", out: Path = OUT) -> dict:
    groups = [json.loads(s) for s in REVIEW.read_text(encoding="utf-8").splitlines() if s]
    db = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    cache = {}
    results = []
    for i, group in enumerate(groups, 1):
        specs = db.execute(
            "SELECT specifications FROM vehicle_variants WHERE catalog_key=?",
            (group["catalog_keys"][0],),
        ).fetchone()
        if specs is None:
            raise ValueError("REVIEW_VARIANT_MISSING")
        catalog = json.loads(specs[0])["catalog"]
        ref = (catalog.get("facts", {}).get("transmission_description") or {}).get(
            "documentary_source"
        ) or {}
        sha = ref.get("sha256")
        path = ROOT / ".localdata/raw" / str(sha)
        status = "SOURCE_MISSING"
        counts = {}
        pages = {}
        if sha and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == sha:
            if sha not in cache:
                try:
                    content = source_text(path)
                    cache[sha] = {
                        name: [p for p, text in content if pattern.search(text)]
                        for name, pattern in TERMS.items()
                    }
                except Exception as exc:
                    cache[sha] = {"error": type(exc).__name__}
            entry = cache[sha]
            if "error" in entry:
                status = "EXTRACTION_FAILED"
            else:
                status = "SCANNED"
                counts = {name: len(locations) for name, locations in entry.items()}
                pages = {name: locations for name, locations in entry.items() if locations}
        results.append(
            {
                "group_id": f"G{i:03d}",
                "make": group["make"],
                "model": group["model"],
                "model_year": group["model_year"],
                "row_count": group["count"],
                "source_url": ref.get("url"),
                "sha256": sha,
                "status": status,
                "term_page_counts": counts,
                "term_pages": pages,
                "exact_applicability_reviewed": False,
            }
        )
    report = {
        "groups": len(results),
        "documents_scanned": len(cache),
        "scan_status": dict(Counter(x["status"] for x in results)),
        "groups_with_any_drive_term": sum(bool(x["term_pages"]) for x in results),
        "warning": "Drive term presence is a triage hint, never a commercial fact assertion.",
        "items": results,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {k: v for k, v in report.items() if k != "items"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(run(args.db, args.out), ensure_ascii=False, indent=2))

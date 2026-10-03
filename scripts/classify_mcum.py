"""Edition market of every mycarusermanual.com generation crawled (Appendix E.5) and the
library of other-market materials (Appendix D).

The market is decided per generation from all its crawled pages (text files next to the
gzip HTML in RAW_ROOT/_mcum) using the markers of Appendix D:
  US       U.S. references, miles/quarts/gallons, API/ILSAC, no ACEA-only grades
  CA       Canada-only wording with metric units
  GCC      Middle East / Gulf wording dominates
  EU       ACEA grades without API/ILSAC, litres/km only, E-mark wording
  GENERAL  several regions in one edition (e.g. Middle East and US paragraphs, diesel
           engines never sold in the US next to US grades)
  UNKNOWN  not enough text
Output:
  data_work/_mcum/edition_markets.json          per generation: market, markers, pages
  data_work/_library/manifest.csv               non-US generations (one row per generation)
  data_work/_mcum/manifest.csv                  edition_market column filled for crawled rows

  .venv/Scripts/python.exe scripts/classify_mcum.py [--keep-manifest]
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

MARKERS = {
    "us_refs": r"U\.S\.A\.|United States|\bU\.S\.\b|U\.S\. only|in the U\.S\.",
    "miles": r"\bmiles\b|\bmph\b",
    "quarts_gallons": r"\bqt\b|\bqts?\.|quarts?|\bgal\b|gallons?",
    "api_ilsac": r"\bAPI\b|ILSAC",
    "acea": r"\bACEA\b",
    "middle_east": r"Middle East|GCC|Gulf",
    "canada": r"Canada only|for Canada|Canadian",
    "europe": r"\bE\.C\b|EU countries|Europe(?:an)?\b",
    "diesel": r"\bdiesel\b|\bCRDi\b|\bTDI\b|\bdCi\b|\bTCI\b",
    "right_hand": r"right[- ]hand drive|RHD",
    "korea": r"Korea",
    "china": r"China|Chinese",
    # owner decision 2026-10-03: an edition for North America with the US NHTSA defect-reporting
    # text is a US edition (Tesla prints no quarts or gallons)
    "north_america": r"North America",
    "us_defect_reporting": r"Reporting Safety Defects[^.]{0,600}?(?:NHTSA|National Highway Traffic Safety Administration)",
}
# trademark notices ("... registered in the U.S. and other countries", Apple CarPlay) name the
# United States without saying anything about the edition: they are not US references
TRADEMARK = re.compile(r"(?:registered |trademarks? )?[^.]{0,80}?\bin the (?:U\.S\.|United States)(?:\s+and(?:/or)?\s+other countries)", re.I)


def classify(counts: dict) -> str:
    """Appendix D markers. Miles together with quarts/gallons mark the North American (US)
    edition even when it also carries Canada notes or, for VW/Mercedes, ACEA-style factory
    oil standards instead of API; CA needs Canada wording without US units."""
    if sum(counts.values()) == 0:
        return "UNKNOWN"
    if counts.get("north_america") and counts.get("us_defect_reporting") and not (counts["acea"] and not counts["api_ilsac"]):
        return "US"
    # a right-hand-drive edition that never refers to the United States (once trademark notices
    # are set aside) is not the US edition, whatever units it prints in brackets ("1,000 km (620
    # miles)"): Mitsubishi Outlander 2020 PHEV, a European edition
    if counts.get("right_hand", 0) >= 20 and counts.get("us_refs", 0) == 0:
        return "EU" if counts.get("europe", 0) >= 5 else "UNKNOWN"
    us_units = counts["miles"] >= 10 and counts["quarts_gallons"] >= 2
    if counts["middle_east"] >= 3 and (counts["us_refs"] >= 3 or counts["europe"] >= 5 or us_units):
        return "GENERAL"
    if counts["middle_east"] >= 3:
        return "GCC"
    if us_units and counts["us_refs"] >= 5:
        return "US"
    if counts["acea"] and not counts["api_ilsac"]:
        return "EU"
    if counts["diesel"] >= 5 and not us_units:
        return "EU"
    if us_units and counts["diesel"] < 5 and (counts["api_ilsac"] or counts["us_refs"] >= 2 or counts["quarts_gallons"] >= 5):
        return "US"
    if counts["canada"] >= 3 and counts["miles"] < 10:
        return "CA"
    if counts["europe"] >= 5:
        return "EU"
    return "UNKNOWN"


def main() -> int:
    manifest_path = WORK / "_mcum" / "manifest.csv"
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0].keys())
    gens = defaultdict(list)
    for row in rows:
        if row["body"] and row["http_status"] == "200":
            gens[(row["make"], row["model"], row["body"], row["years"])].append(row)
    result = {}
    for (make, model, body, years), pages in sorted(gens.items()):
        folder = RAW_ROOT / "_mcum" / make / model / f"{body}_{years}"
        counts = defaultdict(int)
        text_files = list(folder.glob("*.txt"))
        for path in text_files:
            text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8", errors="ignore"))
            for name, pattern in MARKERS.items():
                source = TRADEMARK.sub(" ", text) if name == "us_refs" else text
                counts[name] += len(re.findall(pattern, source))
        market = classify(counts)
        result[f"{make}/{model}/{body}/{years}"] = {"market": market, "markers": dict(counts), "pages": len(pages),
                                                    "folder": folder.relative_to(RAW_ROOT).as_posix()}
        for row in pages:
            row["edition_market"] = market
    (WORK / "_mcum" / "edition_markets.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    if "--keep-manifest" not in sys.argv:  # the crawler appends to it; rewrite only when no crawl runs
        with manifest_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    library = WORK / "_library" / "manifest.csv"
    library.parent.mkdir(parents=True, exist_ok=True)
    lib_fields = ["make", "model", "generation_or_years", "market", "market_markers", "source_url", "path",
                  "sha256", "retrieved_at", "pages"]
    existing = []
    if library.exists():
        with library.open(encoding="utf-8", newline="") as handle:
            existing = [r for r in csv.DictReader(handle) if "mycarusermanual" not in r.get("source_url", "")]
    out = list(existing)
    for key, info in result.items():
        if info["market"] in ("US", "UNKNOWN"):
            continue
        make, model, body, years = key.split("/")
        index = next((r for r in gens[(make, model, body, years)] if r["section"] == "_index"), None)
        digest = hashlib.sha256("".join(sorted(r["sha256"] for r in gens[(make, model, body, years)])).encode()).hexdigest()
        out.append({"make": make, "model": model, "generation_or_years": f"{body} {years}", "market": info["market"],
                    "market_markers": json.dumps(info["markers"]), "source_url": index["url"] if index else "",
                    "path": "rawstore:" + info["folder"], "sha256": digest,
                    "retrieved_at": index["retrieved_at"] if index else datetime.now(UTC).isoformat(timespec="seconds"),
                    "pages": info["pages"]})
    with library.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=lib_fields)
        writer.writeheader()
        writer.writerows(out)
    summary = defaultdict(int)
    for info in result.values():
        summary[info["market"]] += 1
    print(dict(summary))
    for key, info in result.items():
        print(info["market"], key, info["pages"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

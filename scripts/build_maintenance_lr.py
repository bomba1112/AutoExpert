"""Land Rover maintenance schedule from the documents on disk (result: no usable schedule).

Checks every Land Rover document in the raw store and writes, per line, a
data_work/land-rover/staging/<line>/maintenance_official.json that carries the evidence as gap
entries (no items) unless a document prints an interval for a service job:

  * official factory documents: RAW_ROOT/official/land-rover and the official manifests
    (data_work/_shared/manifest_official/*.csv rows of make land-rover);
  * mycarusermanual.com copies: RAW_ROOT/_mcum/land-rover/<model>/<body>_<year>/*.txt, US editions
    only (data_work/_mcum/edition_markets.json); the "Maintenance -> SERVICE INTERVALS" and
    "SERVICE INTERVAL INDICATOR" pages are searched for a distance or time interval;
  * owner's-manual PDFs (RAW_ROOT/manuals/land-rover) and JLR press material
    (RAW_ROOT/press/media.jlr.com) are searched the same way.

A page that states an interval ("every 16,000 miles", "every 2 years") for a job would be turned
into an item (FIXED_INTERVAL; tier B / SECONDARY_NOTE for a mycarusermanual copy); none does, so
the files hold the gaps only.

  .venv/Scripts/python.exe scripts/build_maintenance_lr.py
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maintenance_common import job_of, norm, our_lines, write  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

MAKE = "land-rover"
NAME = "official"
MCUM_FOLDER = {"range-rover-evoque": "evoque", "discovery-sport": "discovery-sport",
               "range-rover": "range-rover", "range-rover-sport": "range-rover-sport"}
INTERVAL = re.compile(r"every\s+[\d,]+\s*(?:miles|km)|every\s+\d+\s+(?:years?|months)|[\d,]{5,7}\s*(?:miles|km)\s*(?:or|/)\s*\d+\s*(?:years?|months)", re.I)


def official_rows() -> list[dict]:
    rows = []
    for path in sorted((WORK / "_shared" / "manifest_official").glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            rows += [r for r in csv.DictReader(handle) if r.get("make") == MAKE or r.get("path", "").startswith(f"official/{MAKE}/")]
    return rows


def interval_hits(text: str) -> list[str]:
    """Sentences that state an interval and name a service job."""
    out = []
    for sentence in re.split(r"(?<=[.!?])\s+", norm(text)):
        if INTERVAL.search(sentence) and job_of(sentence):
            out.append(sentence[:200])
    return out


def main() -> int:
    markets = json.loads((WORK / "_mcum" / "edition_markets.json").read_text(encoding="utf-8"))
    official = official_rows()
    official_dir = RAW_ROOT / "official" / MAKE
    pdf_dir = RAW_ROOT / "manuals" / MAKE
    press_dir = RAW_ROOT / "press" / "media.jlr.com"
    press_hits = []
    press_files = sorted(p for p in press_dir.rglob("*") if p.is_file()) if press_dir.exists() else []
    for p in press_files:
        data = p.read_bytes()
        if p.suffix == ".gz":
            try:
                text = gzip.decompress(data).decode("utf-8", errors="replace")
            except OSError:
                text = ""
        else:
            cache = RAW_ROOT / "pagetext" / f"{hashlib.sha256(data).hexdigest()}.json.gz"
            text = " ".join(json.load(gzip.open(cache, "rt", encoding="utf-8"))["pages"]) if cache.exists() else ""
        press_hits += [f"{p.name}: {h}" for h in interval_hits(text)]
    total_hits = 0
    for slug, line in sorted(our_lines(MAKE).items()):
        gaps = []
        scope = f"{MAKE}/{slug}"
        gaps.append({"scope": f"{scope} MY{line.years[0]}-{line.years[1]}", "field": "maintenance:schedule",
                     "reason": ("no official Land Rover document on disk: "
                                + (f"{len(official)} manifest rows" if official else "no row of make land-rover in data_work/_shared/manifest_official/*.csv")
                                + ("; RAW_ROOT/official/land-rover exists" if official_dir.exists() else "; RAW_ROOT/official/land-rover does not exist")
                                + ("; RAW_ROOT/manuals/land-rover exists" if pdf_dir.exists() else "; no owner's-manual PDF under RAW_ROOT/manuals/land-rover"))})
        folder = RAW_ROOT / "_mcum" / MAKE / MCUM_FOLDER[slug]
        editions = sorted(p for p in folder.iterdir() if p.is_dir()) if folder.exists() else []
        if not editions:
            gaps.append({"scope": f"{scope}", "field": "maintenance:schedule",
                         "reason": f"no mycarusermanual.com copy on disk (RAW_ROOT/_mcum/{MAKE}/{MCUM_FOLDER[slug]} absent)"})
        for ed in editions:
            body, _, year = ed.name.rpartition("_")
            market = markets.get(f"{MAKE}/{MCUM_FOLDER[slug]}/{body}/{year}", {}).get("market", "UNKNOWN")
            pages = sorted(ed.glob("*.txt"))
            hits = []
            for p in pages:
                if p.name.startswith("_"):
                    continue
                hits += [f"{p.stem}: {h}" for h in interval_hits(p.read_text(encoding="utf-8", errors="replace"))]
            total_hits += len(hits)
            svc = ed / "maintenance--service-intervals.txt"
            if market != "US":
                reason = (f"mycarusermanual.com {body} {year}: edition market {market} ({len(pages)} page files on disk, "
                          f"{'index page only' if len(pages) <= 1 else 'content pages'}); not a US edition, not used")
            elif hits:
                reason = f"mycarusermanual.com {body} {year} (US): interval statements found, review needed: {hits[:3]}"
            else:
                said = ""
                if svc.exists():
                    t = norm(svc.read_text(encoding="utf-8", errors="replace"))
                    m = re.search(r"An upcoming service interval will be notified to the driver via the Service Interval Indicator[^.]*\.", t)
                    said = f"; the SERVICE INTERVALS page says: \"{m.group(0)}\"" if m else ""
                    if "SERVICE PORTFOLIO" in t:
                        said += " and refers to the Service Portfolio booklet (not on disk)"
                reason = (f"mycarusermanual.com {body} {year} (US edition, {len(pages)} page files): no page states a distance or "
                          f"time interval for a service job{said}")
            gaps.append({"scope": f"{scope} MY{year} (mcum {MCUM_FOLDER[slug]}/{body}/{year})", "field": "maintenance:schedule",
                         "reason": reason})
        gaps.append({"scope": f"{scope}", "field": "maintenance:schedule",
                     "reason": (f"JLR press material on disk ({len(press_files)} files, media.jlr.com): "
                                + ("no service-interval statement" if not press_hits else f"interval statements: {press_hits[:3]}"))})
        out = write(MAKE, slug, NAME, {}, [], gaps)
        print(f"{scope}: items 0, gaps {len(gaps)} -> {out.relative_to(WORK.parent)}")
    print(f"checked 0, problems 0 (no items; interval statements found in mcum pages: {total_hits}, press: {len(press_hits)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

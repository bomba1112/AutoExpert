"""Mercedes-Benz maintenance items from the official US owners page "Service & Maintenance"
(www.mbusa.com/en/owners/service-maintenance, section "Service Intervals": Service A / Service B).

The US operator's manuals and service/warranty booklets give no intervals (they refer to the
Maintenance Booklet and the ASSYST PLUS display), so this page is the only official US statement.
As published it (1) says "approximately" — kept and flagged; (2) names no model or model year —
the items are stored as SECONDARY_NOTE with that scope stated, for every non-electric line and
generation. The page's EV paragraph gives no interval: electric lines get a gap entry.

Parsed by script from the stored page; every item quotes the page text.
Output: data_work/mercedes-benz/staging/<line>/maintenance.json (format of build_maintenance.py).

  .venv/Scripts/python.exe scripts/build_maintenance_mb.py
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_maintenance import miles_to_km  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import lines_for  # noqa: E402

PAGE = RAW_ROOT / "official" / "mercedes-benz" / "mbusa_pages" / "service-maintenance.html.gz"
URL = "https://www.mbusa.com/en/owners/service-maintenance"
SERVICE = re.compile(
    r"What is Service (?P<s>[AB])\? (?P<first>With the first visit at approximately (?P<m1>[\d,]+) miles or (?P<y1>\d+) years?"
    r"(?P<after>[^–—-]*?))\s*[–—-]?\s*(?:and )?then approximately every (?P<m2>[\d,]+) miles or (?P<y2>\d+) years? after that\s*[–—-]\s*"
    r"Service (?P=s) includes: (?P<items>.*?) Reset maintenance counter"
)
JOBS = [  # (phrase on the page, job, action)
    (r"motor oil replacement", "engine_oil_and_filter", "REPLACE"),
    (r"Cabin dust/combination filter replacement", "cabin_air_filter", "REPLACE"),
    (r"Brake fluid exchange", "brake_fluid", "REPLACE"),
    (r"Brake component inspection", "brakes", "INSPECT"),
]
SCOPE = "general US owner information page; models and model years not stated"


def main() -> int:
    raw = gzip.decompress(PAGE.read_bytes())
    sha = hashlib.sha256(raw).hexdigest()
    text = " ".join(BeautifulSoup(raw.decode("utf-8", errors="replace"), "html.parser").get_text(" ", strip=True).split())
    with gzip.open(RAW_ROOT / "pagetext" / f"{sha}.json.gz", "wt", encoding="utf-8") as handle:
        json.dump({"sha256": sha, "file": PAGE.relative_to(RAW_ROOT).as_posix(), "pages": [text]}, handle)
    services = {m.group("s"): m for m in SERVICE.finditer(text)}
    if set(services) != {"A", "B"}:
        raise SystemExit(f"Service A/B text not found as expected: {sorted(services)}")
    source = {
        "key": "mbusa-service-intervals", "kind": "pdf_pages", "path": "rawstore:" + PAGE.relative_to(RAW_ROOT).as_posix(),
        "url": URL, "page_url": URL, "sha256": sha, "retrieved_at": "2026-10-02",
        "tier": "A", "source_type": "MAINTENANCE_SCHEDULE_OFFICIAL", "registry": "factory-mercedes-us",
        "title": "Mercedes-Benz USA — Owners: Service & Maintenance, Service Intervals (Service A / Service B)",
        "publisher": "Mercedes-Benz USA (www.mbusa.com)", "authenticity": "OFFICIAL_PUBLISHER", "edition": "US",
        "model_year": None, "extract": json.dumps({"pdf_sha256": sha, "url": URL, "pages": {"1": text}}, ensure_ascii=False),
    }
    template = []
    for s, m in sorted(services.items()):
        quote = m.group(0)
        items_text = m.group("items")
        first_note = "approximately (as stated)" + (" ; " + m.group("after").strip() if m.group("after").strip() else "")
        for phrase, job, action in JOBS:
            if not re.search(phrase, items_text, re.I):
                continue
            for occurrence, miles, years, note, rule in (
                ("FIRST", m.group("m1"), m.group("y1"), first_note,
                 "WHICHEVER_FIRST" if "whichever comes first" in m.group("first") else None),
                ("SUBSEQUENT", m.group("m2"), m.group("y2"), "approximately (as stated)", None),
            ):
                mi = int(miles.replace(",", ""))
                template.append({
                    "service": f"Service {s}", "job": job, "action": action, "condition": "NORMAL",
                    "schedule_system": "SERVICE_A_B", "occurrence": occurrence,
                    "interval_km": miles_to_km(mi), "interval_months": int(years) * 12,
                    "interval_miles_original": mi, "rule": rule,
                    "note": f"Service {s}: {note}; scope: {SCOPE}", "quote": quote,
                })
    for line in lines_for("mercedes-benz"):
        path = WORK / "mercedes-benz" / "staging" / line.slug / "staging.json"
        if not path.exists():
            continue
        staging = json.loads(path.read_text(encoding="utf-8"))
        items, gaps = [], []
        for gen in staging["generations"]:
            powertrains = {c["powertrain"] for c in staging["configurations"]
                           if gen["start_year"] <= c["year"] <= gen["end_year"]}
            if not powertrains:
                continue
            if powertrains <= {"BEV", "FCEV"}:
                gaps.append({"scope": f"{line.key} {gen['code']}", "field": "maintenance",
                             "reason": "electric line: the official US page describes an EV service package without intervals"})
                continue
            for t in template:
                digest = hashlib.sha1(json.dumps([gen["code"], t["service"], t["job"], t["occurrence"]]).encode()).hexdigest()[:8]
                items.append({
                    "id": f"{line.slug}-{gen['code']}-mnt-{t['job']}-{digest}-{gen['start_year']}",
                    "generation": gen["code"], "years": [gen["start_year"], gen["end_year"]], "engine": None,
                    "applicability": {"service": t["service"], "scope": SCOPE, "powertrains": sorted(powertrains - {"BEV", "FCEV"}),
                                      "approx_in_source": True},
                    **{k: t[k] for k in ("action", "condition", "job", "occurrence", "schedule_system", "interval_km",
                                         "interval_months", "interval_miles_original", "rule", "note")},
                    "max_interval_km": None, "max_interval_months": None,
                    "cites": [{"source": source["key"], "quote": t["quote"], "pages": [1], "locator": f"Service Intervals: {t['service']}"}],
                    "primary_source": source["key"], "display_level": "SECONDARY_NOTE", "confidence": "MEDIUM",
                })
        out = WORK / "mercedes-benz" / "staging" / line.slug / "maintenance.json"
        out.write_text(json.dumps({"sources": {source["key"]: source} if items else {}, "items": items, "gaps": gaps},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(line.key, "items", len(items), "gaps", len(gaps), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

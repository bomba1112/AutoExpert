"""Shared pieces of the maintenance-schedule builders (next-stage prompt, stage B).

Every builder reads an official document already in the raw store (PDF page text, or HTML
text), and writes data_work/<make>/staging/<line>/maintenance_<source>.json:
  {"sources": {key: source}, "items": [item], "gaps": [gap]}
which build_us_batch_staging.py merges (all maintenance*.json of the line) and
load_us_tech_facts.py writes to maintenance_schedule_items.

Item = one job of the schedule (prompt main section 4 "ТО — строго структурно"):
  job, action (REPLACE/INSPECT/ROTATE/ADJUST/CLEAN), condition (NORMAL/SEVERE), occurrence
  (EVERY/FIRST/SUBSEQUENT), schedule_system (FIXED_INTERVAL/OIL_LIFE_MONITOR/MAINTENANCE_MINDER/
  CBS/SERVICE_A_B), interval_km (km as printed by the source, else miles converted by the units
  module), interval_months, interval_miles_original, rule (WHICHEVER_FIRST), max_interval_* for
  on-board systems when the document states a limit, the quote and page of the document.
Nothing is invented: a job, interval or applicability not printed in the document is not
written; the reason goes to the gaps.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "backend"))
from app.services.tech_units import convert  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402
from us_tech_lines import lines_for  # noqa: E402

JOBS = [  # (job, pattern) tried in order on an item's text
    ("engine_oil_and_filter", r"engine oil(?:\s*[&/,]\s*| and )?(?:oil )?filter|oil (?:and|&) (?:oil )?filter|change (?:the )?(?:engine )?oil|replace engine oil|engine oil,? change|oil change"),
    ("cabin_air_filter", r"cabin (?:air )?filter|dust and pollen filter|pollen filter|dust ?/ ?pollen|air conditioning filter|climate control filter|in-cabin"),
    ("engine_air_filter", r"engine air (?:cleaner )?filter|air cleaner (?:filter|element)|^\W*air filter|air filter\s*-\s*replace"),
    ("spark_plugs", r"spark plugs?"),
    ("brake_fluid", r"brake fluid|brake and clutch system,? chang"),
    ("engine_coolant", r"engine coolant|coolant(?!\s*pump)"),
    ("dual_clutch_fluid", r"\bDSG\b|dual[- ]clutch"),
    ("awd_coupling_fluid", r"AWD clutch|Haldex|all[- ]wheel[- ]drive (?:coupling|clutch)|torque splitter"),
    ("transmission_fluid", r"automatic transmission|transmission fluid|transaxle fluid|\bCVT\b|\bATF\b|transmission, automatic"),
    ("manual_transmission_fluid", r"manual transmission"),
    ("transfer_case_fluid", r"transfer case|transfer ?box"),
    ("differential_fluid", r"axle fluid|differential|power transfer unit|\bPTU\b|rear drive module|final drive"),
    ("timing_belt", r"timing belt|toothed belt|camshaft drive"),
    ("accessory_drive_belt", r"accessory drive belt|drive belt|serpentine|ribbed belt|v-ribbed|\bv-belt"),
    ("tire_rotation", r"rotate (?:the )?tires|tire rotation|tires\s*-\s*rotate"),
    ("fuel_filter", r"fuel filter"),
    ("brakes", r"brake (?:pads?|linings|shoes|rotors|discs?)|brake pad thickness|disc brake pads"),
    ("wiper_blades", r"wiper blades?"),
    ("battery_12v", r"\b12\s?v(?:olt)? battery|\bbattery\b"),
    ("ac_desiccant", r"desiccant"),
    ("diesel_exhaust_fluid", r"diesel exhaust fluid|\bDEF\b|AdBlue"),
]


def job_of(text: str) -> str | None:
    for job, pattern in JOBS:
        if re.search(pattern, text, re.I):
            return job
    return None


def action_of(text: str) -> str:
    t = text.lower()
    if re.search(r"\brotate\b", t):
        return "ROTATE"
    if re.search(r"\badjust\b", t) and not re.search(r"replace|change", t):
        return "ADJUST"
    if re.search(r"\bclean\b", t) and not re.search(r"replace|change", t):
        return "CLEAN"
    if re.search(r"replace|change|renew|flush|drain and fill|fill completely", t):
        return "REPLACE"
    if re.search(r"inspect|check|test|examine", t):
        return "INSPECT"
    return "REPLACE"


def miles_to_km(miles: int) -> int:
    return int(convert(miles, "mi", "km"))


def num(text: str) -> int:
    return int(str(text).replace(",", "").replace(".", ""))


INTERVAL = re.compile(
    r"(?:every|at intervals of|at)?\s*(?P<miles>\d{1,3}(?:,\d{3})+|\d{4,6}|\d{1,3}\s?[Kk])\s*(?:mi\b|miles?)"
    r"(?:\s*\(\s*(?P<km>\d{1,3}(?:,\d{3})+|\d{4,6}|\d{1,3}\s?[Kk])\s*km\s*\))?"
    r"(?:\s*,?\s*or\s*(?:every\s*)?(?P<years>\d{1,2})\s*years?|\s*,?\s*or\s*(?:every\s*)?(?P<months>\d{1,3})\s*months?)?", re.I)
YEARS_ONLY = re.compile(r"every\s*(?P<years>\d{1,2})\s*years?|every\s*(?P<months>\d{1,3})\s*months?", re.I)


def kilo(text: str | None) -> int | None:
    if not text:
        return None
    t = text.replace(" ", "")
    return int(t[:-1]) * 1000 if t[-1] in "kK" else num(t)


def interval_of(text: str) -> dict | None:
    """'Every 60,000 miles (90K km), or 6 years, whichever occurs first' ->
    {interval_km: 90000 (as printed), interval_miles_original: 60000, interval_months: 72,
    rule: WHICHEVER_FIRST}; 'every 2 years' -> months only."""
    m = INTERVAL.search(text)
    if m:
        miles = kilo(m.group("miles"))
        km = kilo(m.group("km")) or miles_to_km(miles)
        months = int(m.group("years")) * 12 if m.group("years") else int(m.group("months")) if m.group("months") else None
        return {"interval_km": km, "interval_miles_original": miles, "interval_months": months,
                "rule": "WHICHEVER_FIRST" if months and re.search(r"whichever|which ever", text, re.I) else None,
                "matched": m.group(0).strip()}
    m = YEARS_ONLY.search(text)
    if m:
        months = int(m.group("years")) * 12 if m.group("years") else int(m.group("months"))
        return {"interval_km": None, "interval_miles_original": None, "interval_months": months, "rule": None,
                "matched": m.group(0).strip()}
    return None


def page_text(sha: str) -> list[str]:
    with gzip.open(RAW_ROOT / "pagetext" / f"{sha}.json.gz", "rt", encoding="utf-8") as handle:
        return json.load(handle)["pages"]


def sha_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text: str) -> str:
    return " ".join(str(text).replace(" ", " ").replace("￾", "").split())


def pdf_source(key: str, path: Path, sha: str, url: str, title: str, publisher: str, registry: str, years: list[int],
               pages_used: set[int], retrieved_at: str, source_type: str = "MAINTENANCE_SCHEDULE_OFFICIAL",
               tier: str = "A", authenticity: str = "OFFICIAL_PUBLISHER") -> dict:
    pages = page_text(sha)
    return {"key": key, "kind": "pdf_pages", "path": "rawstore:" + path.relative_to(RAW_ROOT).as_posix(), "url": url,
            "page_url": url, "sha256": sha, "retrieved_at": retrieved_at, "tier": tier, "source_type": source_type,
            "registry": registry, "title": title, "publisher": publisher, "authenticity": authenticity, "edition": "US",
            "model_year": years[0] if years else None,
            "extract": json.dumps({"pdf_sha256": sha, "url": url, "pages": {str(p): pages[p - 1] for p in sorted(pages_used)}},
                                  ensure_ascii=False)}


def generations_of(make: str, line_slug: str) -> list[dict]:
    path = WORK / make / "staging" / line_slug / "staging.json"
    return json.loads(path.read_text(encoding="utf-8"))["generations"] if path.exists() else []


def gen_for(gens: list[dict], year: int) -> str | None:
    return next((g["code"] for g in gens if g["start_year"] <= year <= g["end_year"]), None)


def item(line_slug: str, gen: str, year: int, job: str, action: str, *, condition: str = "NORMAL", occurrence: str = "EVERY",
         system: str = "FIXED_INTERVAL", interval: dict | None = None, applicability: dict | None = None,
         note: str | None = None, max_interval: dict | None = None, source: str, quote: str, page: int,
         locator: str, display_level: str = "FACT", confidence: str = "HIGH") -> dict:
    interval = interval or {}
    max_interval = max_interval or {}
    body = {"job": job, "action": action, "condition": condition, "occurrence": occurrence, "schedule_system": system,
            "interval_km": interval.get("interval_km"), "interval_months": interval.get("interval_months"),
            "interval_miles_original": interval.get("interval_miles_original"), "rule": interval.get("rule"),
            "max_interval_km": max_interval.get("interval_km"), "max_interval_months": max_interval.get("interval_months"),
            "applicability": applicability or {}, "note": note}
    digest = hashlib.sha1(json.dumps([gen, body], sort_keys=True).encode()).hexdigest()[:8]
    return {"id": f"{line_slug}-{gen}-mnt-{job}-{digest}", "generation": gen, "years": [year, year], "engine": None, **body,
            "cites": [{"source": source, "quote": norm(quote), "pages": [page], "locator": locator}],
            "primary_source": source, "display_level": display_level, "confidence": confidence}


def merge_years(items: list[dict]) -> list[dict]:
    """Identical items (same generation and content) of consecutive model years become one item
    covering the years; their citations are kept together."""
    groups = defaultdict(list)
    for it in items:
        groups[it["id"]].append(it)
    out = []
    for _, group in groups.items():
        group.sort(key=lambda x: x["years"][0])
        run = None
        for it in group:
            if run and it["years"][0] <= run["years"][1] + 1:
                run["years"][1] = max(run["years"][1], it["years"][1])
                run["cites"] += [c for c in it["cites"] if c not in run["cites"]]
            else:
                run = json.loads(json.dumps(it))
                out.append(run)
    for it in out:
        it["id"] = f"{it['id']}-{it['years'][0]}"
        it["primary_source"] = it["cites"][0]["source"]
    return out


def write(make: str, line_slug: str, name: str, sources: dict, items: list[dict], gaps: list[dict]) -> Path:
    used = {c["source"] for it in items for c in it["cites"]}
    out = WORK / make / "staging" / line_slug / f"maintenance_{name}.json"
    out.write_text(json.dumps({"sources": {k: v for k, v in sources.items() if k in used}, "items": items, "gaps": gaps},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def our_lines(make: str) -> dict:
    return {line.slug: line for line in lines_for(make, include_done=True)}


def json_values(path: Path) -> list[str]:
    """String and number values of a JSON source (Mopar schedule data), in document order,
    normalised: the "page text" of a json_file source for the quote checks."""
    out = []

    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, (str, int, float)) and not isinstance(node, bool):
            text = norm(str(node))
            if text:
                out.append(text)

    walk(json.loads(Path(path).read_text(encoding="utf-8")))
    return out


def json_quote_found(values: list[str], quote: str) -> bool:
    """The quote is one value of the JSON source, or a value followed by another one (the
    builders quote '<ancillary title> <service>' of the Mopar data)."""
    q = norm(quote)
    if any(q in v for v in values):
        return True
    return any(q.startswith(v) and any(q[len(v):].strip() == w for w in values) for v in values if len(v) < len(q))

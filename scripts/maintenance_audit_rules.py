"""Rules from the round-3 independent audit of the maintenance verification (2026-10-04).

The audit found CONFIRMED items whose interval is printed as stored but whose scope or job is not
what the source says. The verifier (scripts/verify_maintenance_source.py) applies these rules after
its own checks, so an item they match is UNCONFIRMED (hidden from users, owner decision
2026-10-04) with the reason below. The builders are not changed here: each rule names the builder
fault so it can be fixed later, and the item then passes again only if the fault is gone.

  source_generation_mismatch    Hyundai: the manual of another generation (the year in the
                                manufacturer's manual URL taken as the model year: the 2018 "TMa"
                                Santa Fe manual filed under the NC generation, the 2021 "NX4a"
                                Tucson manual under TL). A vehicle code used by two generations of
                                a line belongs to the one with more items; the other's items fail.
  mopar_schedule_other_generation  Jeep Compass MP 2017 items from the MK schedule (Mopar 108.json:
                                CVT / six-speed ATF rows, PTU and RDA fluid).
  transmission_scope_not_carried  a "(multitronic)" / "Continuously Variable Transmission" row
                                stored without a CVT scope.
  job_names_other_component     a "Connected box / OCU / ConMod battery" row stored as the 12 V
                                battery.
  months_printed_in_note_not_in_item  the item's own note (or the page's "Initial replacement at N
                                years" footnote, Ford coolant) prints a time limit the item lacks.
  footnote_scope_not_carried    a "*N" marker on the row whose footnote is only a scope ("*6:
                                6-cylinder models") while the item names no engine / drive /
                                transmission.
  applicability_truncated       an applicability value with an unbalanced "(" ("Passat (A3"):
                                the restriction inside the parenthesis was cut off.
"""

from __future__ import annotations

import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

RAW = Path(r"C:\AutoExpertData\raw")
SCOPE_FOOT = re.compile(r"^\s*(?:(?:4|6|four|six)[- ]cylinder|V6|V-6|4WD|AWD|2WD|FWD|manual transmission|automatic transmission|CVT|"
                        r"continuously variable transmission|hybrid|turbo|non[- ]turbo|[\d.]+ ?L)[\w\s/-]{0,25}?models?\s*(?:only)?\.?\s*$", re.I)
_pages: dict[str, list[str]] = {}


def _page(source: dict, number: int) -> str:
    sha = source.get("sha256") or ""
    if sha not in _pages:
        path = RAW / "pagetext" / f"{sha}.json.gz"
        _pages[sha] = json.load(gzip.open(path, "rt", encoding="utf-8"))["pages"] if path.exists() else []
    pages = _pages[sha]
    return pages[number - 1] if 0 < number <= len(pages) else ""


def _primary(item: dict) -> dict:
    return next((c for c in item["cites"] if c["source"] == item.get("primary_source")), item["cites"][0])


def _vehicle_code(title: str) -> str | None:
    m = re.search(r"\(([A-Z]{2}\d?[A-Z0-9]*?)(?:a|HEV|PHEV|aHEV|aPHEV)?, ", title or "")
    return m.group(1) if m else None


def reasons_for(make: str, items: list[tuple[dict, dict]]) -> dict[str, list[str]]:
    """{item id: [reason]} for the items (item, sources of its file) of one line."""
    out = defaultdict(list)
    if make == "hyundai":
        by_code = defaultdict(Counter)
        for item, sources in items:
            code = _vehicle_code(sources.get(item["primary_source"], {}).get("title"))
            if code:
                by_code[code][item["generation"]] += 1
        for item, sources in items:
            code = _vehicle_code(sources.get(item["primary_source"], {}).get("title"))
            if code and len(by_code[code]) > 1 and item["generation"] != by_code[code].most_common(1)[0][0]:
                out[item["id"]].append("source_generation_mismatch")
    for item, sources in items:
        if not item.get("cites"):
            continue
        pc = _primary(item)
        quote = pc.get("quote") or ""
        source = sources.get(pc["source"], {})
        app = item.get("applicability") or {}
        if make == "jeep" and item["generation"] == "MP" and item["years"][0] <= 2017 <= item["years"][1] \
                and all(str(sources.get(c["source"], {}).get("path", "")).endswith("/108.json") for c in item["cites"]):
            out[item["id"]].append("mopar_schedule_other_generation")
        if re.search(r"multitronic|continuously variable", quote, re.I) and "cvt" not in json.dumps(app).lower():
            out[item["id"]].append("transmission_scope_not_carried")
        if item["job"] in ("battery_12v", "battery") and re.search(r"connected box|\bOCU\b|conmod", quote, re.I):
            out[item["id"]].append("job_names_other_component")
        note = item.get("note") or ""
        if (item.get("interval_months") is None and item.get("interval_miles_original") and item.get("schedule_system") == "FIXED_INTERVAL"
                and re.search(r"\b(?:one|two|three|four|five|six|seven|eight|ten|\d+)\s+(?:years?|months?)\b", note, re.I)
                and not re.search(r"regardless of mileage|more frequent", note, re.I)):
            out[item["id"]].append("months_printed_in_note_not_in_item")
        if (make == "ford" and item["job"] == "engine_coolant" and item["occurrence"] == "FIRST" and not item.get("interval_months")
                and any(re.search(r"Initial replacement at \w+ years", _page(sources.get(c["source"], {}), p))
                        for c in item["cites"] for p in (c.get("pages") or []) if sources.get(c["source"], {}).get("kind") == "pdf_pages")):
            out[item["id"]].append("months_printed_in_note_not_in_item")
        marks = re.findall(r"\*(\d+)", quote)
        scoped = {k: v for k, v in app.items() if k not in ("minder_code", "edition", "service")}
        if marks and source.get("kind") == "pdf_pages" and not scoped and not item.get("engine"):
            for p in pc.get("pages") or []:
                text = " ".join(_page(source, p).split())
                if any((fm := re.search(r"\*" + m + r":\s*(.{0,80}?)(?=\s\*\d+:|\sCODE\b|$)", text)) and SCOPE_FOOT.match(fm.group(1))
                       for m in marks):
                    out[item["id"]].append("footnote_scope_not_carried")
                    break
        if any(isinstance(v, str) and v.count("(") > v.count(")") for v in app.values()):
            out[item["id"]].append("applicability_truncated")
    return {k: sorted(set(v)) for k, v in out.items()}


def apply(make: str, records: list[dict], work: Path) -> list[dict]:
    """Mark the records the audit rules match UNCONFIRMED (reasons added, prefixed 'audit:')."""
    by_line = defaultdict(list)
    for path in sorted((work / make / "staging").glob("*/maintenance*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        by_line[path.parent.name] += [(item, data.get("sources", {})) for item in data.get("items", [])]
    found = {}
    for line, items in by_line.items():
        for item_id, reasons in reasons_for(make, items).items():
            found[(line, item_id)] = reasons
    for r in records:
        reasons = found.get((r["line"], r["item_id"]))
        if reasons:
            r["verdict"] = "UNCONFIRMED"
            r["reasons"] = sorted(set((r.get("reasons") or []) + [f"audit:{x}" for x in reasons]))
    return records

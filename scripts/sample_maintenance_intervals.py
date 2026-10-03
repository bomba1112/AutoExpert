"""10% sample of maintenance items (stage B): does the cited text state the interval written?

For each sampled item with a fixed distance, the printed number (miles as printed, or km) must be
found in the item's quotes or on the cited page; months / years the same way. Items whose
interval comes from a chart position (GM mileage charts, Nissan grids) carry the chart row as the
quote, so for them the page is searched. Prints the agreement and every disagreement.

  .venv/Scripts/python.exe scripts/sample_maintenance_intervals.py chevrolet ford ...
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from maintenance_common import norm, page_text  # noqa: E402
from us_tech_common import WORK  # noqa: E402


def digits(text: str) -> str:
    return re.sub(r"(?<=\d)[,\s.](?=\d{3}\b)", "", text)


def stated(number: int, text: str) -> bool:
    return bool(re.search(rf"(?<![\d.]){number}(?![\d])", digits(text)))


def months_stated(months: int, text: str) -> bool:
    years = months // 12 if months % 12 == 0 else None
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 10: "ten"}
    t = text.lower()
    if stated(months, t) and re.search(rf"{months}\s*(?:months?|mo\b|mos\b)", digits(t)):
        return True
    if years and (re.search(rf"\b{years}\s*(?:years?|yrs?)\b", t) or (years in words and re.search(rf"\b{words[years]}\s*years?\b", t))):
        return True
    if re.search(r"\bmonths\b", t) and stated(months, t):
        return True  # a schedule grid prints the months in its own header row
    return years == 1 and bool(re.search(r"\b(?:every|once a|each|per|1)\s*year|annual|yearly|12 months", t))


def main(makes: list[str]) -> int:
    rnd = random.Random(20261003)
    sampled = agree = 0
    misses = []
    for make in makes:
        for path in sorted((WORK / make / "staging").glob("*/maintenance_*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            sources = data.get("sources", {})
            items = [it for it in data.get("items", []) if it.get("interval_km") or it.get("interval_months")]
            for it in rnd.sample(items, max(1, len(items) // 10)) if items else []:
                sampled += 1
                quotes = " ".join(c.get("quote", "") for c in it["cites"])
                pages = ""
                for c in it["cites"]:
                    src = sources.get(c["source"]) or {}
                    sha = src.get("sha256")
                    if sha:
                        text = page_text(sha)
                        pages += " ".join(text[p - 1] for p in c.get("pages", []) if 0 < p <= len(text))
                text = norm(quotes + " " + pages)
                ok = True
                if it.get("interval_km"):
                    miles = it.get("interval_miles_original")
                    ok &= stated(it["interval_km"], text) or bool(miles and stated(miles, text)) or bool(
                        miles and stated(miles // 1000, text) and re.search(r"x\s*1,?000|thousand", text, re.I))
                if it.get("interval_months"):
                    ok &= months_stated(it["interval_months"], text)
                if ok:
                    agree += 1
                else:
                    misses.append((make, path.parent.name, it["job"], it.get("interval_km"), it.get("interval_miles_original"),
                                   it.get("interval_months"), it["years"], quotes[:160]))
    print(f"sampled {sampled}, interval stated in the cited text {agree} ({agree / max(sampled, 1):.0%})")
    for m in misses:
        print("  MISS", *m)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Full re-check of maintenance items of stage B (every item, not a sample): the cited document is
the one stored (sha256 of the file, or of the page-text store for HTML copies), the quote is found
again on the cited page (for a JSON source, Mopar schedule data: among the values of the file),
enum values are the database's, a fixed interval has a distance or a time and the distance is
plausible. Every maintenance*.json of a line is checked (maintenance.json of the Mopar,
Hyundai/Kia and Mercedes builders and maintenance_<source>.json of the others).

  .venv/Scripts/python.exe scripts/recheck_maintenance.py volkswagen audi [...]
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from maintenance_common import json_quote_found, json_values, norm, page_text  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

SYSTEMS = {"FIXED_INTERVAL", "OIL_LIFE_MONITOR", "MAINTENANCE_MINDER", "CBS", "SERVICE_A_B"}
ACTIONS = {"REPLACE", "INSPECT", "ROTATE", "ADJUST", "CLEAN"}


def main(makes: list[str]) -> int:
    checked = bad = 0
    sha_ok: dict[str, bool] = {}
    json_cache: dict[str, list[str]] = {}
    for make in makes:
        for path in sorted((WORK / make / "staging").glob("*/maintenance*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for it in data["items"]:
                checked += 1
                problems = []
                if it["schedule_system"] not in SYSTEMS or it["action"] not in ACTIONS:
                    problems.append("enum")
                if it["condition"] not in {"NORMAL", "SEVERE"} or it["occurrence"] not in {"EVERY", "FIRST", "SUBSEQUENT"}:
                    problems.append("enum")
                if it["schedule_system"] == "FIXED_INTERVAL" and not (it.get("interval_km") or it.get("interval_months")):
                    problems.append("fixed interval without distance or time")
                if it.get("interval_km") and not 1000 <= it["interval_km"] <= 400000:
                    problems.append(f"interval_km {it['interval_km']}")
                for cite in it["cites"]:
                    src = data["sources"].get(cite["source"])
                    if src is None:
                        problems.append(f"source {cite['source']} missing")
                        continue
                    raw = RAW_ROOT / src["path"][len("rawstore:"):]
                    if raw.is_file():
                        if src["sha256"] not in sha_ok:
                            data_bytes = raw.read_bytes()
                            # a page stored gzipped (mbusa service page) is identified by its content
                            sha_ok[src["sha256"]] = src["sha256"] in {hashlib.sha256(data_bytes).hexdigest(),
                                                                      hashlib.sha256(gzip.decompress(data_bytes)).hexdigest() if raw.suffix == ".gz" else None}
                        if not sha_ok[src["sha256"]]:
                            problems.append("sha256 differs")
                            continue
                    if src.get("kind") == "json_file":
                        if src["sha256"] not in json_cache:
                            json_cache[src["sha256"]] = json_values(raw) if raw.is_file() else []
                        if not json_quote_found(json_cache[src["sha256"]], cite["quote"]):
                            problems.append(f"quote not in the JSON source: {cite['quote'][:80]}")
                        continue
                    pages = page_text(src["sha256"])
                    if not any(norm(cite["quote"]) in norm(pages[p - 1]) for p in cite.get("pages") or []):
                        problems.append(f"quote not on page {cite.get('pages')}: {cite['quote'][:80]}")
                if problems:
                    bad += 1
                    print(path.parent.name, it["id"], problems)
    print(f"maintenance items checked {checked}, problems {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Full re-check of maintenance items of stage B (every item, not a sample): the cited document is
the one stored (sha256 of the file, or of the page-text store for HTML copies), the quote is found
again on the cited page, enum values are the database's, a fixed interval has a distance or a
time and the distance is plausible.

  .venv/Scripts/python.exe scripts/recheck_maintenance.py volkswagen audi [...]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from maintenance_common import norm, page_text  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

SYSTEMS = {"FIXED_INTERVAL", "OIL_LIFE_MONITOR", "MAINTENANCE_MINDER", "CBS", "SERVICE_A_B"}
ACTIONS = {"REPLACE", "INSPECT", "ROTATE", "ADJUST", "CLEAN"}


def main(makes: list[str]) -> int:
    checked = bad = 0
    sha_ok: dict[str, bool] = {}
    for make in makes:
        for path in sorted((WORK / make / "staging").glob("*/maintenance_*.json")):
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
                            sha_ok[src["sha256"]] = hashlib.sha256(raw.read_bytes()).hexdigest() == src["sha256"]
                        if not sha_ok[src["sha256"]]:
                            problems.append("sha256 differs")
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

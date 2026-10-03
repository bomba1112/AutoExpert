"""Self-check of maintenance*.json files (maintenance.json and maintenance_<name>.json): every
cite of every item is re-opened in the page-text store (RAW_ROOT/pagetext/<sha256>.json.gz of
the cited source) and its quote must be a substring of the cited page (both normalised by
maintenance_common.norm); a cite of a JSON source (Mopar schedule data) must be found among the
values of the stored file. Also checks the DB enums and the interval rules of the backend test.

  .venv/Scripts/python.exe scripts/check_maintenance_quotes.py chevrolet ford tesla [--name owner_manual]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from maintenance_common import json_quote_found, json_values, norm, page_text  # noqa: E402
from us_tech_common import RAW_ROOT, WORK  # noqa: E402

SYSTEMS = {"FIXED_INTERVAL", "OIL_LIFE_MONITOR", "MAINTENANCE_MINDER", "CBS", "SERVICE_A_B"}


def main(argv: list[str]) -> int:
    name = argv[argv.index("--name") + 1] if "--name" in argv else None
    makes = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--name")]
    checked, problems, cache = 0, [], {}
    for make in makes:
        pattern = f"maintenance_{name}.json" if name else "maintenance*.json"
        for path in sorted((WORK / make / "staging").glob(f"*/{pattern}")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for it in data["items"]:
                where = f"{path.parent.name}/{path.name} {it['id']}"
                if it["schedule_system"] not in SYSTEMS or it["action"] not in {"REPLACE", "INSPECT", "ROTATE", "ADJUST", "CLEAN"} \
                        or it["condition"] not in {"NORMAL", "SEVERE"} or it["occurrence"] not in {"EVERY", "FIRST", "SUBSEQUENT"}:
                    problems.append(f"{where}: enum value")
                if it["schedule_system"] == "FIXED_INTERVAL" and not (it.get("interval_km") or it.get("interval_months")):
                    problems.append(f"{where}: fixed interval without km or months")
                if it.get("interval_km") and not 1000 <= it["interval_km"] <= 400000:
                    problems.append(f"{where}: interval_km {it['interval_km']}")
                if it["primary_source"] not in data["sources"]:
                    problems.append(f"{where}: primary source missing")
                for cite in it["cites"]:
                    source = data["sources"].get(cite["source"])
                    if source is None:
                        problems.append(f"{where}: source {cite['source']} missing")
                        continue
                    sha = source["sha256"]
                    if source.get("kind") == "json_file":
                        checked += 1
                        if sha not in cache:
                            cache[sha] = json_values(RAW_ROOT / source["path"][len("rawstore:"):])
                        if not json_quote_found(cache[sha], cite["quote"]):
                            problems.append(f"{where}: quote not in the JSON source: {cite['quote'][:80]}")
                        continue
                    if sha not in cache:
                        cache[sha] = [norm(p) for p in page_text(sha)]
                    for page in cite["pages"]:
                        checked += 1
                        if norm(cite["quote"]) not in cache[sha][page - 1]:
                            problems.append(f"{where}: quote not on page {page}: {cite['quote'][:80]}")
                        extract = json.loads(source["extract"])["pages"]
                        if str(page) not in extract:
                            problems.append(f"{where}: page {page} not in the source extract")
    for p in problems[:50]:
        print("PROBLEM", p)
    print(f"checked {checked}, problems {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

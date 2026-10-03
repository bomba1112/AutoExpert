"""What a rebuilt staging set changes against the committed one (git HEAD), per line: facts,
issues and maintenance items added / removed, by stable id. Run before a rehearsal to make sure a
maintenance pass leaves the technical facts alone.

  .venv/Scripts/python.exe scripts/staging_delta.py volkswagen [audi ...]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ids(staging: dict, part: str) -> set[str]:
    return {x.get("id") or json.dumps(x, sort_keys=True) for x in staging.get(part, [])}


def main(makes: list[str]) -> int:
    for make in makes:
        for path in sorted((ROOT / "data_work" / make / "staging").glob("*/staging.json")):
            rel = path.relative_to(ROOT).as_posix()
            old = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True)
            before = json.loads(old.stdout.decode("utf-8")) if old.returncode == 0 else {}
            after = json.loads(path.read_text(encoding="utf-8"))
            parts = []
            for part in ("facts", "issues", "maintenance"):
                a, b = ids(before, part), ids(after, part)
                parts.append(f"{part} +{len(b - a)} -{len(a - b)} (={len(b)})")
            print(make, path.parent.name, " | ".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

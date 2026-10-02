"""Compare the generation blocks of rebuilt batch staging with the committed (loaded) version.

Prints every line whose generation codes or years differ from git HEAD, so a rule change
in build_us_batch_staging.py is never applied to loaded makes unnoticed.

  .venv/Scripts/python.exe scripts/compare_generations.py [--evidence make/line]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def blocks(staging):
    return [(g["code"], g["start_year"], g["end_year"]) for g in staging["generations"]]


def main(argv) -> int:
    changed = 0
    for path in sorted(ROOT.glob("data_work/*/staging/*/staging.json")):
        rel = path.relative_to(ROOT).as_posix()
        new = json.loads(path.read_text(encoding="utf-8"))
        if not new.get("build"):
            continue
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode:
            continue
        old = json.loads(result.stdout)
        if blocks(old) != blocks(new):
            changed += 1
            print(rel, blocks(old), "->", blocks(new))
    for key in argv[argv.index("--evidence") + 1:] if "--evidence" in argv else []:
        make, line = key.split("/")
        staging = json.loads((ROOT / "data_work" / make / "staging" / line / "staging.json").read_text(encoding="utf-8"))
        for g in staging["generations"]:
            print(key, g["code"], g["start_year"], g["end_year"], g["boundary_evidence"])
    print("changed lines:", changed)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

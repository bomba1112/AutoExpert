"""Second load pass over several makes in the owner's order, stopping on anything to review.

Per make: build -> 10% recheck -> fresh rehearsal copy -> rehearsal load -> checks -> live load
-> project tests -> git commit "data(us): <Make> — ...". The pass stops (exit 1) when:
  - the staging has validation errors;
  - the recheck finds a mismatch;
  - the rehearsal reports a conflict (an earlier row would be kept against a new value) or a
    stale row whose field/value is not in the new staging (a loss to review);
  - quick_check is not ok, a load exits non-zero, or the tests fail.

  .venv/Scripts/python.exe scripts/run_conveyor.py bmw chevrolet ford ...
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from us_tech_lines import MAKES, lines_for  # noqa: E402

PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
UV = ["uv", "run", "--no-project", "--with", "pdfplumber", "--with", "pypdfium2", "--with", "httpx", "--with", "beautifulsoup4", "python"]
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
REHEARSAL = Path(r"C:\AutoExpertData\work\rehearsal_batch.db")
REGISTER = ["scripts/register_carcomplaints.py", "scripts/register_factory_ford_us.py"]


def sh(args, env=None, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, env=env or ENV, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def refresh_copy() -> None:
    src, dst = sqlite3.connect(ROOT / "autoexpert.db"), sqlite3.connect(REHEARSAL)
    src.backup(dst)
    dst.close()
    src.close()


def conflicts(make: str, report_name: str) -> list:
    out = []
    for line in lines_for(make):
        path = ROOT / f"data_work/{make}/staging/{line.slug}/{report_name}"
        if path.exists():
            out += [{"line": line.key, **c} for c in json.loads(path.read_text(encoding="utf-8")).get("conflicts", [])]
    return out


def one(make: str) -> bool:
    name = MAKES[make]["epa"]
    print(f"===== {name}", flush=True)
    r = sh([PY, "scripts/run_make_pass.py", make, "build"])
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-500:], flush=True)
    if r.returncode:
        print("STOP: staging errors", r.stdout[-2000:])
        return False
    r = sh([*UV, "scripts/recheck_us_batch.py", make])
    recheck = json.loads((ROOT / f"data_work/{make}/staging/recheck_10pct.json").read_text(encoding="utf-8"))
    checked = sum(v["checked"] for v in recheck.values())
    bad = sum(v["mismatches"] for v in recheck.values())
    print(f"recheck {checked} checked, {bad} mismatches", flush=True)
    if bad:
        print("STOP: recheck mismatches")
        return False
    refresh_copy()
    r = sh([PY, "scripts/run_make_pass.py", make, "rehearse"])
    summary = json.loads((ROOT / f"data_work/{make}/staging/load_pass_rehearsal.json").read_text(encoding="utf-8"))
    found = conflicts(make, "load_report_rehearsal.json")
    print(f"rehearsal: stopped_at={summary.get('stopped_at')} quick_check={summary.get('quick_check')} "
          f"conflicts={len(found)} stale_without_same_value={len(summary.get('stale_without_same_value', []))}", flush=True)
    if summary.get("stopped_at") or summary.get("quick_check") != "ok" or found or summary.get("stale_without_same_value"):
        print("STOP: review the rehearsal", json.dumps({"conflicts": found[:20], "stale": summary.get("stale_without_same_value", [])[:20]}, ensure_ascii=False, indent=1))
        return False
    first = not any((ROOT / f"data_work/{make}/staging/{line.slug}/load_report.json").exists() for line in lines_for(make))
    r = sh([PY, "scripts/run_make_pass.py", make, "live"])
    live = json.loads((ROOT / f"data_work/{make}/staging/load_pass_live.json").read_text(encoding="utf-8"))
    print(f"live: stopped_at={live.get('stopped_at')} quick_check={live.get('quick_check')} fk={live.get('foreign_key_violations')}", flush=True)
    if live.get("stopped_at") or live.get("quick_check") != "ok":
        print("STOP: live load", r.stdout[-2000:])
        return False
    t = sh([PY, "-m", "pytest", "backend/tests/test_us_tech_database.py", "-q", "-p", "no:cacheprovider"])
    tail = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else ""
    print("tests:", tail, flush=True)
    if t.returncode:
        print("STOP: tests", t.stdout[-3000:])
        return False
    counts = {"te": 0, "issues_updated": 0, "maintenance": 0}
    for v in live.get("lines", {}).values():
        c = v.get("counts") or {}
        counts["te"] += sum(n for k, n in c.items() if k.startswith("te_new"))
        counts["issues_updated"] += c.get("issues_updated", 0)
        counts["maintenance"] += c.get("maintenance_new", 0)
    title = (f"data(us): {name} — first load: base layer (EPA, vPIC, NHTSA, known issues), manual and press facts, CarComplaints\n\n"
             if first else f"data(us): {name} — owner's manual facts, press specifications, CarComplaints (second pass)\n\n")
    message = title + (
        f"Lines:{', '.join(v for v in live.get('lines', {}))}. New technical evidence rows: {counts['te']}; "
        f"issues updated with CarComplaints evidence: {counts['issues_updated']}; maintenance items: {counts['maintenance']}.\n"
        f"Lines reloaded with --replace-own (generation blocks changed): {live.get('replace_own') or 'none'}.\n"
        f"Live: quick_check ok, FK violations {live.get('foreign_key_violations')}, 0 conflicts, 0 stale values "
        f"without the same value; 10% recheck {checked} checked, 0 mismatches; tests: {tail}.\n\n"
        "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
    )
    sh(["git", "add", "scripts", f"data_work/{make}", "data_work/_shared/manifest_press", "data_work/_shared/manifest_official"])
    c = sh(["git", "commit", "-q", "-F", "-"], input=message)
    head = sh(["git", "log", "--oneline", "-n", "1"]).stdout.strip()
    print("commit:", head, c.stderr.strip()[-300:], flush=True)
    return True


def main(argv) -> int:
    for script in REGISTER:
        print(sh([PY, script], env={**ENV, "AUTOEXPERT_DATABASE_URL": f"sqlite:///{(ROOT / 'autoexpert.db').as_posix()}"}).stdout.strip())
    for make in argv:
        if not one(make):
            return 1
    print("conveyor finished:", " ".join(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

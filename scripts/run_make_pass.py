"""One make through the conveyor: build -> validate -> recheck -> rehearsal or live load.

  build      build_manual_facts + build_us_batch_staging for the make (staging errors stop it)
  recheck    10% re-check (run under uv with pdfplumber for the geometric part)
  rehearse   load every batch line of the make into C:\\AutoExpertData\\work\\rehearsal_batch.db
  live       rolling backup of autoexpert.db to C:\\AutoExpertBackups, then load every line

Lines whose generation blocks changed against git HEAD are loaded with --replace-own
(own rows removed and reloaded); all others with --prune-stale. A load that exits non-zero
stops the pass. Summary per line: data_work/<make>/staging/load_pass_<mode>.json.

  .venv/Scripts/python.exe scripts/run_make_pass.py hyundai build|rehearse|live
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from us_tech_lines import lines_for  # noqa: E402

PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
LIVE = ROOT / "autoexpert.db"
REHEARSAL = Path(r"C:\AutoExpertData\work\rehearsal_batch.db")
BACKUP = Path(r"C:\AutoExpertBackups\autoexpert.db.backup_batch_latest")
ENV = {"PYTHONIOENCODING": "utf-8"}


def run(args: list[str], log: Path | None = None) -> int:
    import os

    env = {**os.environ, **ENV}
    if log:
        with log.open("w", encoding="utf-8") as handle:
            return subprocess.run(args, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT).returncode
    return subprocess.run(args, cwd=ROOT, env=env).returncode


def changed_generations(make: str) -> set[str]:
    """Lines whose generation blocks differ from the committed staging (git HEAD)."""
    out = set()
    for line in lines_for(make):
        path = f"data_work/{make}/staging/{line.slug}/staging.json"
        report = f"data_work/{make}/staging/{line.slug}/load_report.json"
        if not (ROOT / path).exists() or not (ROOT / report).exists():
            continue  # never loaded live: a first load, nothing to replace
        # the staging that was loaded live is the one committed with the last live load report
        commit = subprocess.run(["git", "log", "--format=%H", "-n", "1", "--", report],
                                cwd=ROOT, capture_output=True, text=True).stdout.strip()
        old = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True) if commit else None
        if old is None or old.returncode != 0:
            continue
        blocks = lambda staging: sorted((g["code"], g["start_year"], g["end_year"]) for g in staging["generations"])  # noqa: E731
        if blocks(json.loads(old.stdout)) != blocks(json.loads((ROOT / path).read_text(encoding="utf-8"))):
            out.add(line.slug)
    return out


def build(make: str) -> int:
    logs = Path(r"C:\AutoExpertData\logs")
    if run([PY, "scripts/build_manual_facts.py", make], logs / f"pass_manual_{make}.log"):
        print("build_manual_facts failed")
        return 1
    run([PY, "scripts/build_us_batch_staging.py", make], logs / f"pass_stage_{make}.log")
    errors = 0
    for line in lines_for(make):
        path = ROOT / f"data_work/{make}/staging/{line.slug}/staging.json"
        if path.exists():
            staging = json.loads(path.read_text(encoding="utf-8"))
            if staging.get("build"):
                errors += len(staging["errors"])
                if staging["errors"]:
                    print(line.key, "errors", staging["errors"][:3])
    print(make, "staging errors", errors)
    return 1 if errors else 0


def parse_summary(text: str) -> dict:
    """The loader prints its summary as an indented JSON object last; find its opening line."""
    lines = text.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if lines[i] == "{":
            try:
                return json.loads("\n".join(lines[i:]))
            except json.JSONDecodeError:
                continue
    return {}


def backup_live() -> None:
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    src, dst = sqlite3.connect(LIVE), sqlite3.connect(BACKUP)
    src.backup(dst)
    dst.close()
    src.close()
    print("backup", BACKUP)


def load(make: str, mode: str) -> int:
    db = LIVE if mode == "live" else REHEARSAL
    if mode == "live":
        backup_live()
    replace = changed_generations(make)
    summary = {"make": make, "mode": mode, "db": str(db), "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
               "replace_own": sorted(replace), "lines": {}}
    logs = Path(r"C:\AutoExpertData\logs")
    for line in lines_for(make):
        path = ROOT / f"data_work/{make}/staging/{line.slug}/staging.json"
        if not path.exists() or not json.loads(path.read_text(encoding="utf-8")).get("build"):
            continue
        flag = "--replace-own" if line.slug in replace else "--prune-stale"
        log = logs / f"load_{mode}_{make}_{line.slug}.log"
        code = run([PY, "scripts/load_us_tech_facts.py", make, line.slug, "--db", str(db), flag], log)
        text = log.read_text(encoding="utf-8", errors="replace")
        result = parse_summary(text)
        summary["lines"][line.key] = {"flag": flag, "exit": code, **{k: result.get(k) for k in ("counts", "generations", "conflicts", "existing_vs_new")}}
        print(line.key, flag, "exit", code, json.dumps(result.get("counts", {}))[:300], flush=True)
        if code:
            summary["stopped_at"] = line.key
            break
    with sqlite3.connect(db) as con:
        summary["quick_check"] = con.execute("pragma quick_check").fetchone()[0]
        summary["foreign_key_violations"] = len(con.execute("pragma foreign_key_check").fetchall())
    summary["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    out = ROOT / f"data_work/{make}/staging/load_pass_{mode}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print("quick_check", summary["quick_check"], "fk violations", summary["foreign_key_violations"])
    return 1 if summary.get("stopped_at") or summary["quick_check"] != "ok" else 0


def main(argv) -> int:
    make, step = argv[0], argv[1]
    if step == "build":
        return build(make)
    if step in ("rehearse", "live"):
        return load(make, "live" if step == "live" else "rehearsal")
    raise SystemExit(f"unknown step {step}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

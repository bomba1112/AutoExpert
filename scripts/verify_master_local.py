"""Reproducible local verification. No provider requests, deployment or secret output."""

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import get_settings  # noqa: E402

OUT = ROOT / "deliverables/MasterLocal"
OUT.mkdir(parents=True, exist_ok=True)
checks = {}


def run(label, command, env=None):
    result = subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    (OUT / (label + ".txt")).write_text(result.stdout, encoding="utf-8")
    checks[label] = {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "exit_code": result.returncode,
    }
    print(label, checks[label]["status"], flush=True)
    return result


run("pytest", [sys.executable, "-m", "pytest", "-q"])
run("ruff", [sys.executable, "-m", "ruff", "check", "backend", "apps/android_demo", "scripts"])
node = shutil.which("node") or str(
    Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
)
run("javascript-regression", [node, "--test", "apps/android_demo/test_research_hotfix.mjs"])
js_checks = []
for path in sorted((ROOT / "apps/web_preview").glob("*.js")):
    r = subprocess.run([node, "--check", str(path)], capture_output=True)
    js_checks.append({"file": str(path.relative_to(ROOT)), "pass": r.returncode == 0})
checks["javascript-syntax"] = {
    "status": "PASS" if all(r["pass"] for r in js_checks) else "FAIL",
    "files": js_checks,
}

# Frozen migrations compile for PostgreSQL without contacting a server.
pg_env = dict(
    os.environ, AUTOEXPERT_DATABASE_URL="postgresql+psycopg://offline@localhost/autoexpert"
)
run(
    "postgresql-offline-migrations",
    [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head", "--sql"],
    pg_env,
)

stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
fresh = ROOT / ".runtime" / ("migration-qa-" + stamp + ".sqlite3")
sqlite_env = dict(os.environ, AUTOEXPERT_DATABASE_URL="sqlite:///" + fresh.as_posix())
run(
    "fresh-sqlite-migrations",
    [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
    sqlite_env,
)
run(
    "sqlite-downgrade-roundtrip",
    [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "downgrade", "e642d1e823cd"],
    sqlite_env,
)
run(
    "sqlite-reupgrade-roundtrip",
    [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
    sqlite_env,
)

baseline = ROOT / ".backups/before-master-20260918-231040.sqlite3"
current = ROOT / get_settings().database_url.removeprefix("sqlite:///")
preservation = {}
with sqlite3.connect(baseline) as before, sqlite3.connect(current) as after:
    before.row_factory = after.row_factory = sqlite3.Row
    tables = [
        r[0]
        for r in before.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if r[0] != "alembic_version"
    ]
    for table in tables:
        columns = [r[1] for r in before.execute(f'PRAGMA table_info("{table}")')]
        pk = [r[1] for r in before.execute(f'PRAGMA table_info("{table}")') if r[5]]
        if not pk:
            continue
        changes, removed, canonical = 0, 0, 0
        for row in before.execute(f'SELECT * FROM "{table}"'):
            where = " AND ".join(f'"{column}"=?' for column in pk)
            newer = after.execute(
                f'SELECT * FROM "{table}" WHERE {where}', tuple(row[column] for column in pk)
            ).fetchone()
            if newer is None:
                removed += 1
                continue
            changed = {c for c in columns if row[c] != newer[c]}
            if (
                table in {"vehicle_makes", "vehicle_models"}
                and changed <= {"is_demo", "updated_at"}
                and changed
            ):
                canonical += 1
            elif changed:
                changes += 1
        preservation[table] = {
            "removed_rows": removed,
            "changed_historical_rows": changes,
            "canonical_names_confirmed_by_official_source": canonical,
        }
    checks["historical-preservation"] = {
        "status": "PASS"
        if not any(r["removed_rows"] or r["changed_historical_rows"] for r in preservation.values())
        else "REVIEW",
        "tables": preservation,
    }
    checks["database-integrity"] = {
        "status": "PASS"
        if after.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        and not after.execute("PRAGMA foreign_key_check").fetchall()
        else "FAIL"
    }

apk = ROOT / "deliverables/AutoExpert_2_0_Alpha_0.8.0.apk"
checks["apk"] = {
    "exists": apk.is_file(),
    "sha256": hashlib.sha256(apk.read_bytes()).hexdigest() if apk.is_file() else None,
}
checks["physical-device"] = {"status": "DEFERRED_BY_OWNER", "new_apk_installed_or_tested": False}
checks["hetzner"] = {"status": "DEFERRED_BY_OWNER", "deployed": False}
checks["postgresql-runtime"] = {"status": "NOT_RUN_DOCKER_UNAVAILABLE"}
(OUT / "verification.json").write_text(
    json.dumps(
        {"at": datetime.now(UTC).isoformat(), "checks": checks}, ensure_ascii=False, indent=2
    ),
    encoding="utf-8",
)
print("Verification saved; historical data:", checks["historical-preservation"]["status"])
if any(check.get("status") in {"FAIL", "REVIEW"} for check in checks.values()):
    raise SystemExit(1)

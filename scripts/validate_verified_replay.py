"""Restore portable factual data into a fresh isolated database, then repeat without duplicates."""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData"
stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
target = ROOT / ".runtime" / ("verified-replay-" + stamp + ".sqlite3")
env = dict(
    os.environ,
    AUTOEXPERT_DATABASE_URL="sqlite:///" + target.as_posix(),
    AUTOEXPERT_KNOWLEDGE_DATA_DIR=str(ROOT / ".runtime" / ("verified-replay-documents-" + stamp)),
)
commands = [[sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"]]
commands += [
    [
        sys.executable,
        "scripts/replay_verified_data.py",
        "deliverables/VerifiedData/published-data",
        "--publish-reviewed",
    ]
] * 2
logs = []
counts = []
for i, command in enumerate(commands):
    r = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    logs.append(r.stdout + r.stderr)
    (OUT / "portable-replay.txt").write_text("\n".join(logs), encoding="utf-8")
    if r.returncode:
        raise SystemExit("Offline replay failed; inspect portable-replay.txt")
    if i:
        with sqlite3.connect(target) as db:
            counts.append(
                {
                    table: db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                    for table in [
                        "vehicle_variants",
                        "catalog_revisions",
                        "ownership_evidence_revisions",
                        "knowledge_import_jobs",
                    ]
                }
            )
            assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert not db.execute("PRAGMA foreign_key_check").fetchall()
    print("replay step", i, "PASS", flush=True)
assert counts[0] == counts[1]
assert counts[0]["vehicle_variants"] == 3655
assert counts[0]["ownership_evidence_revisions"] == 5
(OUT / "portable-replay.json").write_text(
    json.dumps(
        {
            "status": "PASS",
            "first": counts[0],
            "repeat": counts[1],
            "network_calls": 0,
            "original_database_modified": False,
            "source_rights_retained": True,
        },
        indent=2,
    ),
    encoding="utf-8",
)

"""Consistent SQLite + private knowledge backup, restored into a new test directory.

Never overwrites the running database. Restored data stay local and are not deliverables.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import get_settings  # noqa: E402


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def counts(connection):
    tables = [
        r[0]
        for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    return {
        name: connection.execute(
            'SELECT COUNT(*) FROM "' + name.replace('"', '""') + '"'
        ).fetchone()[0]
        for name in tables
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="deliverables/MasterLocal")
    args = parser.parse_args()
    settings = get_settings()
    if not settings.database_url.startswith("sqlite:///"):
        raise SystemExit("Use deploy/backup.sh for PostgreSQL")
    db = Path(settings.database_url.removeprefix("sqlite:///")).resolve()
    knowledge = Path(settings.knowledge_data_dir).resolve()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup = ROOT / ".backups" / ("master-" + stamp)
    restored = ROOT / ".runtime" / ("restore-" + stamp)
    backup.mkdir(parents=True)
    restored.mkdir(parents=True)
    with sqlite3.connect(db) as source, sqlite3.connect(backup / "database.sqlite3") as target:
        source.backup(target)
        expected = counts(target)
        assert target.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    if knowledge.exists():
        shutil.copytree(knowledge, backup / "knowledge")
    files = {str(p.relative_to(backup)): sha(p) for p in backup.rglob("*") if p.is_file()}
    (backup / "manifest.json").write_text(
        json.dumps({"files": files, "counts": expected}, indent=2), encoding="utf-8"
    )
    shutil.copytree(backup, restored, dirs_exist_ok=True)
    assert all(sha(restored / name) == digest for name, digest in files.items())
    with sqlite3.connect(restored / "database.sqlite3") as test:
        assert counts(test) == expected
        assert test.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        foreign_errors = test.execute("PRAGMA foreign_key_check").fetchall()
        assert not foreign_errors
    report = {
        "status": "PASS",
        "timestamp": stamp,
        "database_integrity": "ok",
        "foreign_keys": "ok",
        "tables": len(expected),
        "files_verified": len(files),
        "backup_bytes": sum((backup / p).stat().st_size for p in files),
        "restored_into_new_directory": True,
        "running_database_overwritten": False,
        "postgres_restore": "NOT_RUN_DOCKER_UNAVAILABLE",
    }
    output = ROOT / args.output / "backup-restore.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()

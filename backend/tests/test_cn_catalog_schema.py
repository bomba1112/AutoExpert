"""f094: CN catalogue columns — SQLite round trip, guarded downgrade, PostgreSQL DDL."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from app.models.catalog import VehicleVariant
from app.models.enums import ScopeLevel
from app.models.evidence import KnownIssue, TechnicalEvidence

ROOT = Path(__file__).resolve().parents[2]


def alembic(database_url: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    environment = {
        **os.environ,
        "AUTOEXPERT_DATABASE_URL": database_url,
        "AUTOEXPERT_ENVIRONMENT": "test",
    }
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ROOT / "backend/alembic.ini"), *args],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        timeout=120,
    )


def columns(connection: sqlite3.Connection, table: str) -> dict[str, bool]:
    """name -> NOT NULL"""
    return {row[1]: bool(row[3]) for row in connection.execute(f"PRAGMA table_info({table})")}


def test_f094_upgrade_downgrade_round_trip_on_sqlite(tmp_path):
    database = tmp_path / "f094.db"
    url = f"sqlite:///{database.as_posix()}"
    result = alembic(url, "upgrade", "head", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    with sqlite3.connect(database) as connection:
        variant = columns(connection, "vehicle_variants")
        assert {"powertrain_type", "battery_kwh"} <= set(variant)
        assert "hybrid_system_key" in columns(connection, "technical_evidence")
        issue = columns(connection, "known_issues")
        assert "hybrid_system_key" in issue
        assert issue["severity"] is False

    result = alembic(url, "downgrade", "f093_owners_club", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    with sqlite3.connect(database) as connection:
        assert "battery_kwh" not in columns(connection, "vehicle_variants")
        assert columns(connection, "known_issues")["severity"] is True

    result = alembic(url, "upgrade", "head", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_f094_downgrade_refused_while_cn_rows_exist(tmp_path):
    database = tmp_path / "f094_guard.db"
    url = f"sqlite:///{database.as_posix()}"
    assert alembic(url, "upgrade", "head", cwd=tmp_path).returncode == 0
    now = "2026-10-04 00:00:00"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO vehicle_makes (id, name, normalized_name, is_demo, created_at, updated_at)"
            " VALUES ('mk', 'BYD', 'byd', 0, ?, ?)",
            (now, now),
        )
        connection.execute(
            "INSERT INTO vehicle_models (id, make_id, name, normalized_name, is_demo, created_at,"
            " updated_at) VALUES ('md', 'mk', 'Qin Plus', 'qin plus', 0, ?, ?)",
            (now, now),
        )
        connection.execute(
            "INSERT INTO vehicle_generations (id, model_id, name, is_demo, created_at, updated_at)"
            " VALUES ('gn', 'md', 'CN', 0, ?, ?)",
            (now, now),
        )
        connection.execute(
            "INSERT INTO vehicle_variants (id, generation_id, market, name, specifications,"
            " is_demo, data_origin, editorial_locked, battery_kwh, created_at, updated_at)"
            " VALUES ('vr', 'gn', 'CN', 'x', '{}', 0, 'REAL', 0, 18.32, ?, ?)",
            (now, now),
        )
    result = alembic(url, "downgrade", "f093_owners_club", cwd=tmp_path)
    assert result.returncode != 0
    assert "f094 downgrade refused" in result.stdout + result.stderr
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (
            "f094_cn_catalog",
        )


def test_f094_postgresql_ddl_is_plain_alter(tmp_path):
    result = alembic(
        "postgresql://user:password@localhost/autoexpert",
        "upgrade",
        "f093_owners_club:f094_cn_catalog",
        "--sql",
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    sql = result.stdout
    assert "ALTER TABLE vehicle_variants ADD COLUMN powertrain_type VARCHAR(16)" in sql
    assert "ALTER TABLE vehicle_variants ADD COLUMN battery_kwh NUMERIC(6, 2)" in sql
    assert "ALTER TABLE technical_evidence ADD COLUMN hybrid_system_key VARCHAR(40)" in sql
    assert "ALTER TABLE known_issues ADD COLUMN hybrid_system_key VARCHAR(40)" in sql
    assert "ALTER TABLE known_issues ALTER COLUMN severity DROP NOT NULL" in sql
    # no table rebuild (that is SQLite only) and no enum type changes
    assert "CREATE TABLE" not in sql.replace("CREATE TABLE alembic_version", "")
    assert "CREATE TYPE" not in sql


def test_f094_models_match_migration():
    assert VehicleVariant.__table__.c.powertrain_type.nullable
    assert VehicleVariant.__table__.c.battery_kwh.nullable
    assert TechnicalEvidence.__table__.c.hybrid_system_key.nullable
    assert KnownIssue.__table__.c.hybrid_system_key.nullable
    assert KnownIssue.__table__.c.severity.nullable
    # stored as VARCHAR(20) without CHECK constraint; the new member fits
    assert len(ScopeLevel.HYBRID_SYSTEM.value) <= 20

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parents[2]


def run_preview_twice(tmp_path, cwd, extra_env):
    database = tmp_path / "preview.db"
    environment = {
        **os.environ,
        # Preserve an explicitly configured dependency path when the installed
        # interpreter loads project packages from an existing virtual environment.
        "PYTHONPATH": os.pathsep.join(
            filter(None, [str(ROOT / "backend"), os.environ.get("PYTHONPATH")])
        ),
        "AUTOEXPERT_DATABASE_URL": f"sqlite:///{database.as_posix()}",
        "AUTOEXPERT_ENVIRONMENT": "test",
        "AUTOEXPERT_DEMO_MODE": "true",
        **extra_env,
    }
    # Exercise the real entry point and migration files; only the blocking server is stubbed.
    script = """
from pathlib import Path
from unittest.mock import patch
from app.run_preview import main
with patch('app.run_preview.uvicorn.run') as server:
    main()
    assert Path.cwd() == Path(server.call_args.kwargs['app_dir']).parent
    assert server.call_args.args == ('app.main:app',)
"""
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=cwd,
            env=environment,
            text=True,
            capture_output=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    configuration = Config(str(ROOT / "backend" / "alembic.ini"))
    head = ScriptDirectory.from_config(configuration).get_current_head()
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (head,)
        return connection.execute("SELECT COUNT(*) FROM vehicle_knowledge_profiles").fetchone()[0]


@pytest.mark.parametrize("working_directory", ["root", "backend", "unrelated"])
def test_preview_migrates_and_seeds_from_any_directory(tmp_path, working_directory):
    cwd = {"root": ROOT, "backend": ROOT / "backend", "unrelated": tmp_path}[working_directory]
    count = run_preview_twice(tmp_path, cwd, {"AUTOEXPERT_SEED_DEMO_ON_START": "true"})
    assert count > 0


def test_preview_does_not_seed_demo_rows_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("AUTOEXPERT_SEED_DEMO_ON_START", raising=False)
    assert run_preview_twice(tmp_path, ROOT, {}) == 0


def test_alembic_config_paths_are_relative_to_config_file(tmp_path):
    environment = {
        **os.environ,
        "AUTOEXPERT_DATABASE_URL": f"sqlite:///{(tmp_path / 'migrations.db').as_posix()}",
        "AUTOEXPERT_ENVIRONMENT": "test",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ROOT / "backend/alembic.ini"),
            "upgrade",
            "head",
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "origin",
    [
        "https://appassets.autoexpert.local",
        "http://localhost:3000",
        "http://localhost:8080",
    ],
)
def test_preview_cors_allows_android_and_developer_origins(client, origin):
    response = client.options(
        "/api/v1/research/jobs",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": (
                "authorization,content-type,x-autoexpert-simulate-paywall"
            ),
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


def test_preview_cors_rejects_unlisted_origin(client):
    response = client.options(
        "/api/v1/research/jobs",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

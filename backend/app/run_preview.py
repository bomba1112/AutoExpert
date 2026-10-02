from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config


def _prepare_database(project_root: Path) -> None:
    # Import only after ``main`` changes to the repository root. Relative SQLite URLs
    # must resolve to the same file for Alembic and SQLAlchemy's application engine.
    from alembic.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from sqlalchemy import create_engine

    from app.core.config import get_settings
    from app.db.seed_demo import seed_demo
    from app.db.session import SessionLocal

    alembic_config = Config(str(project_root / "backend" / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(project_root / "backend" / "alembic"))
    url = get_settings().database_url
    engine = create_engine(url)
    with engine.connect() as connection:
        pending = (
            MigrationContext.configure(connection).get_current_revision()
            != ScriptDirectory.from_config(alembic_config).get_current_head()
        )
    engine.dispose()
    if pending and url.startswith("sqlite:///"):
        database = Path(url.removeprefix("sqlite:///"))
        if database.exists():
            backup = (
                project_root
                / ".backups"
                / ("before-migration-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".sqlite3")
            )
            backup.parent.mkdir(exist_ok=True)
            with sqlite3.connect(database) as source, sqlite3.connect(backup) as target:
                source.backup(target)
    command.upgrade(alembic_config, "head")
    if get_settings().demo_mode:
        with SessionLocal() as session:
            seed_demo(session)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Auto Expert phone Web Preview")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    os.chdir(project_root)
    _prepare_database(project_root)
    uvicorn.run(
        "app.main:app",
        app_dir=str(project_root / "backend"),
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

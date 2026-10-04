"""Chinese configuration catalogue: validate, rehearse and load (data_work/cn/staging).

  build      validate the snapshot (MANIFEST sha256, model map, components) -> build_report.json
  rehearse   copy the live database to C:\\AutoExpertData\\work\\rehearsal_cn.db, migrate the copy
             to head, load, load again (must change nothing), check: production-visible US rows
             before/after, inherited issues vs the catalogue, quick_check, foreign keys and (when
             the matcher exists) the turbo.az listing regression -> load_rehearsal.json
  live       owner decision required (--owner-approved): rolling backup of the live database
             to C:\\AutoExpertBackups, migrate it to head, load, the same checks -> load_live.json

The live database is the STAGE6_1 one (this worktree has none); pass --live-db to override.
Alembic always gets an absolute database URL (a relative one creates a stray empty file).

  .venv/Scripts/python.exe scripts/load_cn_catalog.py build|rehearse
  .venv/Scripts/python.exe scripts/load_cn_catalog.py live --owner-approved
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import models  # noqa: E402,F401
from app.models.catalog import VehicleVariant  # noqa: E402
from app.models.evidence import TechnicalEvidence  # noqa: E402
from app.services import cn_catalog  # noqa: E402
from app.services.cn_catalog_load import CnLoader, db_counts, read_staging, validate  # noqa: E402
from sqlalchemy import create_engine, func, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

CN = ROOT / "data_work" / "cn"
STAGING = CN / "staging"
MODEL_MAP = CN / "model_map.json"
LIVE = Path(r"C:\Users\jalil\OneDrive\Desktop\AUTO_EXPERT\STAGE6_1\autoexpert.db")
REHEARSAL = Path(r"C:\AutoExpertData\work\rehearsal_cn.db")
BACKUP = Path(r"C:\AutoExpertBackups\autoexpert.db.backup_cn_latest")


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def copy_database(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    src, dst = sqlite3.connect(source), sqlite3.connect(target)
    src.backup(dst)
    dst.close()
    src.close()


MAIN_VERSIONS = LIVE.parent / "backend" / "alembic" / "versions"
EXTRA_VERSIONS = Path(r"C:\AutoExpertData\work\alembic_cn_extra")


def foreign_revisions(database: Path) -> list[Path]:
    """Revisions applied to the database that this branch does not have (another session's
    migration on master, e.g. f090_garage): their files come from the STAGE6_1 working tree so
    that alembic can walk the graph; ours is then applied as a second head."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ROOT / "backend" / "alembic.ini")))
    with sqlite3.connect(database) as connection:
        applied = [row[0] for row in connection.execute("SELECT version_num FROM alembic_version")]
    missing = []
    for revision in applied:
        try:
            script.get_revision(revision)
        except Exception as error:  # noqa: BLE001 - unknown to this branch
            path = MAIN_VERSIONS / f"{revision}.py"
            if not path.exists():
                raise SystemExit(
                    f"revision {revision} applied to {database} but no file at {path}"
                ) from error
            missing.append(path)
    return missing


def migrate(database: Path) -> dict:
    url = f"sqlite:///{database.resolve().as_posix()}"
    extra = foreign_revisions(database)
    locations = [(ROOT / "backend" / "alembic" / "versions").as_posix()]
    if extra:
        import shutil

        if EXTRA_VERSIONS.exists():
            shutil.rmtree(EXTRA_VERSIONS)
        EXTRA_VERSIONS.mkdir(parents=True)
        for path in extra:
            shutil.copyfile(path, EXTRA_VERSIONS / path.name)
        locations.append(EXTRA_VERSIONS.as_posix())
    code = "\n".join(
        [
            "from alembic import command",
            "from alembic.config import Config",
            f"cfg = Config({str(ROOT / 'backend' / 'alembic.ini')!r})",
            f"cfg.set_main_option('version_locations', {os.pathsep.join(locations)!r})",
            "command.upgrade(cfg, 'heads')",
        ]
    )
    env = {**os.environ, "AUTOEXPERT_DATABASE_URL": url, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT / "backend", env=env, text=True, capture_output=True
    )
    if result.returncode:
        raise SystemExit("alembic upgrade failed:\n" + result.stdout + result.stderr)
    with sqlite3.connect(database) as connection:
        heads = sorted(r[0] for r in connection.execute("SELECT version_num FROM alembic_version"))
    return {"heads": heads, "foreign_revisions": [p.name for p in extra]}


def session_for(database: Path):
    engine = create_engine(f"sqlite:///{database.resolve().as_posix()}")
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()


def visible_us(db) -> dict:
    from app.services.listing_intake import production_visible_us_rows

    rows = production_visible_us_rows(db)
    return {
        "count": len(rows),
        "variant_ids_sha": __import__("hashlib")
        .sha256("\n".join(sorted(v.id for v, _ in rows)).encode())
        .hexdigest(),
    }


def us_configurations(db) -> dict:
    query = (
        select(func.count())
        .select_from(TechnicalEvidence)
        .where(TechnicalEvidence.fact_key == "configuration", TechnicalEvidence.market == "US")
    )
    return {"us_configuration_rows": db.scalar(query)}


def issues_check(db, staging) -> dict:
    mismatched = []
    for slug, record in staging.records.items():
        variant = db.scalar(
            select(VehicleVariant).where(VehicleVariant.catalog_key == f"cn:{slug}")
        )
        got = [
            (i["text"], i["source"], i["origin"]) for i in cn_catalog.resolved_issues(db, variant)
        ]
        want = [
            (i["text"], i["source"], i["origin"]) for i in record.get("known_issues_resolved") or []
        ]
        if got != want:
            mismatched.append(slug)
    return {"records": len(staging.records), "mismatched": mismatched}


def listing_regression(db) -> dict | None:
    try:
        from app.services import cn_listing_match
    except ImportError:
        return None
    return cn_listing_match.regression(db, Path(r"C:\Users\jalil\samr\turbo_specs.json"), STAGING)


def integrity(database: Path) -> dict:
    with sqlite3.connect(database) as connection:
        return {
            "quick_check": connection.execute("pragma quick_check").fetchone()[0],
            "foreign_key_violations": len(
                connection.execute("pragma foreign_key_check").fetchall()
            ),
        }


def build() -> int:
    staging = read_staging(STAGING, MODEL_MAP)
    errors = validate(staging)
    report = {
        "made_at": now(),
        "samr_commit": staging.manifest["samr_commit"],
        "records": len(staging.records),
        "components": len(staging.components),
        "errors": errors,
    }
    (CN / "build_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False)[:600])
    return 1 if errors else 0


def load(database: Path, mode: str) -> int:
    staging = read_staging(STAGING, MODEL_MAP)
    errors = validate(staging)
    if errors:
        print("staging invalid:", errors[:10])
        return 1
    summary = {
        "mode": mode,
        "database": str(database),
        "started_at": now(),
        "samr_commit": staging.manifest["samr_commit"],
    }
    with sqlite3.connect(database) as connection:
        summary["alembic_before"] = sorted(
            r[0] for r in connection.execute("SELECT version_num FROM alembic_version")
        )
    summary["alembic_after"] = migrate(database)
    db = session_for(database)
    summary["before"] = {
        "production_visible_us": visible_us(db),
        **us_configurations(db),
        "cn": db_counts(db),
    }
    report = CnLoader(db, staging).load()
    db.commit()
    summary["load"] = report.as_dict()
    again = CnLoader(db, staging).load()
    db.commit()
    summary["second_load"] = {
        "counts": dict(again.counts),
        "conflicts": len(again.conflicts),
        "stale": len(again.stale),
    }
    db.expire_all()
    summary["after"] = {
        "production_visible_us": visible_us(db),
        **us_configurations(db),
        "cn": db_counts(db),
    }
    summary["inherited_issues"] = issues_check(db, staging)
    summary["listing_regression"] = listing_regression(db)
    db.close()
    summary["integrity"] = integrity(database)
    summary["finished_at"] = now()
    ok = (
        summary["before"]["production_visible_us"] == summary["after"]["production_visible_us"]
        and summary["before"]["us_configuration_rows"] == summary["after"]["us_configuration_rows"]
        and not report.conflicts
        and not any(k.endswith("_new") for k in again.counts)
        and not again.conflicts
        and not summary["inherited_issues"]["mismatched"]
        and summary["integrity"]["quick_check"] == "ok"
        and summary["integrity"]["foreign_key_violations"] == 0
    )
    summary["ok"] = ok
    out = CN / f"load_{mode}.json"
    out.write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8"
    )
    brief = {
        k: summary[k]
        for k in ("alembic_before", "alembic_after", "before", "after", "integrity", "ok")
    }
    print(json.dumps(brief, ensure_ascii=False, indent=1, default=str))
    print("load counts", json.dumps(summary["load"]["counts"], ensure_ascii=False))
    print("second load", json.dumps(summary["second_load"], ensure_ascii=False))
    print("inherited issues mismatched:", len(summary["inherited_issues"]["mismatched"]))
    print("report ->", out.relative_to(ROOT))
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["build", "rehearse", "live"])
    parser.add_argument("--live-db", type=Path, default=LIVE)
    parser.add_argument("--owner-approved", action="store_true")
    args = parser.parse_args(argv)
    if args.mode == "build":
        return build()
    if args.mode == "rehearse":
        copy_database(args.live_db, REHEARSAL)
        print("rehearsal copy", REHEARSAL)
        return load(REHEARSAL, "rehearsal")
    if not args.owner_approved:
        print("live load needs the owner's decision: --owner-approved")
        return 2
    copy_database(args.live_db, BACKUP)
    print("backup", BACKUP)
    return load(args.live_db, "live")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

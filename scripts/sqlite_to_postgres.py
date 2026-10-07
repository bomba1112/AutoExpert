# ruff: noqa: E501
"""Transfer the Auto Expert database from SQLite to PostgreSQL (deploy prompt, stage A).

The SQLite file is opened read-only and never changed. The PostgreSQL database must already be at
the Alembic head (alembic upgrade head) and empty; --truncate empties it first.

Every table present on both sides is copied in foreign-key order; values are converted by the
PostgreSQL column types (booleans, timestamps, dates, JSON, numerics). Sequences are moved past
the highest id. Then the check: rows per table must be equal, and the content hash of the key
tables (technical_evidence, known_issues, maintenance_schedule_items, content_translations, users,
garage_*, club_*) must be equal on both sides.

    python scripts/sqlite_to_postgres.py --sqlite autoexpert.db --pg postgresql+psycopg://user@host:5432/db [--truncate] [--verify-only]

Text containing NUL characters cannot be stored by PostgreSQL: such characters are reported, never
silently dropped; --strip-nul removes them (the report lists every affected table / column).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sqlite3
import sys
import time
from decimal import Decimal

from sqlalchemy import MetaData, create_engine, insert, select, text
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.sql import sqltypes

KEY_TABLES = ("technical_evidence", "known_issues", "maintenance_schedule_items", "content_translations", "users")
KEY_PREFIXES = ("garage_", "club_")
BATCH = 2000
# migrations that change PostgreSQL only (SQLite stays at the previous head): revision -> SQLite head
PG_ONLY = {"f095_row_order": "f094_subscriptions"}


def convert(value, column, nul_report: dict, strip_nul: bool):
    if value is None:
        return None
    t = column.type
    if isinstance(t, sqltypes.Boolean):
        return bool(int(value)) if not isinstance(value, str) else value.strip().lower() in ("1", "true", "t")
    if isinstance(t, sqltypes.DateTime):
        if isinstance(value, (int, float)):
            return dt.datetime.fromtimestamp(value, dt.UTC)
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if t.timezone and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.UTC)  # the application writes UTC
        return parsed
    if isinstance(t, sqltypes.Date):
        return dt.date.fromisoformat(str(value)[:10])
    if isinstance(t, sqltypes.JSON):
        data = json.loads(value) if isinstance(value, str) else value
        return data
    if isinstance(t, sqltypes.Numeric) and not isinstance(t, (sqltypes.Integer, sqltypes.Float)):
        return Decimal(str(value))
    if isinstance(t, sqltypes.Integer):
        return int(value)
    if isinstance(t, sqltypes.Float):
        return float(value)
    if isinstance(t, (sqltypes.LargeBinary, pg.BYTEA)):
        return bytes(value)
    if isinstance(value, str) and "\x00" in value:
        nul_report[f"{column.table.name}.{column.name}"] = nul_report.get(f"{column.table.name}.{column.name}", 0) + 1
        if strip_nul:
            return value.replace("\x00", "")
    return value


def canonical(value) -> str:
    """One text form for a value read from either side (for the content hash)."""
    if value is None:
        return "∅"
    if isinstance(value, bool):
        return "T" if value else "F"
    if isinstance(value, dt.datetime):
        if value.tzinfo is not None:
            value = value.astimezone(dt.UTC).replace(tzinfo=None)
        return value.isoformat()
    if isinstance(value, (dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    if isinstance(value, (bytes, memoryview)):
        return hashlib.sha256(bytes(value)).hexdigest()
    return str(getattr(value, "value", value))


def sqlite_rows(src: sqlite3.Connection, table, order: list[str]):
    cols = [c.name for c in table.columns]
    # row_order (PostgreSQL only, migration f095) carries SQLite's insertion order: the rowid
    quoted = ", ".join("rowid" if c == "row_order" else f'"{c}"' for c in cols)
    order_sql = ", ".join(f'"{c}"' for c in order) if order else "rowid"
    cursor = src.execute(f'SELECT {quoted} FROM "{table.name}" ORDER BY {order_sql}')
    while True:
        batch = cursor.fetchmany(BATCH)
        if not batch:
            return
        yield cols, batch


def table_hash_sqlite(src, table, order, strip_nul) -> str:
    h = hashlib.sha256()
    dummy: dict = {}
    for cols, batch in sqlite_rows(src, table, order):
        for row in batch:
            values = [convert(v, table.c[c], dummy, strip_nul) for c, v in zip(cols, row, strict=True)]
            h.update("\x1f".join(canonical(v) for v in values).encode("utf-8"))
            h.update(b"\x1e")
    return h.hexdigest()


def table_hash_pg(conn, table, order) -> str:
    h = hashlib.sha256()
    stmt = select(*table.columns).order_by(*[table.c[c] for c in order]) if order else select(*table.columns)
    for row in conn.execution_options(yield_per=BATCH).execute(stmt):
        h.update("\x1f".join(canonical(v) for v in row).encode("utf-8"))
        h.update(b"\x1e")
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", required=True)
    parser.add_argument("--pg", required=True)
    parser.add_argument("--truncate", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--strip-nul", action="store_true")
    parser.add_argument("--report", default=None, help="write the check as JSON here")
    args = parser.parse_args()

    src = sqlite3.connect(f"file:{args.sqlite}?mode=ro", uri=True)  # read-only: the working base is never changed
    sqlite_tables = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    engine = create_engine(args.pg)
    meta = MetaData()
    meta.reflect(engine)
    tables = [t for t in meta.sorted_tables if t.name in sqlite_tables and t.name != "alembic_version"]
    missing = sorted(sqlite_tables - {t.name for t in meta.sorted_tables} - {"alembic_version"})
    if missing:
        print(f"tables only in SQLite (not copied): {missing}")
        return 2
    sqlite_head = src.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    with engine.connect() as conn:
        pg_head = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    if sqlite_head != pg_head and PG_ONLY.get(pg_head) != sqlite_head:
        print(f"Alembic heads differ: SQLite {sqlite_head}, PostgreSQL {pg_head}")
        return 2

    def order_of(table):
        return [c.name for c in table.primary_key.columns] or [c.name for c in table.columns]

    nul_report: dict = {}
    started = time.time()
    if not args.verify_only:
        with engine.begin() as conn:
            filled = [t.name for t in tables if conn.execute(select(text("1")).select_from(t).limit(1)).first()]
            if filled and not args.truncate:
                print(f"PostgreSQL tables are not empty: {filled[:10]} (use --truncate)")
                return 2
            if filled:
                conn.execute(text("TRUNCATE " + ", ".join(f'"{t.name}"' for t in tables) + " CASCADE"))
            conn.execute(text("SET session_replication_role = replica"))  # order is kept anyway; cycles are safe
            for table in tables:
                count = 0
                for cols, batch in sqlite_rows(src, table, order_of(table)):
                    rows = [{c: convert(v, table.c[c], nul_report, args.strip_nul) for c, v in zip(cols, row, strict=True)} for row in batch]
                    conn.execute(insert(table), rows)
                    count += len(rows)
                print(f"{table.name}: {count}", flush=True)
            conn.execute(text("SET session_replication_role = origin"))
            # sequences past the highest id
            for table in tables:
                for column in table.columns:
                    default = str(column.server_default.arg) if column.server_default is not None else ""
                    if "nextval(" in default:
                        seq = default.split("'")[1]
                        conn.execute(text(f"SELECT setval('{seq}', COALESCE((SELECT MAX(\"{column.name}\") FROM \"{table.name}\"), 0) + 1, false)"))
        if nul_report and not args.strip_nul:
            print(f"NUL characters found (rerun with --strip-nul after review): {nul_report}")

    check = {"tables": {}, "hashes": {}, "nul": nul_report, "sqlite_head": sqlite_head}
    ok = True
    with engine.connect() as conn:
        for table in tables:
            a = src.execute(f'SELECT COUNT(*) FROM "{table.name}"').fetchone()[0]
            b = conn.execute(select(text("COUNT(*)")).select_from(table)).scalar()
            check["tables"][table.name] = {"sqlite": a, "postgres": b, "equal": a == b}
            ok &= a == b
        for table in tables:
            if table.name in KEY_TABLES or table.name.startswith(KEY_PREFIXES):
                order = order_of(table)
                ha, hb = table_hash_sqlite(src, table, order, args.strip_nul), table_hash_pg(conn, table, order)
                check["hashes"][table.name] = {"sqlite": ha[:16], "postgres": hb[:16], "equal": ha == hb}
                ok &= ha == hb
    check["ok"] = ok
    check["seconds"] = round(time.time() - started)
    bad = {k: v for k, v in check["tables"].items() if not v["equal"]}
    print(json.dumps({"ok": ok, "tables": len(check["tables"]), "rows": sum(v["postgres"] for v in check["tables"].values()),
                      "unequal_tables": bad, "hashes": {k: v["equal"] for k, v in check["hashes"].items()}, "seconds": check["seconds"]}, ensure_ascii=False))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(check, fh, ensure_ascii=False, indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

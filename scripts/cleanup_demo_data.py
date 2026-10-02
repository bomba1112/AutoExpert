"""Delete the demo data of groups A and B of data_work/DEMO_CLEANUP_PLAN.md (owner-approved).

Seeds are the rows marked is_demo=1 or data_origin='DEMO' in every table except the
country/region profiles (group C stays). Rows that reference a seed through a foreign key
are followed:
  - ON DELETE CASCADE children are deleted with their parent;
  - any other referencing row that is not itself marked as demo blocks the run
    (nothing is deleted, the blockers are printed).

All deleted rows are exported to a JSON archive first; the deletion runs in one
transaction with foreign keys enforced, followed by foreign_key_check and quick_check.

  .venv/Scripts/python.exe scripts/cleanup_demo_data.py --db <path> --dry-run
  .venv/Scripts/python.exe scripts/cleanup_demo_data.py --db <path> --archive <file.json>
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict

KEEP = {"country_profiles", "region_profiles"}  # group C: needed by the app
# Unmarked rows that are still demo artifacts and may go with their demo parent: mock
# development "payments" of seeded demo users for demo VIN checks. Real entitlements
# (any other provider or user) keep blocking the run.
DEMO_DEPENDENTS = {
    "vin_entitlements": (
        "provider = 'mock' and user_id in "
        "(select id from users where email like '%@demo.autoexpert.invalid')"
    ),
}


def tables(con):
    return [
        r[0]
        for r in con.execute("select name from sqlite_master where type='table'")
        if not r[0].startswith("sqlite_") and r[0] != "alembic_version"
    ]


def columns(con, table):
    return [r[1] for r in con.execute(f"pragma table_info('{table}')")]


def referencing(con):
    """parent table -> [(child table, child column, parent column, on_delete)]"""
    refs = defaultdict(list)
    for table in tables(con):
        for fk in con.execute(f"pragma foreign_key_list('{table}')"):
            refs[fk[2]].append((table, fk[3], fk[4], fk[6]))
    return refs


def plan(con):
    seeds: dict[str, set] = defaultdict(set)
    for table in tables(con):
        if table in KEEP:
            continue
        cols = columns(con, table)
        conds = [c for c in ("is_demo=1", "data_origin='DEMO'") if c.split("=")[0] in cols]
        if not conds or "id" not in cols:
            continue
        for (row_id,) in con.execute(f"select id from '{table}' where {' or '.join(conds)}"):
            seeds[table].add(row_id)
    refs = referencing(con)
    delete = {t: set(ids) for t, ids in seeds.items()}
    blockers = []
    queue = [(t, i) for t, ids in seeds.items() for i in ids]
    while queue:
        table, row_id = queue.pop()
        for child, child_col, parent_col, on_delete in refs.get(table, []):
            parent_value = con.execute(
                f"select {parent_col} from '{table}' where id=?", (row_id,)
            ).fetchone()
            if parent_value is None:
                continue
            child_cols = columns(con, child)
            key = "id" if "id" in child_cols else "rowid"
            for (child_id,) in con.execute(
                f"select {key} from '{child}' where {child_col}=?", (parent_value[0],)
            ):
                if child_id in delete.get(child, set()):
                    continue
                demo_dependent = child in DEMO_DEPENDENTS and con.execute(
                    f"select 1 from '{child}' where {key}=? and {DEMO_DEPENDENTS[child]}",
                    (child_id,),
                ).fetchone()
                if on_delete == "CASCADE" or demo_dependent:
                    delete.setdefault(child, set()).add(child_id)
                    queue.append((child, child_id))
                else:
                    blockers.append(
                        {"table": child, "id": child_id, "column": child_col, "references": f"{table}:{row_id}"}
                    )
    return delete, blockers


def order(con, delete):
    """Children before parents among the tables that have rows to delete."""
    refs = referencing(con)
    remaining, ordered = set(delete), []
    while remaining:
        ready = [
            t
            for t in remaining
            if not any(child in remaining and child != t for child, *_ in refs.get(t, []))
        ]
        if not ready:
            raise RuntimeError(f"FK cycle among {sorted(remaining)}")
        for t in sorted(ready):
            ordered.append(t)
            remaining.discard(t)
    return ordered


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--archive")
    args = parser.parse_args(argv)
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    con.execute("pragma foreign_keys=ON")
    delete, blockers = plan(con)
    counts = {t: len(ids) for t, ids in sorted(delete.items())}
    print(json.dumps({"delete": counts, "blockers": blockers}, ensure_ascii=False, indent=1))
    if blockers:
        print("BLOCKED: non-demo rows reference demo rows; nothing deleted")
        return 2
    if args.dry_run:
        return 0
    if not args.archive:
        print("--archive is required for a real run")
        return 2
    sequence = order(con, delete)
    archive = {}
    for table in sequence:
        key = "id" if "id" in columns(con, table) else "rowid"
        ids = sorted(delete[table])
        rows = []
        for start in range(0, len(ids), 500):
            chunk = ids[start : start + 500]
            marks = ",".join("?" * len(chunk))
            rows += [dict(r) for r in con.execute(f"select * from '{table}' where {key} in ({marks})", chunk)]
        archive[table] = rows
    with open(args.archive, "w", encoding="utf-8") as handle:
        json.dump({"order": sequence, "rows": archive}, handle, ensure_ascii=False, indent=1, default=str)
    try:
        con.execute("begin")
        for table in sequence:
            key = "id" if "id" in columns(con, table) else "rowid"
            ids = sorted(delete[table])
            for start in range(0, len(ids), 500):
                chunk = ids[start : start + 500]
                marks = ",".join("?" * len(chunk))
                con.execute(f"delete from '{table}' where {key} in ({marks})", chunk)
        violations = con.execute("pragma foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"foreign_key_check: {[tuple(v) for v in violations][:10]}")
        con.execute("commit")
    except Exception:
        con.execute("rollback")
        raise
    quick = con.execute("pragma quick_check").fetchone()[0]
    left = {}
    for table in tables(con):
        cols = columns(con, table)
        conds = [c for c in ("is_demo=1", "data_origin='DEMO'") if c.split("=")[0] in cols]
        if conds:
            n = con.execute(f"select count(*) from '{table}' where {' or '.join(conds)}").fetchone()[0]
            if n:
                left[table] = n
    print(json.dumps({"deleted": counts, "order": sequence, "quick_check": quick, "demo_rows_left": left}, indent=1))
    return 0 if quick == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())

# ruff: noqa: E501
"""Insertion order of a data table on SQLite and PostgreSQL (deploy prompt, stage A).

Code that keeps "the first" of equal rows must read them in a stated order, not in whatever order
the database returns: SQLite's rowid, PostgreSQL's row_order (migration f095, filled from the
SQLite rowid by scripts/sqlite_to_postgres.py). Tables without row_order fall back to the id.
"""

from __future__ import annotations

from sqlalchemy import literal_column

ORDERED_TABLES = {"technical_evidence", "known_issues", "maintenance_schedule_items", "source_records",
                  "commercial_fact_claims", "vehicle_variants", "catalog_revisions", "content_translations"}


def insertion_order(db, model):
    table = model.__tablename__
    dialect = db.get_bind().dialect.name
    if dialect == "sqlite":
        return literal_column(f"{table}.rowid")
    if table in ORDERED_TABLES:
        return literal_column(f"{table}.row_order")
    return model.__table__.c.id


def add_row_order(connection) -> None:
    """The PostgreSQL row_order columns of migration f095, for schemas built with create_all (tests)."""
    from sqlalchemy import text

    for table in sorted(ORDERED_TABLES):
        connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS row_order BIGSERIAL'))

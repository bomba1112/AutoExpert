"""Insertion order on PostgreSQL (deploy prompt, stage A).

The card builder (app.services.us_tech_facts) keeps the first of equal rows, so it reads the data
tables in insertion order: SQLite's rowid; on PostgreSQL there is no rowid, so these tables get
row_order (a bigserial; the SQLite -> PostgreSQL transfer fills it with the SQLite rowid, new rows
take the next value). SQLite is not changed by this migration.
"""

from alembic import op

revision = "f095_row_order"
down_revision = "f094_subscriptions"
branch_labels = depends_on = None

TABLES = ("technical_evidence", "known_issues", "maintenance_schedule_items", "source_records",
          "commercial_fact_claims", "vehicle_variants", "catalog_revisions", "content_translations")


def upgrade():
    if op.get_bind().dialect.name != "postgresql":
        return
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ADD COLUMN row_order BIGSERIAL')
        op.execute(f'CREATE INDEX "ix_{table}_row_order" ON "{table}" (row_order)')


def downgrade():
    if op.get_bind().dialect.name != "postgresql":
        return
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" DROP COLUMN row_order')

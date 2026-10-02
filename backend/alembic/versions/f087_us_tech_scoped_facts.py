"""Scoped US technical facts: generation / engine family / transmission / configuration.

Adds nullable scope columns to technical_evidence and known_issues so that one
verified fact is stored at the level where it is defined (one ground clearance
per generation, one oil capacity per engine family) instead of being copied onto
every model-year variant. Existing rows keep vehicle_variant_id and get NULL in
every new column; every existing reader filters by vehicle_variant_id, so scoped
rows (vehicle_variant_id IS NULL) stay invisible to current code paths.

Also creates maintenance_schedule_items: one row per scheduled job with typed
intervals, for owner reminders.

Downgrade is refused while scoped rows exist (they cannot be represented in the
previous schema); remove them explicitly first instead of losing them silently.
"""

import sqlalchemy as sa
from alembic import op

revision = "f087_us_tech_scoped_facts"
down_revision = "f086_listing_intake"
branch_labels = depends_on = None


def _scope_columns():
    return [
        sa.Column("scope_level", sa.String(20)),
        sa.Column("make_id", sa.String(36)),
        sa.Column("generation_id", sa.String(36)),
        sa.Column("engine_family_key", sa.String(40)),
        sa.Column("transmission_key", sa.String(40)),
        sa.Column("year_from", sa.Integer()),
        sa.Column("year_to", sa.Integer()),
        sa.Column("display_level", sa.String(20)),
        sa.Column("natural_key", sa.String(64)),
    ]


def upgrade():
    with op.batch_alter_table("technical_evidence") as batch:
        batch.alter_column("vehicle_variant_id", existing_type=sa.String(36), nullable=True)
        for column in _scope_columns():
            batch.add_column(column)
        batch.add_column(sa.Column("configuration_key", sa.String(180)))
        batch.add_column(sa.Column("fact_key", sa.String(100)))
        batch.add_column(sa.Column("value", sa.JSON()))
        batch.add_column(sa.Column("unit", sa.String(30)))
        batch.add_column(sa.Column("raw_document_id", sa.String(36)))
        batch.add_column(sa.Column("locator", sa.String(500)))
        batch.create_foreign_key(
            "fk_technical_evidence_make_id_vehicle_makes", "vehicle_makes", ["make_id"], ["id"]
        )
        batch.create_foreign_key(
            "fk_technical_evidence_generation_id_vehicle_generations",
            "vehicle_generations",
            ["generation_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_technical_evidence_raw_document_id_raw_documents",
            "raw_documents",
            ["raw_document_id"],
            ["id"],
        )
        batch.create_index("ix_technical_evidence_scope_level", ["scope_level"])
        batch.create_index("ix_technical_evidence_make_id", ["make_id"])
        batch.create_index("ix_technical_evidence_generation_id", ["generation_id"])
        batch.create_index("ix_technical_evidence_engine_family_key", ["engine_family_key"])
        batch.create_index("ix_technical_evidence_transmission_key", ["transmission_key"])
        batch.create_index("ix_technical_evidence_years", ["year_from", "year_to"])
        batch.create_index("ix_technical_evidence_configuration_key", ["configuration_key"])
        batch.create_index("ix_technical_evidence_fact_key", ["fact_key"])
        batch.create_index("ix_technical_evidence_display_level", ["display_level"])
        batch.create_index("uq_technical_evidence_natural_key", ["natural_key"], unique=True)

    with op.batch_alter_table("known_issues") as batch:
        batch.alter_column("vehicle_variant_id", existing_type=sa.String(36), nullable=True)
        for column in _scope_columns():
            batch.add_column(column)
        batch.add_column(sa.Column("market", sa.String(2)))
        batch.add_column(sa.Column("title", sa.String(240)))
        batch.add_column(sa.Column("cause", sa.Text()))
        batch.add_column(sa.Column("typical_fix", sa.Text()))
        batch.add_column(sa.Column("probability", sa.String(12)))
        batch.create_foreign_key(
            "fk_known_issues_make_id_vehicle_makes", "vehicle_makes", ["make_id"], ["id"]
        )
        batch.create_foreign_key(
            "fk_known_issues_generation_id_vehicle_generations",
            "vehicle_generations",
            ["generation_id"],
            ["id"],
        )
        batch.create_index("ix_known_issues_scope_level", ["scope_level"])
        batch.create_index("ix_known_issues_make_id", ["make_id"])
        batch.create_index("ix_known_issues_generation_id", ["generation_id"])
        batch.create_index("ix_known_issues_engine_family_key", ["engine_family_key"])
        batch.create_index("ix_known_issues_transmission_key", ["transmission_key"])
        batch.create_index("ix_known_issues_years", ["year_from", "year_to"])
        batch.create_index("ix_known_issues_market", ["market"])
        batch.create_index("uq_known_issues_natural_key", ["natural_key"], unique=True)

    op.create_table(
        "maintenance_schedule_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("market", sa.String(2), nullable=False),
        sa.Column("make_id", sa.String(36), sa.ForeignKey("vehicle_makes.id"), nullable=False),
        sa.Column("model_id", sa.String(36), sa.ForeignKey("vehicle_models.id")),
        sa.Column("generation_id", sa.String(36), sa.ForeignKey("vehicle_generations.id")),
        sa.Column("engine_family_key", sa.String(40)),
        sa.Column("transmission_key", sa.String(40)),
        sa.Column("year_from", sa.Integer(), nullable=False),
        sa.Column("year_to", sa.Integer(), nullable=False),
        sa.Column("applicability", sa.JSON(), nullable=False),
        sa.Column("schedule_system", sa.String(20), nullable=False),
        sa.Column("job", sa.String(40), nullable=False),
        sa.Column("action", sa.String(12), nullable=False),
        sa.Column("condition", sa.String(10), nullable=False),
        sa.Column("occurrence", sa.String(12), nullable=False),
        sa.Column("interval_km", sa.Integer()),
        sa.Column("interval_months", sa.Integer()),
        sa.Column("interval_miles_original", sa.Integer()),
        sa.Column("rule", sa.String(20)),
        sa.Column("max_interval_km", sa.Integer()),
        sa.Column("max_interval_months", sa.Integer()),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("source_records.id"), nullable=False),
        sa.Column("raw_document_id", sa.String(36), sa.ForeignKey("raw_documents.id")),
        sa.Column("locator", sa.String(500), nullable=False),
        sa.Column("confidence", sa.String(6), nullable=False),
        sa.Column("status", sa.String(17), nullable=False),
        sa.Column("display_level", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("natural_key", sa.String(64), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("data_origin", sa.String(4), nullable=False, server_default="REAL"),
        sa.UniqueConstraint("natural_key", name="uq_maintenance_schedule_items_natural_key"),
    )
    for name, columns in {
        "market": ["market"],
        "make_id": ["make_id"],
        "model_id": ["model_id"],
        "generation_id": ["generation_id"],
        "engine_family_key": ["engine_family_key"],
        "transmission_key": ["transmission_key"],
        "years": ["year_from", "year_to"],
        "job": ["job"],
        "source_id": ["source_id"],
    }.items():
        op.create_index(
            f"ix_maintenance_schedule_items_{name}", "maintenance_schedule_items", columns
        )


def downgrade():
    bind = op.get_bind()
    scoped = sum(
        bind.execute(
            sa.text(f"SELECT COUNT(*) FROM {table} WHERE vehicle_variant_id IS NULL")
        ).scalar()
        for table in ("technical_evidence", "known_issues")
    )
    if scoped:
        raise RuntimeError(
            f"f087 downgrade refused: {scoped} scoped rows have no vehicle_variant_id. "
            "Export and delete them explicitly before downgrading."
        )
    op.drop_table("maintenance_schedule_items")

    with op.batch_alter_table("known_issues") as batch:
        for index in (
            "uq_known_issues_natural_key",
            "ix_known_issues_market",
            "ix_known_issues_years",
            "ix_known_issues_transmission_key",
            "ix_known_issues_engine_family_key",
            "ix_known_issues_generation_id",
            "ix_known_issues_make_id",
            "ix_known_issues_scope_level",
        ):
            batch.drop_index(index)
        batch.drop_constraint(
            "fk_known_issues_generation_id_vehicle_generations", type_="foreignkey"
        )
        batch.drop_constraint("fk_known_issues_make_id_vehicle_makes", type_="foreignkey")
        for column in ("probability", "typical_fix", "cause", "title", "market"):
            batch.drop_column(column)
        for column in reversed(_scope_columns()):
            batch.drop_column(column.name)
        batch.alter_column("vehicle_variant_id", existing_type=sa.String(36), nullable=False)

    with op.batch_alter_table("technical_evidence") as batch:
        for index in (
            "uq_technical_evidence_natural_key",
            "ix_technical_evidence_display_level",
            "ix_technical_evidence_fact_key",
            "ix_technical_evidence_configuration_key",
            "ix_technical_evidence_years",
            "ix_technical_evidence_transmission_key",
            "ix_technical_evidence_engine_family_key",
            "ix_technical_evidence_generation_id",
            "ix_technical_evidence_make_id",
            "ix_technical_evidence_scope_level",
        ):
            batch.drop_index(index)
        batch.drop_constraint(
            "fk_technical_evidence_raw_document_id_raw_documents", type_="foreignkey"
        )
        batch.drop_constraint(
            "fk_technical_evidence_generation_id_vehicle_generations", type_="foreignkey"
        )
        batch.drop_constraint("fk_technical_evidence_make_id_vehicle_makes", type_="foreignkey")
        for column in (
            "locator",
            "raw_document_id",
            "unit",
            "value",
            "fact_key",
            "configuration_key",
        ):
            batch.drop_column(column)
        for column in reversed(_scope_columns()):
            batch.drop_column(column.name)
        batch.alter_column("vehicle_variant_id", existing_type=sa.String(36), nullable=False)

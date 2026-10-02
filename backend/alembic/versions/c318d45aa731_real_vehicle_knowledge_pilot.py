"""real vehicle knowledge pilot provenance

Revision ID: c318d45aa731
Revises: b74f2e6a91cd
Create Date: 2026-09-14 19:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c318d45aa731"
down_revision: str | None = "b74f2e6a91cd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _origin_column(enum_name: str) -> sa.Column:
    return sa.Column(
        "data_origin",
        sa.Enum("DEMO", "REAL", name=enum_name, native_enum=False),
        nullable=False,
        server_default="REAL",
    )


def upgrade() -> None:
    with op.batch_alter_table("source_records") as batch:
        batch.add_column(
            sa.Column(
                "source_tier",
                sa.Enum("A", "B", "C", name="source_tier", native_enum=False),
                nullable=False,
                server_default="B",
            )
        )
        batch.add_column(_origin_column("source_data_origin"))
        batch.create_index("ix_source_records_source_tier", ["source_tier"])
        batch.create_index("ix_source_records_data_origin", ["data_origin"])

    tables = {
        "technical_evidence": "evidence_data_origin",
        "known_issues": "known_issue_data_origin",
        "market_listings": "market_listing_data_origin",
        "local_cost_items": "local_cost_data_origin",
        "owner_evidence": "owner_evidence_data_origin",
        "vehicle_variants": "vehicle_variant_data_origin",
        "vin_checks": "vin_history_data_origin",
    }
    with op.batch_alter_table("known_issues") as batch:
        batch.add_column(
            sa.Column("source_count", sa.Integer(), nullable=False, server_default="1")
        )
    for table, enum_name in tables.items():
        with op.batch_alter_table(table) as batch:
            batch.add_column(_origin_column(enum_name))
            batch.create_index(f"ix_{table}_data_origin", ["data_origin"])

    with op.batch_alter_table("vehicle_knowledge_profiles") as batch:
        batch.drop_constraint("uq_vehicle_knowledge_profile_identity", type_="unique")
        batch.add_column(_origin_column("vehicle_profile_data_origin"))
        batch.create_index("ix_vehicle_knowledge_profiles_data_origin", ["data_origin"])
        batch.create_unique_constraint(
            "uq_vehicle_knowledge_profile_identity",
            [
                "make",
                "model",
                "generation",
                "market",
                "year",
                "engine_code",
                "transmission",
                "data_origin",
            ],
        )

    for table in ["source_records", *tables, "vehicle_knowledge_profiles"]:
        op.execute(sa.text(f"UPDATE {table} SET data_origin = 'DEMO' WHERE is_demo = 1"))


def downgrade() -> None:
    with op.batch_alter_table("vehicle_knowledge_profiles") as batch:
        batch.drop_constraint("uq_vehicle_knowledge_profile_identity", type_="unique")
        batch.drop_index("ix_vehicle_knowledge_profiles_data_origin")
        batch.drop_column("data_origin")
        batch.create_unique_constraint(
            "uq_vehicle_knowledge_profile_identity",
            [
                "make",
                "model",
                "generation",
                "market",
                "year",
                "engine_code",
                "transmission",
            ],
        )

    for table in (
        "vin_checks",
        "vehicle_variants",
        "owner_evidence",
        "local_cost_items",
        "market_listings",
        "known_issues",
        "technical_evidence",
    ):
        with op.batch_alter_table(table) as batch:
            batch.drop_index(f"ix_{table}_data_origin")
            batch.drop_column("data_origin")
    with op.batch_alter_table("known_issues") as batch:
        batch.drop_column("source_count")

    with op.batch_alter_table("source_records") as batch:
        batch.drop_index("ix_source_records_data_origin")
        batch.drop_index("ix_source_records_source_tier")
        batch.drop_column("data_origin")
        batch.drop_column("source_tier")

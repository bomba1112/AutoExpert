"""auto expert 2 vin dossier

Revision ID: 6f13b027d4aa
Revises: ea540c89c430
Create Date: 2026-09-14 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6f13b027d4aa"
down_revision: str | None = "ea540c89c430"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("known_issues") as batch_op:
        batch_op.add_column(
            sa.Column("symptoms", sa.JSON(), server_default=sa.text("'[]'"), nullable=False)
        )
        batch_op.add_column(sa.Column("consequences", sa.Text(), nullable=True))

    op.create_table(
        "vehicle_knowledge_profiles",
        sa.Column("vehicle_variant_id", sa.String(length=36), nullable=True),
        sa.Column("make", sa.String(length=120), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("generation", sa.String(length=120), nullable=False),
        sa.Column("production_year_start", sa.Integer(), nullable=True),
        sa.Column("production_year_end", sa.Integer(), nullable=True),
        sa.Column("market", sa.String(length=12), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("engine", sa.String(length=160), nullable=True),
        sa.Column("engine_code", sa.String(length=80), nullable=True),
        sa.Column("transmission", sa.String(length=120), nullable=True),
        sa.Column("drivetrain", sa.String(length=40), nullable=True),
        sa.Column("body", sa.String(length=60), nullable=True),
        sa.Column("fuel", sa.String(length=40), nullable=True),
        sa.Column("profile_version", sa.String(length=30), nullable=False),
        sa.Column("freshness_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dossier_seed", sa.JSON(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["vehicle_variant_id"],
            ["vehicle_variants.id"],
            name=op.f("fk_vehicle_knowledge_profiles_vehicle_variant_id_vehicle_variants"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vehicle_knowledge_profiles")),
        sa.UniqueConstraint(
            "make",
            "model",
            "generation",
            "market",
            "year",
            "engine_code",
            "transmission",
            name="uq_vehicle_knowledge_profile_identity",
        ),
    )
    for column in (
        "vehicle_variant_id",
        "make",
        "model",
        "generation",
        "market",
        "year",
        "engine_code",
        "freshness_at",
        "is_demo",
    ):
        op.create_index(
            op.f(f"ix_vehicle_knowledge_profiles_{column}"),
            "vehicle_knowledge_profiles",
            [column],
            unique=False,
        )

    op.create_table(
        "vehicle_profile_sources",
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["vehicle_knowledge_profiles.id"],
            name=op.f("fk_vehicle_profile_sources_profile_id_vehicle_knowledge_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["source_records.id"],
            name=op.f("fk_vehicle_profile_sources_source_id_source_records"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("profile_id", "source_id", name=op.f("pk_vehicle_profile_sources")),
    )
    op.create_table(
        "vehicle_profile_evidence",
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["vehicle_knowledge_profiles.id"],
            name=op.f("fk_vehicle_profile_evidence_profile_id_vehicle_knowledge_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["technical_evidence.id"],
            name=op.f("fk_vehicle_profile_evidence_evidence_id_technical_evidence"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "profile_id", "evidence_id", name=op.f("pk_vehicle_profile_evidence")
        ),
    )

    op.create_table(
        "vin_checks",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_profile_id", sa.String(length=36), nullable=True),
        sa.Column("normalized_vin", sa.String(length=17), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("found", sa.Boolean(), nullable=False),
        sa.Column("records_count", sa.Integer(), nullable=False),
        sa.Column("photos_count", sa.Integer(), nullable=False),
        sa.Column("auctions_count", sa.Integer(), nullable=False),
        sa.Column("has_salvage_title", sa.Boolean(), nullable=False),
        sa.Column(
            "odometer_risk",
            sa.Enum(
                "NONE", "LOW", "MEDIUM", "HIGH", "UNKNOWN", name="odometer_risk", native_enum=False
            ),
            nullable=False,
        ),
        sa.Column("full_history_payload", sa.JSON(), nullable=False),
        sa.Column("dossier_snapshot", sa.JSON(), nullable=False),
        sa.Column("source_snapshot", sa.JSON(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_vin_checks_user_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_profile_id"],
            ["vehicle_knowledge_profiles.id"],
            name=op.f("fk_vin_checks_vehicle_profile_id_vehicle_knowledge_profiles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vin_checks")),
    )
    for column in ("user_id", "vehicle_profile_id", "normalized_vin", "is_demo"):
        op.create_index(op.f(f"ix_vin_checks_{column}"), "vin_checks", [column], unique=False)

    op.create_table(
        "vin_entitlements",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("vin_check_id", sa.String(length=36), nullable=False),
        sa.Column(
            "entitlement_type",
            sa.Enum("VIN_REPORT_UNLOCKED", name="entitlement_type", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "REVOKED", name="entitlement_status", native_enum=False),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("external_payment_id", sa.String(length=200), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("provider_payload", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_vin_entitlements_user_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["vin_check_id"],
            ["vin_checks.id"],
            name=op.f("fk_vin_entitlements_vin_check_id_vin_checks"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vin_entitlements")),
        sa.UniqueConstraint(
            "user_id",
            "vin_check_id",
            "entitlement_type",
            name="uq_vin_entitlement_owner_resource_type",
        ),
    )
    for column in ("user_id", "vin_check_id", "external_payment_id"):
        op.create_index(
            op.f(f"ix_vin_entitlements_{column}"),
            "vin_entitlements",
            [column],
            unique=False,
        )

    op.create_table(
        "auto_expert_chat_contexts",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("vin_check_id", sa.String(length=36), nullable=False),
        sa.Column("context_version", sa.String(length=30), nullable=False),
        sa.Column("vehicle_profile_snapshot", sa.JSON(), nullable=False),
        sa.Column("vin_history_snapshot", sa.JSON(), nullable=False),
        sa.Column("report_snapshot", sa.JSON(), nullable=False),
        sa.Column("sources_snapshot", sa.JSON(), nullable=False),
        sa.Column("system_constraints", sa.JSON(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_auto_expert_chat_contexts_user_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["vin_check_id"],
            ["vin_checks.id"],
            name=op.f("fk_auto_expert_chat_contexts_vin_check_id_vin_checks"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auto_expert_chat_contexts")),
        sa.UniqueConstraint(
            "user_id", "vin_check_id", name=op.f("uq_auto_expert_chat_contexts_user_id")
        ),
    )
    op.create_index(
        op.f("ix_auto_expert_chat_contexts_user_id"),
        "auto_expert_chat_contexts",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auto_expert_chat_contexts_vin_check_id"),
        "auto_expert_chat_contexts",
        ["vin_check_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_auto_expert_chat_contexts_vin_check_id"), table_name="auto_expert_chat_contexts"
    )
    op.drop_index(
        op.f("ix_auto_expert_chat_contexts_user_id"), table_name="auto_expert_chat_contexts"
    )
    op.drop_table("auto_expert_chat_contexts")
    for column in ("external_payment_id", "vin_check_id", "user_id"):
        op.drop_index(op.f(f"ix_vin_entitlements_{column}"), table_name="vin_entitlements")
    op.drop_table("vin_entitlements")
    for column in ("is_demo", "normalized_vin", "vehicle_profile_id", "user_id"):
        op.drop_index(op.f(f"ix_vin_checks_{column}"), table_name="vin_checks")
    op.drop_table("vin_checks")
    op.drop_table("vehicle_profile_evidence")
    op.drop_table("vehicle_profile_sources")
    for column in (
        "is_demo",
        "freshness_at",
        "engine_code",
        "year",
        "market",
        "generation",
        "model",
        "make",
        "vehicle_variant_id",
    ):
        op.drop_index(
            op.f(f"ix_vehicle_knowledge_profiles_{column}"),
            table_name="vehicle_knowledge_profiles",
        )
    op.drop_table("vehicle_knowledge_profiles")
    with op.batch_alter_table("known_issues") as batch_op:
        batch_op.drop_column("consequences")
        batch_op.drop_column("symptoms")

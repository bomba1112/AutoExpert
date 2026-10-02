"""automatic vehicle research jobs and provider cache

Revision ID: d942f4c1a6e8
Revises: c318d45aa731
Create Date: 2026-09-15 08:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d942f4c1a6e8"
down_revision: str | None = "c318d45aa731"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_jobs",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("vehicle_profile_id", sa.String(36), nullable=True),
        sa.Column("request_key", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "PARTIAL",
                "COMPLETE",
                "FAILED",
                name="research_job_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("requested_vehicle", sa.JSON(), nullable=False),
        sa.Column("provider_steps", sa.JSON(), nullable=False),
        sa.Column("completed_capabilities", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("resolution_snapshot", sa.JSON(), nullable=False),
        sa.Column("dossier_snapshot", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vehicle_profile_id"], ["vehicle_knowledge_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    research_indexes = (
        "user_id",
        "vehicle_profile_id",
        "request_key",
        "status",
        "cache_hit",
        "is_demo",
    )
    for column in research_indexes:
        op.create_index(f"ix_research_jobs_{column}", "research_jobs", [column])

    op.create_table(
        "provider_cache_entries",
        sa.Column("provider_id", sa.String(80), nullable=False),
        sa.Column("capability", sa.String(80), nullable=False),
        sa.Column("cache_key", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "CONFIRMED",
                "ESTIMATE",
                "NEEDS_INSPECTION",
                "INSUFFICIENT_DATA",
                name="provider_cache_evidence_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("normalized_payload", sa.JSON(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "data_origin",
            sa.Enum("DEMO", "REAL", name="provider_cache_data_origin", native_enum=False),
            nullable=False,
        ),
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider_id",
            "capability",
            "cache_key",
            name="uq_provider_cache_provider_capability_key",
        ),
    )
    for column in ("provider_id", "capability", "cache_key", "expires_at", "data_origin"):
        op.create_index(f"ix_provider_cache_entries_{column}", "provider_cache_entries", [column])


def downgrade() -> None:
    op.drop_table("provider_cache_entries")
    op.drop_table("research_jobs")

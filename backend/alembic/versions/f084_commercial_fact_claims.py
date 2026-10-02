"""Add field-scoped commercial evidence without changing research revisions."""

import sqlalchemy as sa
from alembic import op

revision = "f084_commercial_fact_claims"
down_revision = "f083_market_discovery"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "commercial_fact_claims",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "variant_id", sa.String(36), sa.ForeignKey("vehicle_variants.id"), nullable=False
        ),
        sa.Column("fact_name", sa.String(100), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "source_id", sa.String(80), sa.ForeignKey("knowledge_sources.id"), nullable=False
        ),
        sa.Column("evidence_scope", sa.JSON(), nullable=False),
        sa.Column("reuse_status", sa.String(30), nullable=False),
        sa.Column("source_url", sa.String(2000), nullable=False),
        sa.Column("locator", sa.String(500), nullable=False),
        sa.Column("rights_basis", sa.String(40)),
        sa.Column("rights_reference", sa.String(2000)),
        sa.Column("rights_checked_at", sa.String(10)),
        sa.Column("unit", sa.String(40)),
        sa.UniqueConstraint("variant_id", "fact_name", "source_id", "locator"),
    )
    for key in ("variant_id", "fact_name", "source_id", "reuse_status"):
        op.create_index(f"ix_commercial_fact_claims_{key}", "commercial_fact_claims", [key])


def downgrade():
    op.drop_table("commercial_fact_claims")

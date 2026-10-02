"""User-owned Turbo.az snapshot and seller-claim intake."""

import sqlalchemy as sa
from alembic import op

revision = "f086_listing_intake"
down_revision = "f085_vin_history_flow"
branch_labels = depends_on = None


def _identity():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade():
    op.create_table(
        "listing_intake_requests",
        *_identity(),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("request_key", sa.String(64), nullable=False),
        sa.Column("language", sa.String(2), nullable=False),
        sa.UniqueConstraint("user_id", "request_key", name="uq_listing_intake_owner_key"),
    )
    op.create_index("ix_listing_intake_requests_user_id", "listing_intake_requests", ["user_id"])
    op.create_table(
        "listing_snapshots",
        *_identity(),
        sa.Column(
            "request_id", sa.String(36), sa.ForeignKey("listing_intake_requests.id"), nullable=False
        ),
        sa.Column("source_type", sa.String(24), nullable=False),
        sa.Column("source_url", sa.String(2000)),
        sa.Column("source_listing_id", sa.String(40)),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("input_type", sa.String(24), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("raw_content_locator", sa.String(180)),
        sa.Column("sanitized_content", sa.Text()),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("parser_version", sa.String(40), nullable=False),
        sa.UniqueConstraint("request_id", name="uq_listing_snapshot_request"),
    )
    op.create_index("ix_listing_snapshots_request_id", "listing_snapshots", ["request_id"])
    op.create_table(
        "listing_field_claims",
        *_identity(),
        sa.Column(
            "snapshot_id", sa.String(36), sa.ForeignKey("listing_snapshots.id"), nullable=False
        ),
        sa.Column("field_name", sa.String(40), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.JSON(), nullable=False),
        sa.Column("unit", sa.String(24)),
        sa.Column("claim_type", sa.String(24), nullable=False),
        sa.Column("source_locator", sa.String(180), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
    )
    op.create_index("ix_listing_field_claims_snapshot_id", "listing_field_claims", ["snapshot_id"])
    op.create_index("ix_listing_field_claims_field_name", "listing_field_claims", ["field_name"])
    op.create_table(
        "listing_match_results",
        *_identity(),
        sa.Column(
            "request_id", sa.String(36), sa.ForeignKey("listing_intake_requests.id"), nullable=False
        ),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("candidates", sa.JSON(), nullable=False),
        sa.Column("question", sa.Text()),
        sa.Column("conflicts", sa.JSON(), nullable=False),
        sa.UniqueConstraint("request_id", name="uq_listing_match_request"),
    )
    op.create_index("ix_listing_match_results_request_id", "listing_match_results", ["request_id"])


def downgrade():
    op.drop_index("ix_listing_match_results_request_id", table_name="listing_match_results")
    op.drop_table("listing_match_results")
    op.drop_index("ix_listing_field_claims_field_name", table_name="listing_field_claims")
    op.drop_index("ix_listing_field_claims_snapshot_id", table_name="listing_field_claims")
    op.drop_table("listing_field_claims")
    op.drop_index("ix_listing_snapshots_request_id", table_name="listing_snapshots")
    op.drop_table("listing_snapshots")
    op.drop_index("ix_listing_intake_requests_user_id", table_name="listing_intake_requests")
    op.drop_table("listing_intake_requests")

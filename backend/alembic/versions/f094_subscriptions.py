# ruff: noqa: E501
"""The subscription model (product phase, stage 6): the user's plan state. A new table only; no
payment data."""

import sqlalchemy as sa
from alembic import op

revision = "f094_subscriptions"
down_revision = "f093_owners_club"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_subscriptions_user_id_users"), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("store", sa.String(15), nullable=False),
        sa.Column("region", sa.String(8), nullable=False),
        sa.Column("price_minor", sa.Integer()),
        sa.Column("currency", sa.String(3)),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("external_id", sa.String(200)),
        sa.Column("canceled_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])


def downgrade():
    op.drop_table("subscriptions")

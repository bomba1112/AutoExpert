# ruff: noqa: E501
"""The AI mechanic's request log (product phase, stage 3). A new table only."""

import sqlalchemy as sa
from alembic import op

revision = "f091_ai_mechanic"
down_revision = "f090_garage"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "ai_mechanic_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE",
                                                         name="fk_ai_mechanic_requests_user_id_users"), nullable=False),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("garage_vehicles.id", ondelete="SET NULL",
                                                            name="fk_ai_mechanic_requests_vehicle_id_garage_vehicles")),
        sa.Column("configuration_key", sa.String(200)),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("model", sa.String(80)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("answer", sa.JSON(), nullable=False),
        sa.Column("rejected", sa.JSON(), nullable=False),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("latency_ms", sa.Integer()),
    )
    op.create_index("ix_ai_mechanic_requests_user_id", "ai_mechanic_requests", ["user_id"])
    op.create_index("ix_ai_mechanic_requests_vehicle_id", "ai_mechanic_requests", ["vehicle_id"])


def downgrade():
    op.drop_table("ai_mechanic_requests")

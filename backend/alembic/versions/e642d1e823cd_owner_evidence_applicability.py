"""Persist applicability of owner/official complaint evidence without asserting VIN match."""

import sqlalchemy as sa
from alembic import op

revision = "e642d1e823cd"
down_revision = "e641c0f912ab"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "owner_evidence", sa.Column("applicability", sa.JSON(), nullable=False, server_default="{}")
    )
    op.add_column(
        "owner_evidence",
        sa.Column("applicability_class", sa.String(20), nullable=False, server_default="UNKNOWN"),
    )


def downgrade() -> None:
    with op.batch_alter_table("owner_evidence") as batch:
        batch.drop_column("applicability_class")
        batch.drop_column("applicability")

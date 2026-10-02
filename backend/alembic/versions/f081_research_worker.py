"""Durable control for the existing ResearchJob, independent of result metrics."""

import sqlalchemy as sa
from alembic import op

revision = "f081_research_worker"
down_revision = "f080_catalog_publication"
branch_labels = depends_on = None


def upgrade():
    op.add_column("research_jobs", sa.Column("worker_queue", sa.String(30)))
    op.add_column("research_jobs", sa.Column("worker_lease_until", sa.DateTime(timezone=True)))
    op.add_column(
        "research_jobs",
        sa.Column("worker_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "research_jobs",
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_research_jobs_worker_queue", "research_jobs", ["worker_queue"])


def downgrade():
    op.drop_index("ix_research_jobs_worker_queue", table_name="research_jobs")
    with op.batch_alter_table("research_jobs") as batch:
        for name in ("worker_queue", "worker_lease_until", "worker_attempts", "cancel_requested"):
            batch.drop_column(name)

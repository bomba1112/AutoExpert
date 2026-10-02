"""Typed cost evidence uses the existing acquisition/publication jobs and reports."""

import sqlalchemy as sa
from alembic import op

revision = "f082_ownership_evidence"
down_revision = "f081_research_worker"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "ownership_evidence_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "import_job_id",
            sa.String(36),
            sa.ForeignKey("knowledge_import_jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "source_id", sa.String(80), sa.ForeignKey("knowledge_sources.id"), nullable=False
        ),
        sa.Column("external_key", sa.String(160), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("state", sa.String(30), nullable=False),
        sa.Column("active_key", sa.String(250), unique=True),
        sa.Column("previous_revision_id", sa.String(36)),
        sa.Column("identity_hashes", sa.JSON(), nullable=False),
        sa.Column("publication_scope", sa.String(30)),
        sa.Column("editorial_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reviewer", sa.String(120)),
        sa.Column("review_note", sa.Text()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("import_job_id", "external_key"),
    )
    for key in ("import_job_id", "source_id", "kind", "state"):
        op.create_index(
            "ix_ownership_evidence_revisions_" + key, "ownership_evidence_revisions", [key]
        )


def downgrade():
    op.drop_table("ownership_evidence_revisions")

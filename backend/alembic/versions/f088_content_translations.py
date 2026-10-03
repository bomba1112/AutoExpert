"""Translations of buyer-facing English content into Russian and Azerbaijani.

A new table only; no existing row or column changes. The English original stays in its
table; content_translations carries text_ru / text_az per (kind, sha256 of the English text).
"""

import sqlalchemy as sa
from alembic import op

revision = "f088_content_translations"
down_revision = "f087_us_tech_scoped_facts"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "content_translations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("text_ru", sa.Text(), nullable=False),
        sa.Column("text_az", sa.Text(), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("glossary_version", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.UniqueConstraint("kind", "source_hash", name="uq_content_translations_kind"),
    )
    op.create_index("ix_content_translations_kind", "content_translations", ["kind"])
    op.create_index("ix_content_translations_source_hash", "content_translations", ["source_hash"])


def downgrade():
    op.drop_index("ix_content_translations_source_hash", table_name="content_translations")
    op.drop_index("ix_content_translations_kind", table_name="content_translations")
    op.drop_table("content_translations")

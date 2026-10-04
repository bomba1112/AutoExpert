"""Clean English versions of the buyer-facing texts (product phase, stage 1).

content_translations gets text_en: the English shown to English users — sentence case and plain
wording where the source is in capitals (NHTSA component paths), else the source text. The
original stays in source_text. Nullable, so existing rows stay valid until the next load.
"""

import sqlalchemy as sa
from alembic import op

revision = "f089_content_translations_en"
down_revision = "f088_content_translations"
branch_labels = depends_on = None


def upgrade():
    op.add_column("content_translations", sa.Column("text_en", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("content_translations", "text_en")

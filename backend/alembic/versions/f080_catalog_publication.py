"""Add acquisition/review metadata to the existing catalogue, preserving legacy rows."""

import sqlalchemy as sa
from alembic import op

revision = "f080_catalog_publication"
down_revision = "e642d1e823cd"
branch_labels = depends_on = None

TABLES = [
    "knowledge_sources",
    "raw_documents",
    "knowledge_import_jobs",
    "catalog_revisions",
    "editorial_reviews",
    "vehicle_assets",
    "editorial_publications",
    "publication_favorites",
]


def upgrade():
    # New operational tables have no predecessor data. Catalogue entities are reused.
    op.add_column("vehicle_variants", sa.Column("catalog_key", sa.String(180)))
    op.add_column("vehicle_variants", sa.Column("published_revision_id", sa.String(36)))
    op.add_column(
        "vehicle_variants",
        sa.Column("editorial_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_vehicle_variants_catalog_key", "vehicle_variants", ["catalog_key"], unique=True
    )
    op.create_index(
        "ix_vehicle_variants_published_revision_id", "vehicle_variants", ["published_revision_id"]
    )
    with op.batch_alter_table("vehicle_variants") as batch:
        batch.alter_column("market", type_=sa.String(24), existing_type=sa.String(2))
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.String(length=80), nullable=False, primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("paused", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "raw_documents",
        sa.Column(
            "source_id", sa.String(length=80), sa.ForeignKey("knowledge_sources.id"), nullable=False
        ),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=180), nullable=False),
        sa.Column("media_type", sa.String(length=80), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("locator", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_id", "sha256", name="uq_raw_documents_source_id"),
    )
    op.create_index("ix_raw_documents_sha256", "raw_documents", ["sha256"], unique=False)
    op.create_table(
        "knowledge_import_jobs",
        sa.Column("request_key", sa.String(length=64), nullable=False),
        sa.Column(
            "source_id", sa.String(length=80), sa.ForeignKey("knowledge_sources.id"), nullable=False
        ),
        sa.Column(
            "raw_document_id",
            sa.String(length=36),
            sa.ForeignKey("raw_documents.id"),
            nullable=True,
        ),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("cursor", sa.Integer(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("request_key", name="uq_knowledge_import_jobs_request_key"),
    )
    op.create_index(
        "ix_knowledge_import_jobs_source_id", "knowledge_import_jobs", ["source_id"], unique=False
    )
    op.create_index(
        "ix_knowledge_import_jobs_state", "knowledge_import_jobs", ["state"], unique=False
    )
    op.create_table(
        "catalog_revisions",
        sa.Column(
            "import_job_id",
            sa.String(length=36),
            sa.ForeignKey("knowledge_import_jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "variant_id", sa.String(length=36), sa.ForeignKey("vehicle_variants.id"), nullable=True
        ),
        sa.Column("external_key", sa.String(length=160), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("previous_revision_id", sa.String(length=36), nullable=True),
        sa.Column("reviewer", sa.String(length=120), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "import_job_id", "external_key", name="uq_catalog_revisions_import_job_id"
        ),
    )
    op.create_index(
        "ix_catalog_revisions_external_key", "catalog_revisions", ["external_key"], unique=False
    )
    op.create_index(
        "ix_catalog_revisions_import_job_id", "catalog_revisions", ["import_job_id"], unique=False
    )
    op.create_index("ix_catalog_revisions_state", "catalog_revisions", ["state"], unique=False)
    op.create_index(
        "ix_catalog_revisions_variant_id", "catalog_revisions", ["variant_id"], unique=False
    )
    op.create_table(
        "editorial_reviews",
        sa.Column("actor_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", sa.String(length=80), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("before", sa.JSON(), nullable=False),
        sa.Column("after", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_editorial_reviews_target_id", "editorial_reviews", ["target_id"], unique=False
    )
    op.create_table(
        "vehicle_assets",
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("applicability", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("rights", sa.JSON(), nullable=False),
        sa.Column("renditions", sa.JSON(), nullable=False),
        sa.Column("original_key", sa.String(length=180), nullable=False),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("reviewer", sa.String(length=120), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("sha256", name="uq_vehicle_assets_sha256"),
    )
    op.create_index("ix_vehicle_assets_state", "vehicle_assets", ["state"], unique=False)
    op.create_table(
        "editorial_publications",
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("translations", sa.JSON(), nullable=False),
        sa.Column("variant_ids", sa.JSON(), nullable=False),
        sa.Column("asset_ids", sa.JSON(), nullable=False),
        sa.Column("scenario", sa.JSON(), nullable=False),
        sa.Column("claims", sa.JSON(), nullable=False),
        sa.Column("topics", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("slug", name="uq_editorial_publications_slug"),
    )
    op.create_index(
        "ix_editorial_publications_state", "editorial_publications", ["state"], unique=False
    )
    op.create_table(
        "publication_favorites",
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "publication_id",
            sa.String(length=36),
            sa.ForeignKey("editorial_publications.id"),
            nullable=False,
        ),
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "publication_id", name="uq_publication_favorites_user_id"),
    )
    op.create_index(
        "ix_publication_favorites_user_id", "publication_favorites", ["user_id"], unique=False
    )


def downgrade():
    for name in reversed(TABLES):
        op.drop_table(name)
    op.drop_index("ix_vehicle_variants_catalog_key", table_name="vehicle_variants")
    op.drop_index("ix_vehicle_variants_published_revision_id", table_name="vehicle_variants")
    with op.batch_alter_table("vehicle_variants") as batch:
        batch.drop_column("catalog_key")
        batch.drop_column("published_revision_id")
        batch.drop_column("editorial_locked")

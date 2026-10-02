"""Publication and acquisition metadata for the existing vehicle catalogue."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SourceRegistry(TimestampMixin, Base):
    __tablename__ = "knowledge_sources"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    config: Mapped[dict] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(40), default="NEEDS_PERMISSION")
    paused: Mapped[bool] = mapped_column(Boolean, default=False)


class CommercialFactClaim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Independent, field-scoped evidence for a research candidate.

    A claim never changes the underlying catalogue revision. In particular, a
    claim about one field cannot grant reuse rights to the EPA source row or to
    another field from that row.
    """

    __tablename__ = "commercial_fact_claims"
    __table_args__ = (UniqueConstraint("variant_id", "fact_name", "source_id", "locator"),)

    variant_id: Mapped[str] = mapped_column(ForeignKey("vehicle_variants.id"), index=True)
    fact_name: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[object] = mapped_column(JSON)
    source_id: Mapped[str] = mapped_column(ForeignKey("knowledge_sources.id"), index=True)
    evidence_scope: Mapped[dict] = mapped_column(JSON)
    reuse_status: Mapped[str] = mapped_column(String(30), index=True)
    source_url: Mapped[str] = mapped_column(String(2000))
    locator: Mapped[str] = mapped_column(String(500))
    rights_basis: Mapped[str | None] = mapped_column(String(40))
    rights_reference: Mapped[str | None] = mapped_column(String(2000))
    rights_checked_at: Mapped[str | None] = mapped_column(String(10))
    unit: Mapped[str | None] = mapped_column(String(40))


class RawDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "raw_documents"
    __table_args__ = (UniqueConstraint("source_id", "sha256"),)
    source_id: Mapped[str] = mapped_column(ForeignKey("knowledge_sources.id"))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    storage_key: Mapped[str] = mapped_column(String(180))
    media_type: Mapped[str] = mapped_column(String(80))
    byte_size: Mapped[int] = mapped_column(Integer)
    locator: Mapped[str] = mapped_column(Text)


class ImportJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_import_jobs"
    request_key: Mapped[str] = mapped_column(String(64), unique=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("knowledge_sources.id"), index=True)
    raw_document_id: Mapped[str | None] = mapped_column(ForeignKey("raw_documents.id"))
    manifest: Mapped[dict] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(40), default="QUEUED", index=True)
    cursor: Mapped[int] = mapped_column(Integer, default=0)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)


class CatalogRevision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "catalog_revisions"
    __table_args__ = (UniqueConstraint("import_job_id", "external_key"),)
    import_job_id: Mapped[str] = mapped_column(ForeignKey("knowledge_import_jobs.id"), index=True)
    variant_id: Mapped[str | None] = mapped_column(ForeignKey("vehicle_variants.id"), index=True)
    external_key: Mapped[str] = mapped_column(String(160), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    checksum: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(30), default="STAGING", index=True)
    previous_revision_id: Mapped[str | None] = mapped_column(String(36))
    reviewer: Mapped[str | None] = mapped_column(String(120))
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EditorialReview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "editorial_reviews"
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[str] = mapped_column(String(80), index=True)
    action: Mapped[str] = mapped_column(String(40))
    note: Mapped[str] = mapped_column(Text)
    before: Mapped[dict] = mapped_column(JSON, default=dict)
    after: Mapped[dict] = mapped_column(JSON, default=dict)


class OwnershipEvidenceRevision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ownership_evidence_revisions"
    __table_args__ = (UniqueConstraint("import_job_id", "external_key"),)
    import_job_id: Mapped[str] = mapped_column(ForeignKey("knowledge_import_jobs.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("knowledge_sources.id"), index=True)
    external_key: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(30), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    checksum: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(30), default="STAGING", index=True)
    active_key: Mapped[str | None] = mapped_column(String(250), unique=True)
    previous_revision_id: Mapped[str | None] = mapped_column(String(36))
    identity_hashes: Mapped[dict] = mapped_column(JSON, default=dict)
    publication_scope: Mapped[str | None] = mapped_column(String(30))
    editorial_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewer: Mapped[str | None] = mapped_column(String(120))
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VehicleAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_assets"
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    applicability: Mapped[dict] = mapped_column(JSON)
    provenance: Mapped[dict] = mapped_column(JSON)
    rights: Mapped[dict] = mapped_column(JSON)
    renditions: Mapped[dict] = mapped_column(JSON, default=dict)
    original_key: Mapped[str] = mapped_column(String(180))
    state: Mapped[str] = mapped_column(String(40), default="IMAGE_QA", index=True)
    reviewer: Mapped[str | None] = mapped_column(String(120))
    version: Mapped[int] = mapped_column(Integer, default=1)


class MarketDiscoveryRevision(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "market_discovery_revisions"
    __table_args__ = (UniqueConstraint("import_job_id", "external_key"),)
    import_job_id: Mapped[str] = mapped_column(ForeignKey("knowledge_import_jobs.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("knowledge_sources.id"), index=True)
    external_key: Mapped[str] = mapped_column(String(160))
    payload: Mapped[dict] = mapped_column(JSON)
    checksum: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(30), default="STAGING", index=True)
    active_key: Mapped[str | None] = mapped_column(String(250), unique=True)
    previous_revision_id: Mapped[str | None] = mapped_column(String(36))
    reviewer: Mapped[str | None] = mapped_column(String(120))
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EditorialPublication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "editorial_publications"
    slug: Mapped[str] = mapped_column(String(180), unique=True)
    translations: Mapped[dict] = mapped_column(JSON)
    variant_ids: Mapped[list] = mapped_column(JSON)
    asset_ids: Mapped[list] = mapped_column(JSON, default=list)
    scenario: Mapped[dict] = mapped_column(JSON, default=dict)
    claims: Mapped[list] = mapped_column(JSON, default=list)
    topics: Mapped[list] = mapped_column(JSON, default=list)
    state: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class PublicationFavorite(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publication_favorites"
    __table_args__ = (UniqueConstraint("user_id", "publication_id"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    publication_id: Mapped[str] = mapped_column(ForeignKey("editorial_publications.id"))

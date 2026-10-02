"""User-owned listing snapshots, isolated from verified vehicle evidence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ListingIntakeRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "listing_intake_requests"
    __table_args__ = (
        UniqueConstraint("user_id", "request_key", name="uq_listing_intake_owner_key"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    request_key: Mapped[str] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(2))
    snapshot: Mapped[ListingSnapshot] = relationship(
        back_populates="request", uselist=False, cascade="all, delete-orphan"
    )
    match: Mapped[ListingMatchResult] = relationship(
        back_populates="request", uselist=False, cascade="all, delete-orphan"
    )


class ListingSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "listing_snapshots"
    __table_args__ = (UniqueConstraint("request_id", name="uq_listing_snapshot_request"),)

    request_id: Mapped[str] = mapped_column(ForeignKey("listing_intake_requests.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(24), default="TURBO_AZ")
    source_url: Mapped[str | None] = mapped_column(String(2000))
    source_listing_id: Mapped[str | None] = mapped_column(String(40))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    input_type: Mapped[str] = mapped_column(String(24))
    content_hash: Mapped[str] = mapped_column(String(64))
    raw_content_locator: Mapped[str | None] = mapped_column(String(180))
    # Sanitized, visible text only. HTML, scripts, photos and remote bytes are never stored.
    sanitized_content: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(2))
    parser_version: Mapped[str] = mapped_column(String(40))
    request: Mapped[ListingIntakeRequest] = relationship(back_populates="snapshot")
    claims: Mapped[list[ListingFieldClaim]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan", order_by="ListingFieldClaim.id"
    )


class ListingFieldClaim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "listing_field_claims"

    snapshot_id: Mapped[str] = mapped_column(ForeignKey("listing_snapshots.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(40), index=True)
    raw_value: Mapped[str] = mapped_column(Text)
    normalized_value: Mapped[object] = mapped_column(JSON)
    unit: Mapped[str | None] = mapped_column(String(24))
    claim_type: Mapped[str] = mapped_column(String(24), default="SELLER_CLAIM")
    source_locator: Mapped[str] = mapped_column(String(180))
    confidence: Mapped[float] = mapped_column(Float)
    snapshot: Mapped[ListingSnapshot] = relationship(back_populates="claims")


class ListingMatchResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "listing_match_results"
    __table_args__ = (UniqueConstraint("request_id", name="uq_listing_match_request"),)

    request_id: Mapped[str] = mapped_column(ForeignKey("listing_intake_requests.id"), index=True)
    status: Mapped[str] = mapped_column(String(32))
    candidates: Mapped[list] = mapped_column(JSON, default=list)
    question: Mapped[str | None] = mapped_column(Text)
    conflicts: Mapped[list] = mapped_column(JSON, default=list)
    request: Mapped[ListingIntakeRequest] = relationship(back_populates="match")

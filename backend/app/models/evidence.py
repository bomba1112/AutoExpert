from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    ConfidenceLevel,
    DataOrigin,
    EvidenceCategory,
    EvidenceStatus,
    Sentiment,
    Severity,
    SourceTier,
    SourceUsageStatus,
)


def enum_column(enum_type: type, name: str) -> Enum:
    return Enum(enum_type, name=name, native_enum=False, validate_strings=True)


class SourceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_records"

    title: Mapped[str] = mapped_column(String(300))
    publisher: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(80), index=True)
    source_tier: Mapped[SourceTier] = mapped_column(
        enum_column(SourceTier, "source_tier"), default=SourceTier.B, index=True
    )
    data_origin: Mapped[DataOrigin] = mapped_column(
        enum_column(DataOrigin, "source_data_origin"), default=DataOrigin.REAL, index=True
    )
    market: Mapped[str | None] = mapped_column(String(2), index=True)
    language: Mapped[str | None] = mapped_column(String(5))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        enum_column(ConfidenceLevel, "source_confidence")
    )
    usage_status: Mapped[SourceUsageStatus] = mapped_column(
        enum_column(SourceUsageStatus, "source_usage_status"),
        default=SourceUsageStatus.ACTIVE,
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class TechnicalEvidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "technical_evidence"

    vehicle_variant_id: Mapped[str] = mapped_column(ForeignKey("vehicle_variants.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_records.id"), index=True)
    category: Mapped[EvidenceCategory] = mapped_column(
        enum_column(EvidenceCategory, "evidence_category"), index=True
    )
    title: Mapped[str] = mapped_column(String(240))
    statement: Mapped[str] = mapped_column(Text)
    status: Mapped[EvidenceStatus] = mapped_column(
        enum_column(EvidenceStatus, "evidence_status"), index=True
    )
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        enum_column(ConfidenceLevel, "evidence_confidence")
    )
    market: Mapped[str | None] = mapped_column(String(2))
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    data_origin: Mapped[DataOrigin] = mapped_column(
        enum_column(DataOrigin, "evidence_data_origin"), default=DataOrigin.REAL, index=True
    )

    vehicle_variant: Mapped[VehicleVariant] = relationship(back_populates="technical_evidence")
    source: Mapped[SourceRecord] = relationship()


class KnownIssue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "known_issues"

    vehicle_variant_id: Mapped[str] = mapped_column(ForeignKey("vehicle_variants.id"), index=True)
    component: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text)
    affected_variants: Mapped[dict] = mapped_column(JSON, default=dict)
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    symptoms: Mapped[list] = mapped_column(JSON, default=list)
    consequences: Mapped[str | None] = mapped_column(Text)
    typical_mileage_min: Mapped[int | None] = mapped_column(Integer)
    typical_mileage_max: Mapped[int | None] = mapped_column(Integer)
    severity: Mapped[Severity] = mapped_column(enum_column(Severity, "issue_severity"))
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    source_count: Mapped[int] = mapped_column(Integer, default=1)
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        enum_column(ConfidenceLevel, "issue_confidence")
    )
    inspection_recommendation: Mapped[str] = mapped_column(Text)
    status: Mapped[EvidenceStatus] = mapped_column(
        enum_column(EvidenceStatus, "known_issue_status")
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    data_origin: Mapped[DataOrigin] = mapped_column(
        enum_column(DataOrigin, "known_issue_data_origin"), default=DataOrigin.REAL, index=True
    )

    vehicle_variant: Mapped[VehicleVariant] = relationship(back_populates="known_issues")


class MarketListing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "market_listings"
    __table_args__ = (UniqueConstraint("source_id", "external_key"),)

    vehicle_variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_variants.id"), index=True
    )
    source_id: Mapped[str] = mapped_column(ForeignKey("source_records.id"), index=True)
    external_key: Mapped[str] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(2), index=True)
    city: Mapped[str | None] = mapped_column(String(120), index=True)
    make: Mapped[str] = mapped_column(String(120), index=True)
    model: Mapped[str] = mapped_column(String(120), index=True)
    generation: Mapped[str | None] = mapped_column(String(120))
    year: Mapped[int] = mapped_column(Integer)
    engine: Mapped[str | None] = mapped_column(String(160))
    displacement_l: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    transmission: Mapped[str | None] = mapped_column(String(120))
    drivetrain: Mapped[str | None] = mapped_column(String(40))
    mileage_km: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3))
    url: Mapped[str] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    data_origin: Mapped[DataOrigin] = mapped_column(
        enum_column(DataOrigin, "market_listing_data_origin"), default=DataOrigin.REAL, index=True
    )

    source: Mapped[SourceRecord] = relationship()


class LocalCostItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "local_cost_items"

    source_id: Mapped[str] = mapped_column(ForeignKey("source_records.id"), index=True)
    country: Mapped[str] = mapped_column(String(2), index=True)
    city: Mapped[str | None] = mapped_column(String(120), index=True)
    vehicle_variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_variants.id"), index=True
    )
    applicability: Mapped[dict] = mapped_column(JSON, default=dict)
    category: Mapped[str] = mapped_column(String(100), index=True)
    operation: Mapped[str] = mapped_column(String(200))
    part_price_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    part_price_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    labor_price_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    labor_price_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    updated_at_source: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    data_origin: Mapped[DataOrigin] = mapped_column(
        enum_column(DataOrigin, "local_cost_data_origin"), default=DataOrigin.REAL, index=True
    )

    source: Mapped[SourceRecord] = relationship()


class OwnerEvidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "owner_evidence"
    __table_args__ = (UniqueConstraint("vehicle_variant_id", "dedupe_key"),)
    applicability: Mapped[dict] = mapped_column(JSON, default=dict)
    applicability_class: Mapped[str] = mapped_column(String(20), default="UNKNOWN")

    source_id: Mapped[str] = mapped_column(ForeignKey("source_records.id"), index=True)
    vehicle_variant_id: Mapped[str] = mapped_column(ForeignKey("vehicle_variants.id"), index=True)
    owner_identity_key: Mapped[str | None] = mapped_column(String(200))
    material_identity_key: Mapped[str] = mapped_column(String(200), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(64), index=True)
    mileage_km: Mapped[int | None] = mapped_column(Integer)
    component: Mapped[str] = mapped_column(String(100), index=True)
    topic: Mapped[str] = mapped_column(String(120), index=True)
    sentiment: Mapped[Sentiment] = mapped_column(enum_column(Sentiment, "owner_sentiment"))
    issue_type: Mapped[str | None] = mapped_column(String(120))
    excerpt: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    data_origin: Mapped[DataOrigin] = mapped_column(
        enum_column(DataOrigin, "owner_evidence_data_origin"), default=DataOrigin.REAL, index=True
    )

    source: Mapped[SourceRecord] = relationship()


from app.models.catalog import VehicleVariant  # noqa: E402

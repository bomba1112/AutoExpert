from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
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
    DisplayLevel,
    EvidenceCategory,
    EvidenceStatus,
    IssueProbability,
    MaintenanceAction,
    MaintenanceCondition,
    MaintenanceOccurrence,
    MaintenanceSystem,
    ScopeLevel,
    Sentiment,
    Severity,
    SourceTier,
    SourceUsageStatus,
)


def enum_column(enum_type: type, name: str, length: int | None = None) -> Enum:
    return Enum(enum_type, name=name, native_enum=False, validate_strings=True, length=length)


class ScopedFactMixin:
    """f087 scope columns: where a fact is defined, independent of one model-year variant."""

    scope_level: Mapped[ScopeLevel | None] = mapped_column(
        enum_column(ScopeLevel, "scope_level", 20), index=True
    )
    make_id: Mapped[str | None] = mapped_column(ForeignKey("vehicle_makes.id"), index=True)
    generation_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_generations.id"), index=True
    )
    # Normalized factory family key confirmed by a source (e.g. A25A-FKS); never an EPA code.
    engine_family_key: Mapped[str | None] = mapped_column(String(40), index=True)
    transmission_key: Mapped[str | None] = mapped_column(String(40), index=True)
    # f096: hybrid system component key (CN catalogue, e.g. byd_dmi_4.0).
    hybrid_system_key: Mapped[str | None] = mapped_column(String(40), index=True)
    year_from: Mapped[int | None] = mapped_column(Integer)
    year_to: Mapped[int | None] = mapped_column(Integer)
    display_level: Mapped[DisplayLevel | None] = mapped_column(
        enum_column(DisplayLevel, "display_level", 20)
    )
    natural_key: Mapped[str | None] = mapped_column(String(64), unique=True)


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


class TechnicalEvidence(ScopedFactMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "technical_evidence"
    __table_args__ = (
        Index("ix_technical_evidence_years", "year_from", "year_to"),
        Index("ix_technical_evidence_display_level", "display_level"),
    )

    # NULL only for f087 scoped rows (scope_level set); legacy rows always reference a variant.
    vehicle_variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_variants.id"), index=True
    )
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
    configuration_key: Mapped[str | None] = mapped_column(String(180), index=True)
    fact_key: Mapped[str | None] = mapped_column(String(100), index=True)
    value: Mapped[object | None] = mapped_column(JSON)
    unit: Mapped[str | None] = mapped_column(String(30))
    raw_document_id: Mapped[str | None] = mapped_column(ForeignKey("raw_documents.id"))
    locator: Mapped[str | None] = mapped_column(String(500))

    vehicle_variant: Mapped[VehicleVariant | None] = relationship(
        back_populates="technical_evidence"
    )
    source: Mapped[SourceRecord] = relationship()


class KnownIssue(ScopedFactMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "known_issues"
    __table_args__ = (Index("ix_known_issues_years", "year_from", "year_to"),)

    # NULL only for f087 scoped issues (engine / transmission / generation + years).
    vehicle_variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_variants.id"), index=True
    )
    component: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text)
    affected_variants: Mapped[dict] = mapped_column(JSON, default=dict)
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    symptoms: Mapped[list] = mapped_column(JSON, default=list)
    consequences: Mapped[str | None] = mapped_column(Text)
    typical_mileage_min: Mapped[int | None] = mapped_column(Integer)
    typical_mileage_max: Mapped[int | None] = mapped_column(Integer)
    # NULL only for f090 owner-review issues that state no severity (CN catalogue); hidden.
    severity: Mapped[Severity | None] = mapped_column(enum_column(Severity, "issue_severity"))
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
    market: Mapped[str | None] = mapped_column(String(2), index=True)
    title: Mapped[str | None] = mapped_column(String(240))
    cause: Mapped[str | None] = mapped_column(Text)
    typical_fix: Mapped[str | None] = mapped_column(Text)
    probability: Mapped[IssueProbability | None] = mapped_column(
        enum_column(IssueProbability, "issue_probability", 12)
    )

    vehicle_variant: Mapped[VehicleVariant | None] = relationship(back_populates="known_issues")


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


class MaintenanceScheduleItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One scheduled maintenance job from an official schedule (f087).

    Intervals are metric; the source's original mileage is kept for audit. Onboard
    systems (oil-life monitors) keep only the manual's stated maximum, never an
    invented fixed interval.
    """

    __tablename__ = "maintenance_schedule_items"
    __table_args__ = (Index("ix_maintenance_schedule_items_years", "year_from", "year_to"),)

    market: Mapped[str] = mapped_column(String(2), index=True)
    make_id: Mapped[str] = mapped_column(ForeignKey("vehicle_makes.id"), index=True)
    model_id: Mapped[str | None] = mapped_column(ForeignKey("vehicle_models.id"), index=True)
    generation_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_generations.id"), index=True
    )
    engine_family_key: Mapped[str | None] = mapped_column(String(40), index=True)
    transmission_key: Mapped[str | None] = mapped_column(String(40), index=True)
    year_from: Mapped[int] = mapped_column(Integer)
    year_to: Mapped[int] = mapped_column(Integer)
    applicability: Mapped[dict] = mapped_column(JSON, default=dict)
    schedule_system: Mapped[MaintenanceSystem] = mapped_column(
        enum_column(MaintenanceSystem, "maintenance_system", 20)
    )
    job: Mapped[str] = mapped_column(String(40), index=True)
    action: Mapped[MaintenanceAction] = mapped_column(
        enum_column(MaintenanceAction, "maintenance_action", 12)
    )
    condition: Mapped[MaintenanceCondition] = mapped_column(
        enum_column(MaintenanceCondition, "maintenance_condition", 10)
    )
    occurrence: Mapped[MaintenanceOccurrence] = mapped_column(
        enum_column(MaintenanceOccurrence, "maintenance_occurrence", 12)
    )
    interval_km: Mapped[int | None] = mapped_column(Integer)
    interval_months: Mapped[int | None] = mapped_column(Integer)
    interval_miles_original: Mapped[int | None] = mapped_column(Integer)
    rule: Mapped[str | None] = mapped_column(String(20))
    max_interval_km: Mapped[int | None] = mapped_column(Integer)
    max_interval_months: Mapped[int | None] = mapped_column(Integer)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_records.id"), index=True)
    raw_document_id: Mapped[str | None] = mapped_column(ForeignKey("raw_documents.id"))
    locator: Mapped[str] = mapped_column(String(500))
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        enum_column(ConfidenceLevel, "maintenance_confidence")
    )
    status: Mapped[EvidenceStatus] = mapped_column(
        enum_column(EvidenceStatus, "maintenance_status")
    )
    display_level: Mapped[DisplayLevel] = mapped_column(
        enum_column(DisplayLevel, "maintenance_display_level", 20)
    )
    notes: Mapped[str | None] = mapped_column(Text)
    natural_key: Mapped[str] = mapped_column(String(64), unique=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    data_origin: Mapped[DataOrigin] = mapped_column(
        enum_column(DataOrigin, "maintenance_data_origin"), default=DataOrigin.REAL
    )

    source: Mapped[SourceRecord] = relationship()


from app.models.catalog import VehicleVariant  # noqa: E402

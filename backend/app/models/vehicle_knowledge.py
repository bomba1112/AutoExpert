from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    ChatAccessMode,
    ChatRole,
    DataOrigin,
    EntitlementStatus,
    EntitlementType,
    EvidenceStatus,
    OdometerRisk,
)

vehicle_profile_sources = Table(
    "vehicle_profile_sources",
    Base.metadata,
    Column(
        "profile_id",
        String(36),
        ForeignKey("vehicle_knowledge_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "source_id",
        String(36),
        ForeignKey("source_records.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


vehicle_profile_evidence = Table(
    "vehicle_profile_evidence",
    Base.metadata,
    Column(
        "profile_id",
        String(36),
        ForeignKey("vehicle_knowledge_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "evidence_id",
        String(36),
        ForeignKey("technical_evidence.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class VehicleKnowledgeProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_knowledge_profiles"
    # Immutable profile revisions may share model/engine/transmission. They must
    # not merge different VINs, drives, trims, HEV/PHEV variants or fresh research.

    vehicle_variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_variants.id"), index=True
    )
    make: Mapped[str] = mapped_column(String(120), index=True)
    model: Mapped[str] = mapped_column(String(120), index=True)
    generation: Mapped[str] = mapped_column(String(120), index=True)
    production_year_start: Mapped[int | None] = mapped_column(Integer)
    production_year_end: Mapped[int | None] = mapped_column(Integer)
    market: Mapped[str] = mapped_column(String(12), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    engine: Mapped[str | None] = mapped_column(String(160))
    engine_code: Mapped[str | None] = mapped_column(String(80), index=True)
    transmission: Mapped[str | None] = mapped_column(String(120))
    drivetrain: Mapped[str | None] = mapped_column(String(40))
    body: Mapped[str | None] = mapped_column(String(60))
    fuel: Mapped[str | None] = mapped_column(String(40))
    profile_version: Mapped[str] = mapped_column(String(30), default="2.0.0")
    freshness_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    dossier_seed: Mapped[dict] = mapped_column(JSON, default=dict)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    data_origin: Mapped[DataOrigin] = mapped_column(
        Enum(DataOrigin, name="vehicle_profile_data_origin", native_enum=False),
        default=DataOrigin.REAL,
        index=True,
    )

    variant: Mapped[VehicleVariant | None] = relationship()
    sources: Mapped[list[SourceRecord]] = relationship(secondary=vehicle_profile_sources)
    evidence: Mapped[list[TechnicalEvidence]] = relationship(secondary=vehicle_profile_evidence)


class VINCheck(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vin_checks"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    vehicle_profile_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_knowledge_profiles.id"), index=True
    )
    normalized_vin: Mapped[str] = mapped_column(String(17), index=True)
    language: Mapped[str] = mapped_column(String(5), default="ru")
    found: Mapped[bool] = mapped_column(Boolean, default=False)
    records_count: Mapped[int] = mapped_column(Integer, default=0)
    photos_count: Mapped[int] = mapped_column(Integer, default=0)
    auctions_count: Mapped[int] = mapped_column(Integer, default=0)
    has_salvage_title: Mapped[bool] = mapped_column(Boolean, default=False)
    odometer_risk: Mapped[OdometerRisk] = mapped_column(
        Enum(OdometerRisk, name="odometer_risk", native_enum=False),
        default=OdometerRisk.UNKNOWN,
    )
    full_history_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    dossier_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    source_snapshot: Mapped[list] = mapped_column(JSON, default=list)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    data_origin: Mapped[DataOrigin] = mapped_column(
        Enum(DataOrigin, name="vin_history_data_origin", native_enum=False),
        default=DataOrigin.REAL,
        index=True,
    )

    profile: Mapped[VehicleKnowledgeProfile | None] = relationship()
    entitlements: Mapped[list[VINEntitlement]] = relationship(
        back_populates="vin_check", cascade="all, delete-orphan"
    )
    chat_context: Mapped[AutoExpertChatContext | None] = relationship(
        back_populates="vin_check", cascade="all, delete-orphan", uselist=False
    )
    chat_sessions: Mapped[list[AutoExpertChatSession]] = relationship(
        back_populates="vin_check", cascade="all, delete-orphan"
    )


class VINEntitlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vin_entitlements"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "vin_check_id",
            "entitlement_type",
            name="uq_vin_entitlement_owner_resource_type",
        ),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    vin_check_id: Mapped[str] = mapped_column(ForeignKey("vin_checks.id"), index=True)
    entitlement_type: Mapped[EntitlementType] = mapped_column(
        Enum(EntitlementType, name="entitlement_type", native_enum=False)
    )
    status: Mapped[EntitlementStatus] = mapped_column(
        Enum(EntitlementStatus, name="entitlement_status", native_enum=False),
        default=EntitlementStatus.ACTIVE,
    )
    provider: Mapped[str] = mapped_column(String(80))
    external_payment_id: Mapped[str | None] = mapped_column(String(200), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    provider_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    vin_check: Mapped[VINCheck] = relationship(back_populates="entitlements")


class AutoExpertChatContext(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auto_expert_chat_contexts"
    __table_args__ = (UniqueConstraint("user_id", "vin_check_id"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    vin_check_id: Mapped[str] = mapped_column(ForeignKey("vin_checks.id"), index=True)
    context_version: Mapped[str] = mapped_column(String(30), default="2.0.0")
    vehicle_profile_snapshot: Mapped[dict] = mapped_column(JSON)
    vin_history_snapshot: Mapped[dict] = mapped_column(JSON)
    report_snapshot: Mapped[dict] = mapped_column(JSON)
    sources_snapshot: Mapped[list] = mapped_column(JSON)
    system_constraints: Mapped[dict] = mapped_column(JSON, default=dict)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    vin_check: Mapped[VINCheck] = relationship(back_populates="chat_context")


class AutoExpertChatSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auto_expert_chat_sessions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    vin_check_id: Mapped[str] = mapped_column(ForeignKey("vin_checks.id"), index=True)
    language: Mapped[str] = mapped_column(String(5))
    context_version: Mapped[str] = mapped_column(String(30), default="2.0.0-chat")
    context_snapshot: Mapped[dict] = mapped_column(JSON)
    context_hash: Mapped[str] = mapped_column(String(64), index=True)
    access_mode: Mapped[ChatAccessMode] = mapped_column(
        Enum(ChatAccessMode, name="chat_access_mode", native_enum=False)
    )
    question_limit: Mapped[int | None] = mapped_column(Integer)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    vin_check: Mapped[VINCheck] = relationship(back_populates="chat_sessions")
    messages: Mapped[list[AutoExpertChatMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AutoExpertChatMessage.sequence",
    )


class AutoExpertChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auto_expert_chat_messages"
    __table_args__ = (UniqueConstraint("session_id", "sequence"),)

    session_id: Mapped[str] = mapped_column(ForeignKey("auto_expert_chat_sessions.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[ChatRole] = mapped_column(
        Enum(ChatRole, name="auto_expert_chat_role", native_enum=False), index=True
    )
    sequence: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[EvidenceStatus | None] = mapped_column(
        Enum(EvidenceStatus, name="chat_evidence_status", native_enum=False)
    )
    source_ids: Mapped[list] = mapped_column(JSON, default=list)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    session: Mapped[AutoExpertChatSession] = relationship(back_populates="messages")


from app.models.catalog import VehicleVariant  # noqa: E402
from app.models.evidence import SourceRecord, TechnicalEvidence  # noqa: E402

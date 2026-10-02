from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataOrigin, EvidenceStatus, ResearchJobStatus


class ResearchJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_jobs"

    worker_queue: Mapped[str | None] = mapped_column(String(30), index=True)
    worker_lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_attempts: Mapped[int] = mapped_column(Integer, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    vehicle_profile_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_knowledge_profiles.id"), index=True
    )
    request_key: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[ResearchJobStatus] = mapped_column(
        Enum(ResearchJobStatus, name="research_job_status", native_enum=False),
        default=ResearchJobStatus.QUEUED,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(5), default="ru")
    requested_vehicle: Mapped[dict] = mapped_column(JSON)
    provider_steps: Mapped[list] = mapped_column(JSON, default=list)
    completed_capabilities: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    resolution_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    dossier_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    profile: Mapped[VehicleKnowledgeProfile | None] = relationship()


class ProviderCacheEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_cache_entries"
    __table_args__ = (
        UniqueConstraint(
            "provider_id",
            "capability",
            "cache_key",
            name="uq_provider_cache_provider_capability_key",
        ),
    )

    provider_id: Mapped[str] = mapped_column(String(80), index=True)
    capability: Mapped[str] = mapped_column(String(80), index=True)
    cache_key: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[EvidenceStatus] = mapped_column(
        Enum(EvidenceStatus, name="provider_cache_evidence_status", native_enum=False)
    )
    source_url: Mapped[str] = mapped_column(Text)
    normalized_payload: Mapped[list] = mapped_column(JSON, default=list)
    raw_payload: Mapped[dict | list] = mapped_column(JSON, default=dict)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    data_origin: Mapped[DataOrigin] = mapped_column(
        Enum(DataOrigin, name="provider_cache_data_origin", native_enum=False),
        default=DataOrigin.REAL,
        index=True,
    )


from app.models.vehicle_knowledge import VehicleKnowledgeProfile  # noqa: E402

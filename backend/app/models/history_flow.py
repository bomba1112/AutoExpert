"""Isolated VIN-history checkout data. Catalog and legacy VIN tables are untouched."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VinCheckRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vin_check_requests"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "vin",
            "provider_id",
            "product",
            name="uq_vin_history_owner_vin_provider_product",
        ),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    vin: Mapped[str] = mapped_column(String(17), index=True)
    provider_id: Mapped[str] = mapped_column(String(80))
    product: Mapped[str] = mapped_column(String(80), default="VIN_HISTORY")
    language: Mapped[str] = mapped_column(String(5), default="ru")
    status: Mapped[str] = mapped_column(String(32), default="CREATED", index=True)
    vehicle_identity: Mapped[dict] = mapped_column(JSON, default=dict)
    preview: Mapped[dict] = mapped_column(JSON, default=dict)
    quote: Mapped[dict] = mapped_column(JSON, default=dict)
    failure_code: Mapped[str | None] = mapped_column(String(80))
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)

    report: Mapped[VehicleHistoryReport | None] = relationship(
        back_populates="request", uselist=False
    )


class ProviderCapabilitySnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_capability_snapshots"
    __table_args__ = (UniqueConstraint("request_id", name="uq_provider_capability_request"),)

    request_id: Mapped[str] = mapped_column(ForeignKey("vin_check_requests.id"), index=True)
    provider_id: Mapped[str] = mapped_column(String(80))
    capabilities: Mapped[dict] = mapped_column(JSON)


class ProviderTransaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_transactions"
    __table_args__ = (
        UniqueConstraint("request_id", "kind", name="uq_provider_transaction_request_kind"),
        UniqueConstraint("idempotency_key", name="uq_provider_transaction_idempotency"),
    )

    request_id: Mapped[str] = mapped_column(ForeignKey("vin_check_requests.id"), index=True)
    provider_id: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(20))  # MOCK_PAYMENT or REPORT
    status: Mapped[str] = mapped_column(String(30))
    idempotency_key: Mapped[str] = mapped_column(String(120))
    external_id: Mapped[str | None] = mapped_column(String(200))
    # Only provider payload; never project this column to the consumer API.
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    failure_code: Mapped[str | None] = mapped_column(String(80))


class VehicleHistoryReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_history_reports"
    __table_args__ = (UniqueConstraint("request_id", name="uq_vehicle_history_report_request"),)

    request_id: Mapped[str] = mapped_column(ForeignKey("vin_check_requests.id"), index=True)
    provider_id: Mapped[str] = mapped_column(String(80))
    provider_report_id: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="REPORT_READY")
    vehicle_identity: Mapped[dict] = mapped_column(JSON, default=dict)
    normalized_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    source_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    request: Mapped[VinCheckRequest] = relationship(back_populates="report")


class HistoryEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "history_events"
    __table_args__ = (
        UniqueConstraint(
            "report_id", "source_record_id", "event_type", name="uq_history_event_source_type"
        ),
    )

    report_id: Mapped[str] = mapped_column(ForeignKey("vehicle_history_reports.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    event_date: Mapped[str | None] = mapped_column(String(10))
    country: Mapped[str | None] = mapped_column(String(3))
    state: Mapped[str | None] = mapped_column(String(60))
    mileage: Mapped[int | None] = mapped_column(Integer)
    mileage_unit: Mapped[str | None] = mapped_column(String(5))
    source_provider: Mapped[str] = mapped_column(String(80))
    source_record_id: Mapped[str] = mapped_column(String(160))
    normalized_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_locator: Mapped[str] = mapped_column(String(300))
    confidence: Mapped[str] = mapped_column(String(20), default="SOURCE_REPORTED")
    status: Mapped[str] = mapped_column(String(30), default="REPORTED")


class _TypedHistoryEvent:
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    history_event_id: Mapped[str] = mapped_column(ForeignKey("history_events.id"), unique=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class OdometerEvent(_TypedHistoryEvent, Base):
    __tablename__ = "odometer_events"


class DamageEvent(_TypedHistoryEvent, Base):
    __tablename__ = "damage_events"


class AuctionEvent(_TypedHistoryEvent, Base):
    __tablename__ = "auction_events"


class TitleEvent(_TypedHistoryEvent, Base):
    __tablename__ = "title_events"


class RegistrationEvent(_TypedHistoryEvent, Base):
    __tablename__ = "registration_events"


class TheftEvent(_TypedHistoryEvent, Base):
    __tablename__ = "theft_events"


class HistoryAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "history_assets"
    __table_args__ = (
        UniqueConstraint("report_id", "source_record_id", name="uq_history_asset_source"),
    )

    report_id: Mapped[str] = mapped_column(ForeignKey("vehicle_history_reports.id"), index=True)
    event_id: Mapped[str | None] = mapped_column(ForeignKey("history_events.id"))
    source_record_id: Mapped[str] = mapped_column(String(160))
    media_type: Mapped[str] = mapped_column(String(80))
    photo_type: Mapped[str] = mapped_column(String(32), default="UNKNOWN_PHOTO_TYPE")
    display_rights_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[bytes | None] = mapped_column(LargeBinary)
    caption: Mapped[dict] = mapped_column(JSON, default=dict)


class ReportEntitlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "history_report_entitlements"
    __table_args__ = (
        UniqueConstraint("user_id", "request_id", name="uq_history_entitlement_owner_request"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("vin_check_requests.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    payment_transaction_id: Mapped[str] = mapped_column(ForeignKey("provider_transactions.id"))


class CostLedgerEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "history_cost_ledger"
    __table_args__ = (UniqueConstraint("request_id", "kind", name="uq_history_cost_request_kind"),)

    request_id: Mapped[str] = mapped_column(ForeignKey("vin_check_requests.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    currency: Mapped[str] = mapped_column(String(3))
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)

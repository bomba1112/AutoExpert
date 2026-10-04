# ruff: noqa: E501
"""The Garage (product phase, stage 2): the owner's cars, odometer readings, service log, the
"My car" feed and recall notices found by the daily NHTSA check.

Distances are stored in kilometres; the display follows the language (app.services.unit_display).
A car is bound to one configuration of the US technical database (technical_evidence
configuration_key); everything the Garage advises comes from that configuration's published rows.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GarageVehicle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "garage_vehicles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    configuration_key: Mapped[str | None] = mapped_column(String(200), index=True)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    vin: Mapped[str | None] = mapped_column(String(17))
    vin_decode: Mapped[dict | None] = mapped_column(JSON)
    nickname: Mapped[str | None] = mapped_column(String(80))
    # US / AZ / CIS: the region sets the default conditions (AZ / CIS severe, US normal)
    region: Mapped[str] = mapped_column(String(8), default="US", nullable=False)
    conditions: Mapped[str] = mapped_column(String(10), default="NORMAL", nullable=False)
    conditions_by_owner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    in_service_date: Mapped[date | None] = mapped_column(Date)
    monthly_km: Mapped[int | None] = mapped_column(Integer)
    # engine oil: the owner sets the interval (the manual's value is only a hint)
    oil_interval_km: Mapped[int | None] = mapped_column(Integer)
    oil_interval_months: Mapped[int | None] = mapped_column(Integer)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    readings: Mapped[list[GarageOdometerReading]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", order_by="GarageOdometerReading.read_on")
    records: Mapped[list[GarageServiceRecord]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", order_by="GarageServiceRecord.created_at")
    feed: Mapped[list[GarageFeedItem]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")


class GarageOdometerReading(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "garage_odometer_readings"

    vehicle_id: Mapped[str] = mapped_column(ForeignKey("garage_vehicles.id", ondelete="CASCADE"), index=True, nullable=False)
    km: Mapped[int] = mapped_column(Integer, nullable=False)
    read_on: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="OWNER", nullable=False)  # OWNER / SERVICE_LOG

    vehicle: Mapped[GarageVehicle] = relationship(back_populates="readings")


class GarageServiceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One job in the owner's log. status DONE: done on that date / mileage; UNKNOWN: the owner
    does not know when it was last done ("не знаю"); ONBOARD_RESET: the car's own system asked
    for service and the owner reset it."""

    __tablename__ = "garage_service_records"

    vehicle_id: Mapped[str] = mapped_column(ForeignKey("garage_vehicles.id", ondelete="CASCADE"), index=True, nullable=False)
    job: Mapped[str] = mapped_column(String(60), nullable=False)
    action: Mapped[str] = mapped_column(String(20), default="REPLACE", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DONE", nullable=False)
    performed_on: Mapped[date | None] = mapped_column(Date)
    odometer_km: Mapped[int | None] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text)

    vehicle: Mapped[GarageVehicle] = relationship(back_populates="records")


class GarageFeedItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The "My car" feed. key makes an item unique per car (one notice per recall / due job)."""

    __tablename__ = "garage_feed_items"
    __table_args__ = (UniqueConstraint("vehicle_id", "key", name="uq_garage_feed_items_vehicle_key"),)

    vehicle_id: Mapped[str] = mapped_column(ForeignKey("garage_vehicles.id", ondelete="CASCADE"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    key: Mapped[str] = mapped_column(String(200), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    vehicle: Mapped[GarageVehicle] = relationship(back_populates="feed")


class GarageRecallNotice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A campaign the daily NHTSA check found for a make / model / year in someone's garage that
    the US technical database does not have yet. Kept as NHTSA states it; not a database fact."""

    __tablename__ = "garage_recall_notices"
    __table_args__ = (UniqueConstraint("campaign_number", "make", "model", "year", name="uq_garage_recall_notices_campaign"),)

    campaign_number: Mapped[str] = mapped_column(String(40), nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    component: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    remedy: Mapped[str | None] = mapped_column(Text)
    report_date: Mapped[str | None] = mapped_column(String(20))
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

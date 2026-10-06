# ruff: noqa: E501
"""The subscription "my car under the expert's eye" (product phase, stage 6): the user's plan
state. No real payment is taken here: the stores (App Store / Google Play) are connected at
deployment; until then a purchase is a stub available only outside production."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Subscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default="PREMIUM", nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False)  # TRIAL / ACTIVE / CANCELED / EXPIRED
    store: Mapped[str] = mapped_column(String(15), nullable=False)  # TRIAL / APP_STORE / GOOGLE_PLAY / STUB
    region: Mapped[str] = mapped_column(String(8), nullable=False)
    price_minor: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str | None] = mapped_column(String(3))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(200))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

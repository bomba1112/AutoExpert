# ruff: noqa: E501
"""The AI mechanic's request log (product phase, stage 3): every question, the answer as checked
and shown, what the check removed, the model, tokens and time. The log is what the per-user limit
counts."""

from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIMechanicRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_mechanic_requests"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("garage_vehicles.id", ondelete="SET NULL"), index=True)
    configuration_key: Mapped[str | None] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)  # CLAUDE / DATA_ONLY
    model: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # OK / REFUSED / ERROR
    answer: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    rejected: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)

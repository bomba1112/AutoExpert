from __future__ import annotations

from decimal import Decimal

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PaymentStatus, ReportStatus


class AnalysisRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analysis_requests"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    vehicle_variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("vehicle_variants.id"), index=True
    )
    country: Mapped[str] = mapped_column(String(2), index=True)
    city: Mapped[str | None] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(5))
    vehicle_input: Mapped[dict] = mapped_column(JSON)
    usage_profile: Mapped[dict] = mapped_column(JSON)
    selected_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    mileage_km: Mapped[int | None] = mapped_column(Integer)

    user: Mapped[User] = relationship(back_populates="analysis_requests")
    reports: Mapped[list[Report]] = relationship(back_populates="analysis_request")


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    analysis_request_id: Mapped[str] = mapped_column(ForeignKey("analysis_requests.id"), index=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status", native_enum=False),
        default=ReportStatus.PREVIEW,
    )
    language: Mapped[str] = mapped_column(String(5))
    report_version: Mapped[str] = mapped_column(String(30), default="1.0.0")
    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    input_snapshot: Mapped[dict] = mapped_column(JSON)
    evidence_bundle: Mapped[dict] = mapped_column(JSON)
    calculated_data: Mapped[dict] = mapped_column(JSON)
    generated_sections: Mapped[dict] = mapped_column(JSON)
    methodology_version: Mapped[str] = mapped_column(String(30), default="mvp-1")

    user: Mapped[User] = relationship(back_populates="reports")
    analysis_request: Mapped[AnalysisRequest] = relationship(back_populates="reports")
    questions: Mapped[list[ReportQuestion]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
    payments: Mapped[list[Payment]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class ReportQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "report_questions"

    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text)
    evidence_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    succeeded: Mapped[bool] = mapped_column(Boolean, default=False)

    report: Mapped[Report] = relationship(back_populates="questions")


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    external_payment_id: Mapped[str | None] = mapped_column(String(200), index=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", native_enum=False),
        default=PaymentStatus.PENDING,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    provider_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    report: Mapped[Report] = relationship(back_populates="payments")


from app.models.user import User  # noqa: E402

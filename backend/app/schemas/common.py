from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    ConfidenceLevel,
    DataOrigin,
    EvidenceStatus,
    SourceTier,
    SourceUsageStatus,
)

SupportedLanguage = Literal["az", "ru", "en"]
CountryCode = Annotated[str, Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")]
CurrencyCode = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")]


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class SourceSnapshot(APIModel):
    id: str
    title: str
    publisher: str
    url: str
    source_type: str
    source_tier: SourceTier = SourceTier.B
    data_origin: DataOrigin = DataOrigin.REAL
    market: str | None = None
    language: str | None = None
    published_at: str | None = None
    retrieved_at: str
    confidence: ConfidenceLevel
    usage_status: SourceUsageStatus | None = None
    is_demo: bool = False
    applicability_summary: str | None = None


class EvidenceItem(APIModel):
    id: str
    category: str
    title: str
    statement: str
    status: EvidenceStatus
    confidence: ConfidenceLevel
    source_ids: list[str] = Field(default_factory=list)
    conditions: dict = Field(default_factory=dict)
    is_demo: bool = False
    data_origin: DataOrigin = DataOrigin.REAL

    @model_validator(mode="after")
    def confirmed_requires_a_source(self) -> EvidenceItem:
        if self.status == EvidenceStatus.CONFIRMED and not self.source_ids:
            raise ValueError("CONFIRMED evidence must reference at least one source")
        return self


class MoneyRange(APIModel):
    low: Decimal = Field(ge=0)
    high: Decimal = Field(ge=0)
    currency: CurrencyCode

    @model_validator(mode="after")
    def high_must_not_be_below_low(self) -> MoneyRange:
        if self.high < self.low:
            raise ValueError("high must be greater than or equal to low")
        return self


class MessageResponse(APIModel):
    message: str

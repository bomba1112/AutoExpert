from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from app.models.enums import ConfidenceLevel, EvidenceStatus
from app.schemas.common import APIModel, CountryCode, CurrencyCode


class MarketVehicle(APIModel):
    country: CountryCode
    city: str | None = None
    make: str
    model: str
    generation: str | None = None
    year: int = Field(ge=1950, le=2100)
    engine: str | None = None
    displacement_l: Decimal | None = Field(default=None, gt=0, le=20)
    transmission: str | None = None
    drivetrain: str | None = None
    mileage_km: int | None = Field(default=None, ge=0, le=5_000_000)
    selected_price: Decimal | None = Field(default=None, gt=0)
    currency: CurrencyCode


class MarketListingInput(APIModel):
    id: str
    country: CountryCode
    city: str | None = None
    make: str
    model: str
    generation: str | None = None
    year: int = Field(ge=1950, le=2100)
    engine: str | None = None
    displacement_l: Decimal | None = Field(default=None, gt=0, le=20)
    transmission: str | None = None
    drivetrain: str | None = None
    mileage_km: int | None = Field(default=None, ge=0, le=5_000_000)
    price: Decimal = Field(gt=0)
    currency: CurrencyCode
    observed_at: str
    source_id: str | None = None
    url: str | None = None
    is_demo: bool = False


class MarketAnalysis(APIModel):
    status: EvidenceStatus
    confidence: ConfidenceLevel
    sample_count: int = 0
    comparable_count: int = 0
    used_count: int = 0
    excluded_outlier_count: int = 0
    median: Decimal | None = None
    market_range_low: Decimal | None = None
    market_range_high: Decimal | None = None
    selected_price: Decimal | None = None
    absolute_deviation: Decimal | None = None
    percentage_deviation: Decimal | None = None
    currency: CurrencyCode
    assumptions: list[str] = Field(default_factory=list)
    matched_listing_ids: list[str] = Field(default_factory=list)

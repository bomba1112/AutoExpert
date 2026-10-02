from __future__ import annotations

from decimal import Decimal

from pydantic import Field, model_validator

from app.models.enums import EvidenceStatus
from app.schemas.common import APIModel, CurrencyCode, MoneyRange


class ConsumptionRange(APIModel):
    city_low: Decimal = Field(gt=0, le=100)
    city_high: Decimal = Field(gt=0, le=100)
    highway_low: Decimal = Field(gt=0, le=100)
    highway_high: Decimal = Field(gt=0, le=100)

    @model_validator(mode="after")
    def ranges_are_ordered(self) -> ConsumptionRange:
        if self.city_high < self.city_low or self.highway_high < self.highway_low:
            raise ValueError("consumption range highs must be >= lows")
        return self


class PlannedCost(APIModel):
    name: str
    low: Decimal = Field(ge=0)
    high: Decimal = Field(ge=0)
    required_first_year: bool = False
    assumption: str

    @model_validator(mode="after")
    def range_is_ordered(self) -> PlannedCost:
        if self.high < self.low:
            raise ValueError("planned cost high must be >= low")
        return self


class OwnershipCostInput(APIModel):
    monthly_mileage_km: int = Field(ge=0, le=100_000)
    city_share: Decimal = Field(ge=0, le=1)
    consumption: ConsumptionRange | None
    fuel_price_per_liter: Decimal | None = Field(default=None, gt=0)
    currency: CurrencyCode
    planned_costs: list[PlannedCost] = Field(default_factory=list)
    starting_service_costs: list[PlannedCost] = Field(default_factory=list)
    fuel_price_source_date: str | None = None


class OwnershipCostResult(APIModel):
    status: EvidenceStatus
    monthly_fuel: MoneyRange | None = None
    yearly_fuel: MoneyRange | None = None
    planned_maintenance: MoneyRange
    first_year_total: MoneyRange | None = None
    assumptions: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

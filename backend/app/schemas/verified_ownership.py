"""Typed evidence for ownership costs; source facts are separate from user assumptions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, allow_inf_nan=False, validate_default=True
    )


class Material(Strict):
    key: str
    quantity: Decimal = Field(gt=0, le=10000)
    unit: Literal["EACH", "L", "SET", "AXLE"]
    specification: str | None = None
    method: str | None = None


class MaintenanceOperation(Strict):
    operation: str = Field(min_length=1, max_length=100)
    action: Literal["INSPECT", "REPLACE", "CONDITION", "SCENARIO_REPAIR"]
    schedule: Literal["NORMAL", "SEVERE"]
    condition_codes: list[str] = Field(default_factory=list)
    interval_km: Decimal | None = Field(default=None, gt=0, le=1000000)
    interval_months: int | None = Field(default=None, gt=0, le=1200)
    first_km: Decimal | None = Field(default=None, gt=0, le=1000000)
    first_months: int | None = Field(default=None, gt=0, le=1200)
    original_interval: str
    rule: Literal["WHICHEVER_FIRST", "CONDITION_ONLY"] = "WHICHEVER_FIRST"
    materials: list[Material] = Field(default_factory=list, max_length=30)
    labels: dict[str, str]

    @model_validator(mode="after")
    def interval(self):
        if self.rule == "WHICHEVER_FIRST" and not (self.interval_km or self.interval_months):
            raise ValueError("MAINTENANCE_INTERVAL_REQUIRED")
        if set(self.labels) != {"az", "ru"}:
            raise ValueError("AZ_RU_LABELS_REQUIRED")
        return self


class PartFitment(Strict):
    part_number: str
    brand: str
    material_key: str
    relationship: Literal["OEM", "SUPERSESSION", "MANUFACTURER_EQUIVALENT", "SELLER_CLAIM"]
    replaces: str | None = None
    production_from: date | None = None
    production_to: date | None = None
    constraints: dict[str, str] = Field(default_factory=dict)
    identity_basis: str = Field(min_length=10)


class PartPrice(Strict):
    seller_id: str
    original_offer_id: str
    part_number: str
    brand: str
    region: str
    condition: Literal["NEW", "USED", "REMANUFACTURED"]
    unit: Literal["EACH", "L", "SET", "AXLE"]
    package_quantity: Decimal = Field(gt=0, le=10000)
    package_price: Decimal = Field(gt=0, le=1000000, decimal_places=2)
    currency: Literal["AZN"] = "AZN"
    available: bool | None = None
    additional_cost: Decimal | None = Field(default=None, ge=0, le=1000000, decimal_places=2)
    authenticity: Literal["UNVERIFIED", "SELLER_CLAIM", "DOCUMENTED"] = "UNVERIFIED"
    offer_type: Literal["EXACT", "FROM_PRICE"] = "EXACT"


class LaborQuote(Strict):
    seller_id: str
    original_offer_id: str
    region: str
    workshop_type: str
    operation: str
    unit: Literal["OPERATION", "HOUR", "PACKAGE"]
    price_min: Decimal = Field(ge=0, le=1000000, decimal_places=2)
    price_max: Decimal = Field(ge=0, le=1000000, decimal_places=2)
    currency: Literal["AZN"] = "AZN"
    included_operations: list[str] = Field(default_factory=list)
    included_materials: list[str] = Field(default_factory=list)
    overlap_group: str | None = None
    hours: Decimal | None = Field(default=None, gt=0, le=1000)

    @model_validator(mode="after")
    def range(self):
        if self.price_max < self.price_min:
            raise ValueError("INVALID_QUOTE_RANGE")
        return self


class TariffTier(Strict):
    up_to_kwh: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal = Field(ge=0, decimal_places=4)


class EnergyPrice(Strict):
    energy: Literal["AI92", "AI95", "AI98", "DIESEL", "ELECTRICITY"]
    channel: Literal["RETAIL", "HOME", "PUBLIC_AC", "PUBLIC_DC", "SUPPLIER_TO_OPERATOR"]
    provider: str
    region: str = "AZ"
    unit: Literal["L", "kWh"]
    currency: Literal["AZN"] = "AZN"
    unit_price: Decimal | None = Field(default=None, ge=0, decimal_places=4)
    tiers: list[TariffTier] = Field(default_factory=list, max_length=20)
    fixed_monthly: Decimal = Field(default=Decimal(0), ge=0, decimal_places=2)
    regulated: bool
    vat_included: bool | None = None

    @model_validator(mode="after")
    def tariff(self):
        if (self.unit_price is None) == (not self.tiers):
            raise ValueError("ONE_TARIFF_STRUCTURE_REQUIRED")
        if self.energy == "ELECTRICITY" and self.unit != "kWh":
            raise ValueError("INVALID_ENERGY_UNIT")
        if self.energy != "ELECTRICITY" and (self.unit != "L" or self.channel != "RETAIL"):
            raise ValueError("INVALID_FUEL_CHANNEL")
        previous = Decimal(0)
        for i, tier in enumerate(self.tiers):
            if tier.up_to_kwh is None:
                if i != len(self.tiers) - 1:
                    raise ValueError("UNBOUNDED_TIER_MUST_BE_LAST")
            elif tier.up_to_kwh <= previous:
                raise ValueError("TARIFF_TIERS_UNORDERED")
            else:
                previous = tier.up_to_kwh
        if self.tiers and self.tiers[-1].up_to_kwh is not None:
            raise ValueError("FINAL_TIER_UNBOUNDED_REQUIRED")
        return self


DATA_TYPES = {
    "MAINTENANCE": MaintenanceOperation,
    "FITMENT": PartFitment,
    "PART_PRICE": PartPrice,
    "LABOR": LaborQuote,
    "ENERGY_PRICE": EnergyPrice,
}


class OwnershipRecord(Strict):
    external_key: str = Field(min_length=1, max_length=160)
    kind: Literal["MAINTENANCE", "FITMENT", "PART_PRICE", "LABOR", "ENERGY_PRICE"]
    variant_ids: list[str] = Field(default_factory=list, max_length=10000)
    source_url: str = Field(min_length=8, max_length=2000)
    locator: str = Field(min_length=1, max_length=1000)
    observed_at: AwareDatetime
    effective_from: date
    effective_to: date | None = None
    verification: Literal["CONFIRMED", "ESTIMATE", "NEEDS_INSPECTION", "INSUFFICIENT_DATA"]
    limitations: dict[str, str]
    data: dict

    @model_validator(mode="after")
    def validate_data(self):
        if not self.source_url.startswith("https://"):
            raise ValueError("SOURCE_HTTPS_REQUIRED")
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("INVALID_EFFECTIVE_PERIOD")
        if self.kind in {"MAINTENANCE", "FITMENT"} and not self.variant_ids:
            raise ValueError("EXACT_VARIANT_APPLICABILITY_REQUIRED")
        if set(self.limitations) != {"az", "ru"}:
            raise ValueError("AZ_RU_LIMITATIONS_REQUIRED")
        self.data = DATA_TYPES[self.kind].model_validate(self.data).model_dump(mode="json")
        return self


class OperationHistory(Strict):
    operation: str
    never_serviced: bool = False
    last_date: date | None = None
    last_odometer_km: Decimal | None = Field(default=None, ge=0)


class OwnershipScenario(Strict):
    start_date: date
    months: int = Field(default=24, ge=1, le=120)
    monthly_km: Decimal = Field(default=1000, ge=0, le=30000)
    current_odometer_km: Decimal = Field(ge=0, le=5000000)
    first_registration: date | None = None
    region: str = "Baku"
    schedule: Literal["NORMAL", "SEVERE"] = "NORMAL"
    severe_conditions: list[str] = Field(default_factory=list)
    history: list[OperationHistory] = Field(default_factory=list)
    initial_service_assumption: bool = False
    fuel_energy: Literal["AI92", "AI95", "AI98", "DIESEL"] | None = None
    fuel_price_revision_id: str | None = None
    home_tariff_revision_id: str | None = None
    public_tariff_revision_id: str | None = None
    public_channel: Literal["PUBLIC_AC", "PUBLIC_DC"] = "PUBLIC_DC"
    home_share: Decimal = Field(default=1, ge=0, le=1)
    household_monthly_kwh: Decimal | None = Field(default=None, ge=0)
    new_dedicated_meter: bool = False
    electric_distance_share: Decimal | None = Field(default=None, ge=0, le=1)
    consumption_side: Literal["GRID", "BATTERY", "UNKNOWN"] = "UNKNOWN"
    charging_loss_fraction: Decimal | None = Field(default=None, ge=0, lt=1)
    purchase: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    resale: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    repair_reserve: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    other: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    selected_part_prices: list[str] = Field(default_factory=list)
    selected_labor_quotes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def coherence(self):
        if self.schedule == "SEVERE" and not self.severe_conditions:
            raise ValueError("SEVERE_CONDITIONS_REQUIRED")
        if self.first_registration and self.first_registration > self.start_date:
            raise ValueError("REGISTRATION_AFTER_SCENARIO")
        for h in self.history:
            if h.never_serviced and (h.last_date or h.last_odometer_km is not None):
                raise ValueError("CONFLICTING_FIRST_SERVICE_HISTORY")
            if h.last_date and h.last_date > self.start_date:
                raise ValueError("FUTURE_MAINTENANCE_HISTORY")
            if h.last_odometer_km is not None and h.last_odometer_km > self.current_odometer_km:
                raise ValueError("HISTORY_ODOMETER_AFTER_CURRENT")
        if len({h.operation for h in self.history}) != len(self.history):
            raise ValueError("DUPLICATE_MAINTENANCE_HISTORY")
        return self

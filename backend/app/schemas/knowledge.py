from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.schemas.catalog_verification import (
    DocumentaryReference,
    DocumentarySection,
    IdentityVerification,
)
from app.schemas.market_discovery import MarketDiscoveryRecord
from app.schemas.verified_ownership import OwnershipRecord


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class FactInput(StrictModel):
    value: str | int | float | bool
    unit: str | None = Field(default=None, max_length=30)
    status: Literal["CONFIRMED", "ESTIMATE", "NEEDS_INSPECTION", "INSUFFICIENT_DATA"] = "CONFIRMED"
    locator: str = Field(min_length=1, max_length=500)
    source_date: date | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    titles: dict[str, str] = Field(default_factory=dict)
    documentary_source: DocumentaryReference | None = None


class MarketObservationInput(StrictModel):
    source_id: str = Field(min_length=1, max_length=80)
    external_key: str = Field(min_length=1, max_length=160)
    country: str = Field(default="AZ", pattern=r"^[A-Z]{2}$")
    city: str | None = Field(default=None, max_length=100)
    currency: str = Field(default="AZN", pattern=r"^[A-Z]{3}$")
    price: Decimal = Field(gt=0, le=10000000, decimal_places=2)
    mileage_km: int | None = Field(default=None, ge=0, le=10000000)
    observed_at: AwareDatetime
    source_url: str = Field(min_length=8, max_length=2000)
    locator: str = Field(min_length=1, max_length=500)
    identity_basis: str = Field(min_length=10, max_length=1000)

    @model_validator(mode="after")
    def public_observation(self):
        from datetime import UTC, datetime

        if not self.source_url.startswith("https://"):
            raise ValueError("SOURCE_HTTPS_REQUIRED")
        if self.observed_at > datetime.now(UTC):
            raise ValueError("FUTURE_MARKET_OBSERVATION")
        return self


class CatalogRecord(StrictModel):
    external_key: str = Field(min_length=1, max_length=160)
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    configuration: str = Field(min_length=1, max_length=180)
    aliases: list[str] = Field(default_factory=list, max_length=30)
    original_market: str = Field(min_length=2, max_length=24)
    model_year: int = Field(ge=1886, le=2100)
    generation: str | None = Field(default=None, max_length=100)
    generation_code: str | None = Field(default=None, max_length=80)
    facelift: str | None = Field(default=None, max_length=80)
    production_from: date | None = None
    production_to: date | None = None
    assembly_country: str | None = Field(default=None, max_length=2)
    supply_channel: str | None = Field(default=None, max_length=80)
    facts: dict[str, FactInput] = Field(min_length=1, max_length=100)
    source_url: str = Field(min_length=8, max_length=2000)
    source_date: date | None = None
    revision_note: str = Field(default="", max_length=1000)
    identity_verification: IdentityVerification | None = None
    documentary_sections: list[DocumentarySection] = Field(default_factory=list, max_length=30)
    market_observations: list[MarketObservationInput] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def coherent_identity(self):
        if (
            self.production_from
            and self.production_to
            and self.production_to < self.production_from
        ):
            raise ValueError("INVALID_PRODUCTION_INTERVAL")
        if any(not key.replace("_", "").replace(".", "").isalnum() for key in self.facts):
            raise ValueError("INVALID_FACT_KEY")
        if not self.source_url.startswith("https://"):
            raise ValueError("SOURCE_HTTPS_REQUIRED")
        quantities = {
            "engine_displacement": (0, 12, "L"),
            "fuel_combined": (0, 100, "L/100km"),
            "electricity_combined": (0, 500, "kWh/100km"),
            "seats": (1, 100, None),
            "ground_clearance": (0, 1000, "mm"),
            "cargo_l": (0, 20000, "L"),
            "power_kw": (0, 3000, "kW"),
        }
        for key, (minimum, maximum, unit) in quantities.items():
            if key not in self.facts:
                continue
            fact = self.facts[key]
            try:
                quantity = Decimal(str(fact.value))
                valid = quantity.is_finite() and minimum <= quantity <= maximum
            except Exception:
                valid = False
            if not valid or (unit and fact.unit != unit):
                raise ValueError("INVALID_FACT_QUANTITY_OR_UNIT")
        return self


class ImportManifest(StrictModel):
    source_id: str = Field(max_length=80)
    parser: Literal[
        "manifest-json-v1",
        "manifest-csv-v1",
        "epa-csv-v1",
        "ownership-json-v1",
        "ownership-csv-v1",
        "nrcan-csv-v1",
        "market-discovery-json-v1",
        "market-discovery-csv-v1",
    ]
    dataset_kind: Literal["CONVENTIONAL", "BEV", "PHEV"] | None = None
    family_mappings: list[dict[str, str]] = Field(default_factory=list, max_length=1000)
    document_id: str | None = None
    download_url: str | None = Field(default=None, max_length=2000)
    expected_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    year_min: int = Field(default=2016, ge=1886, le=2100)
    year_max: int = Field(default=2026, ge=1886, le=2100)
    makes: list[str] = Field(default_factory=list, max_length=200)
    priority_families: list[str] = Field(default_factory=list, max_length=500)
    family_limit: int = Field(default=120, ge=1, le=10000)
    versions_per_family: int = Field(default=6, ge=1, le=100)
    selection_basis: str = Field(min_length=10, max_length=2000)
    dry_run: bool = False
    records: list[CatalogRecord] = Field(default_factory=list, max_length=10000)
    ownership_records: list[OwnershipRecord] = Field(default_factory=list, max_length=10000)
    market_records: list[MarketDiscoveryRecord] = Field(default_factory=list, max_length=10000)

    @model_validator(mode="after")
    def one_record_family(self):
        if self.market_records and (
            self.parser != "market-discovery-json-v1" or self.records or self.ownership_records
        ):
            raise ValueError("MARKET_DISCOVERY_MANIFEST_REQUIRED")
        if self.parser.startswith("market-discovery-") and (
            self.records or self.ownership_records or self.download_url
        ):
            raise ValueError("PERMITTED_MINIMAL_MARKET_IMPORT_REQUIRED")
        if self.ownership_records and (self.parser != "ownership-json-v1" or self.records):
            raise ValueError("OWNERSHIP_MANIFEST_REQUIRED")
        if self.parser.startswith("ownership-") and self.records:
            raise ValueError("MIXED_RECORD_FAMILIES")
        return self


class BuyerFilters(StrictModel):
    catalog_scope: Literal["ALL", "US_BASE_2000", "US_CONFIRMED_2000"] = "ALL"
    catalog_ready_only: bool = False
    generations: list[str] = Field(default_factory=list, max_length=30)
    budget_max_minor: int | None = Field(default=None, ge=0, le=1000000000)
    budget_min_minor: int | None = Field(default=None, ge=0, le=1000000000)
    initial_service_included: bool | None = None
    year_min: int | None = Field(default=None, ge=1886, le=2100)
    year_max: int | None = Field(default=None, ge=1886, le=2100)
    makes: list[str] = Field(default_factory=list, max_length=30)
    models: list[str] = Field(default_factory=list, max_length=30)
    query: str = Field(default="", max_length=180)
    markets: list[str] = Field(default_factory=list, max_length=30)
    market_preference: Literal["ANY", "UNKNOWN", "SELECTED"] = "UNKNOWN"
    body: list[str] = Field(default_factory=list, max_length=15)
    engine: Literal[
        "ANY",
        "UNKNOWN",
        "GASOLINE_NA",
        "GASOLINE",
        "GASOLINE_TURBO",
        "DIESEL",
        "HEV",
        "PHEV",
        "BEV",
        "MHEV",
        "EREV",
        "FCEV",
    ] = "ANY"
    transmission: Literal[
        "ANY",
        "UNKNOWN",
        "AT",
        "CVT",
        "DCT",
        "MANUAL",
        "AUTOMATIC_UNSPECIFIED",
        "AMT",
        "ECVT",
        "SINGLE_SPEED",
    ] = "ANY"
    drivetrain: str | None = Field(default=None, max_length=25)
    min_seats: int | None = Field(default=None, ge=1, le=30)
    min_clearance_mm: int | None = Field(default=None, ge=0, le=600)
    large_boot: bool = False
    displacement_max_l: Decimal | None = Field(default=None, ge=0, le=12)
    country: str = Field(default="AZ", min_length=2, max_length=2)
    city: str = Field(default="", max_length=100)
    supply_channel: str | None = Field(default=None, max_length=80)
    family_use: bool = False
    roads: list[str] = Field(default_factory=list, max_length=5)
    monthly_km: int = Field(default=1000, ge=0, le=30000)
    ownership_months: int = Field(default=24, ge=1, le=120)
    charging: Literal["YES", "NO", "UNKNOWN"] = "UNKNOWN"
    priorities: list[
        Literal[
            "reliability",
            "cost",
            "comfort",
            "performance",
            "repair",
            "parts",
            "space",
            "safety",
            "resale",
        ]
    ] = Field(default_factory=list, max_length=3)
    sort: Literal["recommended", "year_desc", "make", "consumption"] = "recommended"
    offset: int = Field(default=0, ge=0, le=100000)
    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def ranges(self):
        if self.year_min and self.year_max and self.year_min > self.year_max:
            raise ValueError("YEAR_RANGE")
        if (
            self.budget_min_minor is not None
            and self.budget_max_minor is not None
            and self.budget_min_minor > self.budget_max_minor
        ):
            raise ValueError("BUDGET_RANGE")
        if self.market_preference == "SELECTED" and not self.markets:
            raise ValueError("MARKET_REQUIRED")
        return self


class CostScenario(StrictModel):
    months: int = Field(default=24, ge=1, le=120)
    monthly_km: int = Field(default=1000, ge=0, le=30000)
    region: str = Field(default="AZ", max_length=100)
    price_date: date | None = None
    price_source: str | None = Field(default=None, max_length=1000)
    fuel_price: Decimal | None = Field(default=None, ge=0, le=1000, decimal_places=4)
    electricity_price: Decimal | None = Field(default=None, ge=0, le=1000, decimal_places=4)
    purchase_price: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)
    resale_price: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)
    maintenance: Decimal | None = Field(default=None, ge=0, le=1000000, decimal_places=2)
    repair_reserve: Decimal | None = Field(default=None, ge=0, le=1000000, decimal_places=2)
    other_costs: Decimal | None = Field(default=None, ge=0, le=1000000, decimal_places=2)

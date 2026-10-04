"""Public, non-provider-specific VIN-history checkout contract."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from app.core.vin import VINValidationError, validate_vin
from app.schemas.common import APIModel

HistoryLanguage = Literal["ru", "az", "en"]


class HistoryCheckCreate(APIModel):
    vin: str
    language: HistoryLanguage = "ru"

    @field_validator("vin")
    @classmethod
    def valid_vin(cls, value: str) -> str:
        try:
            return validate_vin(value)
        except VINValidationError as exc:
            raise ValueError(str(exc)) from exc


class HistoryPreview(APIModel):
    available_record_types: list[str] = Field(default_factory=list)
    photo_count: int | None = Field(default=None, ge=0)
    odometer_event_count: int | None = Field(default=None, ge=0)
    damage_records_available: bool | None = None
    title_records_available: bool | None = None
    coverage_limitations: list[str] = Field(default_factory=list)
    content_determined_after_purchase: bool = False


class HistoryQuote(APIModel):
    retail_price_azn: str | None = None
    currency: str = "AZN"
    sellable: bool = False
    reason: str | None = None
    is_mock_scenario: bool = False


class HistoryCheckRead(APIModel):
    check_id: str
    vin: str
    status: str
    vehicle_identity: dict = Field(default_factory=dict)
    preview: HistoryPreview = Field(default_factory=HistoryPreview)
    quote: HistoryQuote = Field(default_factory=HistoryQuote)
    is_unlocked: bool = False
    is_mock: bool = True


class MockHistoryPayment(APIModel):
    simulate_failure: bool = False


class HistoryReportItem(APIModel):
    event_id: str | None = None
    date: str | None = None
    text: str


class HistoryReportSection(APIModel):
    key: str
    title: str
    items: list[HistoryReportItem] = Field(default_factory=list)


class HistoryReportAsset(APIModel):
    id: str
    caption: str | None = None
    event_date: str | None = None
    source: str | None = None
    photo_type: str | None = None


class HistoryReportRead(APIModel):
    check_id: str
    vin: str
    language: HistoryLanguage
    status: str
    vehicle_identity: dict
    sections: list[HistoryReportSection]
    mileage_anomaly: bool
    odometer_points: list[dict] = Field(default_factory=list)
    asset_ids: list[str]
    assets: list[HistoryReportAsset] = Field(default_factory=list)
    is_mock: bool

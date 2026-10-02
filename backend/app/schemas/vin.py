from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, field_validator, model_validator

from app.core.vehicle_identifiers import VehicleIdentifierValidator
from app.models.enums import (
    ConfidenceLevel,
    DataOrigin,
    EvidenceStatus,
    OdometerRisk,
    VehicleIdentifierType,
)
from app.schemas.common import APIModel, SourceSnapshot, SupportedLanguage


class VINPrecheckCreate(APIModel):
    vin: str
    language: SupportedLanguage = "ru"
    market: str = "USA"
    identifier_type: VehicleIdentifierType = VehicleIdentifierType.VIN

    @model_validator(mode="after")
    def identifier_must_be_valid(self) -> VINPrecheckCreate:
        result = VehicleIdentifierValidator().validate(
            self.vin,
            market=self.market,
            identifier_type=self.identifier_type,
        )
        self.vin = result.value
        self.market = result.market
        return self


class RealPilotPrecheckCreate(APIModel):
    language: SupportedLanguage = "ru"
    vin: str | None = Field(default=None, min_length=17, max_length=17)

    @field_validator("vin", mode="before")
    @classmethod
    def normalize_optional_vin(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class VehicleKnowledgeProfileDTO(APIModel):
    id: str
    make: str
    model: str
    generation: str
    production_year_start: int | None
    production_year_end: int | None
    market: str
    year: int
    trim: str | None = None
    engine: str | None
    engine_code: str | None
    transmission: str | None
    drivetrain: str | None
    body: str | None
    fuel: str | None
    profile_version: str
    freshness_at: datetime
    source_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    is_demo: bool
    data_origin: DataOrigin = DataOrigin.REAL


class VINPrecheckTeaser(APIModel):
    check_id: str
    vin: str
    vehicle: VehicleKnowledgeProfileDTO | None
    found: bool
    records_count: int = Field(ge=0)
    photos_count: int = Field(ge=0)
    auctions_count: int = Field(ge=0)
    has_salvage_title: bool
    odometer_risk: OdometerRisk
    details_locked: bool
    can_purchase: bool
    blurred_preview_data_url: str | None = None
    hidden_photos_count: int = Field(ge=0)
    price: Decimal | None = None
    currency: str | None = None
    no_records_message: str | None = None
    caution_message: str | None = None
    demo_notice: str
    is_demo: bool
    developer_mode: bool = False
    simulate_user_paywall: bool = False


class DossierClaim(APIModel):
    text: str
    status: EvidenceStatus
    heading: str | None = None
    why_it_matters: str | None = None
    what_to_check: str | None = None
    applicability: str | None = None
    kind: str = "fact"
    original_available: bool = False
    source_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def grounded_status_must_be_traceable(self) -> DossierClaim:
        if (
            self.status in {EvidenceStatus.CONFIRMED, EvidenceStatus.ESTIMATE}
            and not self.source_ids
        ):
            raise ValueError("Grounded dossier claims must reference a source")
        if self.status == EvidenceStatus.CONFIRMED and not self.evidence_ids:
            raise ValueError("CONFIRMED dossier claims must reference evidence")
        return self


class DossierKnownIssue(APIModel):
    component: str
    description: str
    affected_variant: dict
    symptoms: list[str] = Field(default_factory=list)
    mileage_range: list[int] | None = None
    consequences: str | None = None
    inspection_recommendation: str
    severity: str
    confidence: ConfidenceLevel
    status: EvidenceStatus
    source_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    source_count: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def grounded_issue_must_be_traceable(self) -> DossierKnownIssue:
        if (
            self.status in {EvidenceStatus.CONFIRMED, EvidenceStatus.ESTIMATE}
            and not self.source_ids
        ):
            raise ValueError("Grounded known issues must reference a source")
        if self.status == EvidenceStatus.CONFIRMED and not self.evidence_ids:
            raise ValueError("CONFIRMED known issues must reference evidence")
        return self


class DossierSection(APIModel):
    key: str
    title: str
    summary: str
    claims: list[DossierClaim] = Field(default_factory=list)
    known_issues: list[DossierKnownIssue] = Field(default_factory=list)
    is_empty: bool = False


class VehicleDossier(APIModel):
    dossier_version: str = "2.0.0"
    language: SupportedLanguage
    vehicle: VehicleKnowledgeProfileDTO
    expert_verdict: str
    inspection_notice: str
    sections: list[DossierSection]
    source_ids: list[str]
    generated_at: datetime
    is_demo: bool


class VINHistoryEvent(APIModel):
    date: date
    event_type: str
    summary: str
    status: EvidenceStatus
    source_ids: list[str] = Field(default_factory=list)
    is_demo: bool


class VINAuctionRecord(APIModel):
    date: date
    sale_price: Decimal
    currency: str
    damage: str
    status: EvidenceStatus
    source_ids: list[str] = Field(default_factory=list)
    is_demo: bool


class VINArchivePhoto(APIModel):
    id: str
    label: str
    placeholder: bool
    status: EvidenceStatus
    source_ids: list[str] = Field(default_factory=list)
    is_demo: bool


class VINDamageDetail(APIModel):
    area: str
    description: str
    status: EvidenceStatus
    source_ids: list[str] = Field(default_factory=list)
    is_demo: bool


class VINOdometerRecord(APIModel):
    date: date
    value: int = Field(ge=0)
    unit: str
    status: EvidenceStatus
    source_ids: list[str] = Field(default_factory=list)
    is_demo: bool


class VINHistoryPayload(APIModel):
    vin: str
    timeline: list[VINHistoryEvent]
    auctions: list[VINAuctionRecord]
    photos: list[VINArchivePhoto]
    damage_details: list[VINDamageDetail]
    odometer_records: list[VINOdometerRecord]
    is_demo: bool
    data_origin: DataOrigin = DataOrigin.DEMO


class VINUnlockRequest(APIModel):
    simulate_failure: bool = False


class VINUnlockResponse(APIModel):
    check_id: str
    entitlement_id: str | None = None
    entitlement_type: str
    provider: str
    status: str
    is_unlocked: bool
    amount: Decimal
    currency: str
    is_demo: bool


class VINFullReportResponse(APIModel):
    check_id: str
    vin: str
    vehicle: VehicleKnowledgeProfileDTO
    history: VINHistoryPayload
    dossier: VehicleDossier
    sources: list[SourceSnapshot]
    chat_context_id: str
    entitlement_type: str
    is_demo: bool
    vin_history_origin: DataOrigin = DataOrigin.DEMO
    dossier_origin: DataOrigin = DataOrigin.REAL
    developer_mode: bool = False
    simulate_user_paywall: bool = False
    paid_report: dict | None = None


class VINCheckSummary(APIModel):
    check_id: str
    created_at: datetime
    vin: str
    vehicle: dict | None
    records_count: int
    photos_count: int
    is_unlocked: bool
    is_demo: bool

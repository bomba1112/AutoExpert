from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, model_validator

from app.models.enums import (
    ConfidenceLevel,
    EvidenceStatus,
    FitRating,
    Severity,
)
from app.schemas.common import (
    APIModel,
    CountryCode,
    CurrencyCode,
    EvidenceItem,
    SourceSnapshot,
    SupportedLanguage,
)
from app.schemas.fit import FitAnalysis, UsageProfileInput
from app.schemas.market import MarketAnalysis, MarketListingInput
from app.schemas.ownership import OwnershipCostResult
from app.schemas.reviews import OwnerFeedbackAggregation, OwnerObservation


class VehicleInput(APIModel):
    country: CountryCode
    city: str | None = Field(default=None, max_length=120)
    make: str = Field(min_length=1, max_length=120)
    model: str = Field(min_length=1, max_length=120)
    generation: str | None = Field(default=None, max_length=120)
    year: int = Field(ge=1950, le=2100)
    engine: str | None = Field(default=None, max_length=160)
    transmission: str | None = Field(default=None, max_length=120)
    drivetrain: str | None = Field(default=None, max_length=40)
    mileage_km: int | None = Field(default=None, ge=0, le=5_000_000)
    price: Decimal | None = Field(default=None, gt=0)
    currency: CurrencyCode
    vin: str | None = Field(default=None, min_length=11, max_length=20)
    listing_url: str | None = Field(default=None, max_length=2048)


class AnalysisCreate(APIModel):
    vehicle_variant_id: str | None = None
    vehicle: VehicleInput
    usage_profile: UsageProfileInput
    report_language: SupportedLanguage = "ru"


class VehicleSnapshot(APIModel):
    variant_id: str
    make: str
    model: str
    generation: str
    variant: str
    market: str
    year: int
    engine: str | None = None
    transmission: str | None = None
    drivetrain: str | None = None
    body: str | None = None
    fuel: str | None = None
    displacement_l: Decimal | None = None
    power_kw: Decimal | None = None
    ground_clearance_mm: int | None = None
    source_ids: list[str] = Field(default_factory=list)
    is_demo: bool


class KnownIssueSnapshot(APIModel):
    id: str
    component: str
    description: str
    conditions: dict
    mileage_range: list[int] | None = None
    severity: Severity
    evidence_ids: list[str]
    confidence: ConfidenceLevel
    inspection_recommendation: str
    status: EvidenceStatus
    is_demo: bool = False

    @model_validator(mode="after")
    def confirmed_issue_requires_evidence(self) -> KnownIssueSnapshot:
        if self.status == EvidenceStatus.CONFIRMED and not self.evidence_ids:
            raise ValueError("CONFIRMED known issue must reference evidence")
        return self


class LocalCostSnapshot(APIModel):
    id: str
    category: str
    operation: str
    applicability: dict = Field(default_factory=dict)
    part_price_low: Decimal | None
    part_price_high: Decimal | None
    labor_price_low: Decimal | None
    labor_price_high: Decimal | None
    currency: str
    source_id: str
    updated_at: str
    is_demo: bool = False


class EvidenceBundle(APIModel):
    schema_version: str = "1.0"
    vehicle: VehicleSnapshot
    user_profile: UsageProfileInput
    technical_evidence: list[EvidenceItem]
    known_issues: list[KnownIssueSnapshot]
    market_listings: list[MarketListingInput] = Field(default_factory=list)
    market_analysis: MarketAnalysis
    local_costs: list[LocalCostSnapshot]
    owner_evidence: list[OwnerObservation] = Field(default_factory=list)
    owner_feedback: OwnerFeedbackAggregation
    ownership_calculation: OwnershipCostResult
    fit_analysis: FitAnalysis
    sources: list[SourceSnapshot]
    inspection_notice_status: EvidenceStatus = EvidenceStatus.NEEDS_INSPECTION


class GroundedClaim(APIModel):
    text: str
    status: EvidenceStatus
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def confirmed_claim_is_traceable(self) -> GroundedClaim:
        if self.status == EvidenceStatus.CONFIRMED and not self.evidence_ids:
            raise ValueError("CONFIRMED claim must reference evidence")
        return self


class GeneratedSection(APIModel):
    key: str
    title: str
    summary: str
    claims: list[GroundedClaim] = Field(default_factory=list)


class GeneratedReport(APIModel):
    language: SupportedLanguage
    verdict: FitRating
    verdict_summary: str
    inspection_notice: str
    sections: list[GeneratedSection]


class PreviewResponse(APIModel):
    report_id: str
    vehicle: VehicleSnapshot
    verdict: FitRating
    verdict_summary: str
    highlights: list[GroundedClaim]
    local_market_status: EvidenceStatus
    available_sections: list[str]
    is_unlocked: bool
    is_demo: bool
    price: Decimal | None
    currency: str | None
    country: str
    city: str | None
    comparable_count: int
    used_comparable_count: int
    evidence_count: int
    source_count: int
    pipeline_stages: list[str]


class PaymentUnlockRequest(APIModel):
    simulate_failure: bool = False


class PaymentUnlockResponse(APIModel):
    report_id: str
    payment_id: str | None = None
    provider: str
    status: str
    is_unlocked: bool
    amount: Decimal
    currency: str
    is_demo: bool


class ReportQuestionCreate(APIModel):
    question: str = Field(min_length=2, max_length=1000)


class ReportQuestionItem(APIModel):
    id: str
    question: str
    answer: str
    created_at: datetime


class ReportQuestionResponse(APIModel):
    report_id: str
    item: ReportQuestionItem
    questions_remaining: int


class ReportSummary(APIModel):
    id: str
    created_at: datetime
    status: str
    language: SupportedLanguage
    is_unlocked: bool
    is_demo: bool
    vehicle: dict
    verdict: str


class ReportDetail(APIModel):
    id: str
    created_at: datetime
    status: str
    language: SupportedLanguage
    report_version: str
    is_unlocked: bool
    is_demo: bool
    input_snapshot: dict
    evidence_bundle: dict | None = None
    calculated_data: dict | None = None
    generated_sections: dict
    questions: list[ReportQuestionItem] = Field(default_factory=list)
    questions_remaining: int = 3


class CatalogCountry(APIModel):
    code: str
    currency: str
    cities: list[str]
    is_demo: bool


class CatalogVariant(APIModel):
    id: str
    country: str
    make: str
    model: str
    generation: str
    generation_code: str | None
    year_from: int | None
    year_to: int | None
    engine: str | None
    transmission: str | None
    drivetrain: str | None
    body: str | None
    fuel: str | None
    currency: str
    is_demo: bool


class CatalogResponse(APIModel):
    countries: list[CatalogCountry]
    variants: list[CatalogVariant]

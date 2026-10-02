from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.core.vehicle_identifiers import VehicleIdentifierValidator, normalize_market
from app.models.enums import (
    DataOrigin,
    EvidenceStatus,
    ResearchJobStatus,
    VariantResolutionStatus,
    VehicleIdentifierType,
)
from app.schemas.common import APIModel, SupportedLanguage
from app.schemas.vin import VehicleDossier, VehicleKnowledgeProfileDTO


class VehicleResearchRequest(APIModel):
    make: str | None = Field(default=None, min_length=1, max_length=120)
    model: str | None = Field(default=None, min_length=1, max_length=120)
    year: int | None = Field(default=None, ge=1981, le=2100)
    market: str = Field(default="USA", min_length=2, max_length=12)
    engine_hint: str | None = Field(default=None, max_length=80)
    powertrain_hint: Literal["ICE", "HEV", "PHEV", "BEV", "MHEV"] | None = None
    fuel_hint: Literal["Gasoline", "Diesel", "Electricity"] | None = None
    transmission_hint: str | None = Field(default=None, max_length=80)
    drivetrain_hint: str | None = Field(default=None, max_length=80)
    trim_hint: str | None = Field(default=None, max_length=120)
    vin: str | None = Field(default=None, min_length=11, max_length=17)
    identifier: str | None = Field(default=None, min_length=5, max_length=30)
    identifier_type: VehicleIdentifierType = VehicleIdentifierType.VIN

    @field_validator("make", "model", "market", "engine_hint", "vin", "identifier")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None

    @field_validator("market")
    @classmethod
    def normalize_market(cls, value: str) -> str:
        return normalize_market(value)

    @model_validator(mode="after")
    def valid_lookup_input(self) -> VehicleResearchRequest:
        identifier = self.identifier or self.vin
        if self.identifier and self.vin and self.identifier != self.vin:
            raise ValueError("identifier and legacy vin fields conflict")
        if identifier:
            result = VehicleIdentifierValidator().validate(
                identifier,
                market=self.market,
                identifier_type=self.identifier_type,
            )
            self.identifier = result.value
            self.vin = result.value if self.identifier_type == VehicleIdentifierType.VIN else None

        identity_fields = (self.make, self.model, self.year)
        if any(item is not None for item in identity_fields) and not all(
            item is not None for item in identity_fields
        ):
            raise ValueError("make, model, and year must be supplied together")
        if not identifier and not all(item is not None for item in identity_fields):
            raise ValueError("provide an identifier or make, model, and year")
        return self


class ResearchJobCreate(APIModel):
    vehicle: VehicleResearchRequest
    language: SupportedLanguage = "ru"


class ProviderResult(APIModel):
    provider_id: str
    capability: str
    status: EvidenceStatus
    records: list[dict] = Field(default_factory=list)
    raw_payload: dict | list = Field(default_factory=dict)
    source_url: str
    retrieved_at: datetime
    error: str | None = None
    from_cache: bool = False
    api_requests: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=0, ge=0)
    http_status: int | None = Field(default=None, ge=100, le=599)
    data_origin: DataOrigin = DataOrigin.REAL


class ProviderDefinitionDTO(APIModel):
    id: str
    markets: list[str]
    capabilities: list[str]
    cost_model: str
    precheck_cost: str
    full_lookup_cost: str
    requires_api_key: bool
    active: bool
    priority: int
    data_classes: list[str]


class ResearchStepDTO(APIModel):
    provider_id: str
    capability: str
    status: Literal["COMPLETE", "FAILED", "CACHE_HIT", "SKIPPED"]
    records_count: int = Field(default=0, ge=0)
    source_url: str | None = None
    started_at: datetime
    completed_at: datetime
    duration_ms: int = Field(default=0, ge=0)
    from_cache: bool = False
    error: str | None = None
    http_status: int | None = None


class VariantCandidateDTO(APIModel):
    id: str
    label: str
    generation: str | None = None
    production_year_start: int | None = None
    production_year_end: int | None = None
    market: str
    trim: str | None = None
    powertrain_type: str = "UNKNOWN"
    fuel: str | None = None
    engine: str | None = None
    engine_code: str | None = None
    transmission: str | None = None
    drivetrain: str | None = None
    body: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: str


class VariantSelectionRequest(APIModel):
    candidate_id: str = Field(min_length=1, max_length=240)


class VehicleResolutionDTO(APIModel):
    powertrain_type: str = "UNKNOWN"
    fuel: str | None = None
    identity_state: str = "IDENTITY_INCOMPLETE"
    identity_conflicts: list[dict] = Field(default_factory=list)
    make: str | None
    model: str | None
    year: int | None
    market: str
    generation: str | None = None
    engine_candidates: list[str] = Field(default_factory=list)
    engine_code_candidates: list[str] = Field(default_factory=list)
    transmission_candidates: list[str] = Field(default_factory=list)
    drivetrain_candidates: list[str] = Field(default_factory=list)
    ambiguity: bool = False
    needs_user_selection: bool = False
    unresolved_fields: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    status: VariantResolutionStatus = VariantResolutionStatus.INSUFFICIENT_DATA
    candidates: list[VariantCandidateDTO] = Field(default_factory=list)
    selected_candidate_id: str | None = None


class ResearchJobDTO(APIModel):
    id: str
    status: ResearchJobStatus
    requested_vehicle: VehicleResearchRequest
    provider_steps: list[ResearchStepDTO] = Field(default_factory=list)
    completed_capabilities: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cache_hit: bool = False
    profile_id: str | None = None
    profile: VehicleKnowledgeProfileDTO | None = None
    dossier: VehicleDossier | None = None
    resolution: VehicleResolutionDTO | None = None
    metrics: dict = Field(default_factory=dict)
    is_demo: bool = False


class DeveloperDossierAccessDTO(APIModel):
    """Owner-scoped, paywall-free dossier handle for local DeveloperMode."""

    job_id: str
    check_id: str
    profile_id: str
    developer_mode: bool = True
    simulate_user_paywall: bool = False

from __future__ import annotations

from pydantic import Field

from app.models.enums import ConfidenceLevel, EvidenceStatus, FitRating
from app.schemas.common import APIModel


class UsageProfileInput(APIModel):
    monthly_mileage_km: int = Field(ge=0, le=100_000)
    city_share: float = Field(ge=0, le=1)
    poor_roads: bool = False
    regular_region_trips: bool = False
    mountains: bool = False
    unpaved_roads: bool = False
    passengers: int = Field(default=1, ge=1, le=20)
    cargo_need: str = Field(default="normal", pattern=r"^(low|normal|high)$")
    economy_priority: int = Field(default=3, ge=1, le=5)
    reliability_priority: int = Field(default=3, ge=1, le=5)
    comfort_priority: int = Field(default=3, ge=1, le=5)
    performance_priority: int = Field(default=3, ge=1, le=5)
    maintenance_cost_priority: int = Field(default=3, ge=1, le=5)
    resale_priority: int = Field(default=3, ge=1, le=5)


class GroundedMetric(APIModel):
    value: float = Field(ge=0, le=100)
    status: EvidenceStatus
    evidence_ids: list[str] = Field(default_factory=list)


class VehicleFitFacts(APIModel):
    ground_clearance_mm: int | None = Field(default=None, ge=50, le=600)
    ground_clearance_status: EvidenceStatus = EvidenceStatus.INSUFFICIENT_DATA
    drivetrain: str | None = None
    drivetrain_status: EvidenceStatus = EvidenceStatus.INSUFFICIENT_DATA
    economy: GroundedMetric | None = None
    reliability: GroundedMetric | None = None
    comfort: GroundedMetric | None = None
    performance: GroundedMetric | None = None
    maintenance_affordability: GroundedMetric | None = None
    resale_liquidity: GroundedMetric | None = None
    passenger_space: GroundedMetric | None = None
    cargo_space: GroundedMetric | None = None


class FitReason(APIModel):
    code: str
    impact: int
    evidence_status: EvidenceStatus
    parameters: dict = Field(default_factory=dict)


class FitAnalysis(APIModel):
    rating: FitRating
    score: int = Field(ge=0, le=100)
    confidence: ConfidenceLevel
    reasons: list[FitReason]
    missing_facts: list[str]

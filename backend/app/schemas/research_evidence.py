"""VIN-specific events and owner materials, independent of model specifications."""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field, HttpUrl, model_validator

from app.schemas.common import APIModel, SourceSnapshot
from app.schemas.paid_report import VehiclePhotoSet


class ResearchState(StrEnum):
    NO_RECORDS = "NO_RECORDS"
    PARTIAL = "PARTIAL"
    AVAILABLE = "AVAILABLE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    ERROR = "ERROR"


class EvidenceProviderMetadata(APIModel):
    id: str
    name: str
    cost_type: Literal["FREE_PUBLIC", "PAYG", "SUBSCRIPTION"] = "FREE_PUBLIC"
    estimated_cost: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = "USD"
    capabilities: list[str]
    market: list[str] = Field(default_factory=lambda: ["USA"])
    priority: int = 100
    requires_auth: bool = False
    commercial_usage_status: Literal[
        "ALLOWED", "FACTUAL_SUMMARY_ONLY", "REVIEW_REQUIRED", "RESTRICTED"
    ] = "REVIEW_REQUIRED"
    policy_url: HttpUrl


class ProviderAttempt(APIModel):
    provider: EvidenceProviderMetadata
    state: ResearchState
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    query: dict
    scope: str
    reason: str | None = None
    http_status: int | None = None
    provenance: dict = Field(min_length=1)
    # A successful empty query must be explicit; a 404, blocked request, missing
    # adapter or an empty search index must never silently become NO_RECORDS.
    query_completed: bool = False

    @model_validator(mode="after")
    def completed_query(self):
        if (
            self.state in {ResearchState.NO_RECORDS, ResearchState.AVAILABLE}
            and not self.query_completed
        ):
            raise ValueError("Available/empty results require a completed source query")
        return self


class VinEvent(APIModel):
    id: str
    vin: str = Field(pattern=r"^[A-HJ-NPR-Z0-9]{17}$")
    event_type: Literal["AUCTION", "SALE", "TITLE", "ODOMETER", "DAMAGE", "OTHER"]
    event_date: date | None = None
    auction: str | None = None
    lot_id: str | None = None
    location: str | None = None
    odometer: Decimal | None = Field(default=None, ge=0)
    odometer_unit: Literal["mi", "km"] | None = None
    odometer_status: str | None = None
    title: str | None = None
    primary_damage: str | None = None
    secondary_damage: str | None = None
    loss_type: str | None = None
    sale_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None
    seller_type: str | None = None
    source_ids: list[str] = Field(min_length=1)
    provenance: list[dict] = Field(min_length=1)
    conflicts: dict[str, list] = Field(default_factory=dict)

    @model_validator(mode="after")
    def units(self):
        if self.odometer is not None and self.odometer_unit is None:
            raise ValueError("Odometer requires the source unit")
        if self.sale_price is not None and not self.currency:
            raise ValueError("Sale price requires the source currency")
        return self


class VinHistoryResult(APIModel):
    vin: str = Field(pattern=r"^[A-HJ-NPR-Z0-9]{17}$")
    attempt: ProviderAttempt
    events: list[VinEvent] = Field(default_factory=list)
    sources: list[SourceSnapshot] = Field(default_factory=list)
    photo_sets: list[VehiclePhotoSet] = Field(default_factory=list)

    @model_validator(mode="after")
    def exact_vin_provenance(self):
        source_ids = {s.id for s in self.sources if not s.is_demo and s.data_origin == "REAL"}
        event_ids = {e.id for e in self.events}
        source_urls = {s.id: s.url for s in self.sources}
        if any(e.vin != self.vin or not set(e.source_ids) <= source_ids for e in self.events):
            raise ValueError("Every event needs exact VIN and real source provenance")
        for group in self.photo_sets:
            if group.vin != self.vin or group.source_id not in source_ids:
                raise ValueError("Photo source and exact VIN are required")
            if not group.event_id or group.event_id not in event_ids:
                raise ValueError("A real photo set must belong to a supplied VIN event")
            if any(p.event_id != group.event_id for p in group.photos):
                raise ValueError("Photo and event must match")
            if any(
                str(p.source_url).rstrip("/") != source_urls[p.source_id].rstrip("/")
                for p in group.photos
            ):
                raise ValueError("Photo page must match its supplied source record")
            if any(
                group.source_id not in e.source_ids for e in self.events if e.id == group.event_id
            ):
                raise ValueError("Photo source must belong to its event")
        if self.attempt.state == ResearchState.NO_RECORDS and (self.events or self.photo_sets):
            raise ValueError("NO_RECORDS cannot contain events or photos")
        if self.attempt.state == ResearchState.AVAILABLE and not self.events:
            raise ValueError("AVAILABLE needs at least one event")
        if self.events and self.attempt.state not in {
            ResearchState.AVAILABLE,
            ResearchState.PARTIAL,
        }:
            raise ValueError("Failed providers cannot return publishable events")
        return self


OWNER_CLASSES = {"OWNER_REVIEW", "OWNER_LOG", "FORUM_POST", "REPAIR_EXPERIENCE", "COMMUNITY_REPORT"}
OWNER_TOPICS = {
    "ENGINE",
    "TRANSMISSION",
    "COOLING",
    "ELECTRICAL",
    "SUSPENSION",
    "STEERING",
    "BRAKES",
    "BODY",
    "INTERIOR",
    "INFOTAINMENT",
    "FUEL_ECONOMY",
    "MAINTENANCE",
    "RELIABILITY_GENERAL",
}


class OwnerMaterial(APIModel):
    applicability_class: Literal[
        "EXACT_VIN", "EXACT_VARIANT", "GENERATION", "MODEL_YEAR", "MODEL_WIDE", "UNKNOWN"
    ] = "UNKNOWN"
    material_id: str
    evidence_class: Literal[
        "OWNER_REVIEW", "OWNER_LOG", "FORUM_POST", "REPAIR_EXPERIENCE", "COMMUNITY_REPORT"
    ]
    canonical_url: HttpUrl
    publisher_group: str
    owner_id: str | None = None
    observed_at: date | None = None
    retrieved_at: datetime
    applicability: dict
    mileage: int | None = Field(default=None, ge=0)
    mileage_unit: Literal["mi", "km"] | None = None
    topics: list[str]
    sentiment: Literal["POSITIVE", "NEGATIVE", "MIXED", "NEUTRAL"]
    issue_key: str | None = None
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    text_fingerprint: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    provenance: dict = Field(min_length=1)
    repost_of: str | None = None

    @model_validator(mode="after")
    def topic_vocabulary(self):
        from app.services.vehicle_identity import applicability_class

        self.applicability_class = applicability_class(
            self.applicability, exact=bool(self.applicability.get("vin"))
        )
        if not self.topics or not set(self.topics) <= OWNER_TOPICS:
            raise ValueError("Owner material requires supported topics")
        self.topics = sorted(set(self.topics))
        return self


class OwnerReviewResult(APIModel):
    attempt: ProviderAttempt
    sources: list[SourceSnapshot] = Field(default_factory=list)
    materials: list[OwnerMaterial] = Field(default_factory=list)
    excluded: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def material_sources(self):
        ids = {s.id for s in self.sources if not s.is_demo and s.data_origin == "REAL"}
        if any(not set(m.source_ids) <= ids for m in self.materials):
            raise ValueError("Owner materials require real source provenance")
        if self.attempt.state == ResearchState.NO_RECORDS and self.materials:
            raise ValueError("NO_RECORDS cannot contain owner materials")
        return self

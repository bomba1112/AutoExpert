from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, HttpUrl, model_validator

from app.schemas.common import APIModel, SupportedLanguage


class PhotoEvidence(APIModel):
    id: str
    vin: str = Field(min_length=17, max_length=17)
    source_id: str
    source_url: HttpUrl
    asset_url: HttpUrl
    event_id: str | None = None
    captured_at: datetime | None = None
    retrieved_at: datetime
    provenance: dict = Field(min_length=1)
    caption: str
    asset_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    order: int = Field(default=0, ge=0)
    original_reference: str | None = None
    cache_permission: str | None = None


class VehiclePhotoSet(APIModel):
    vin: str
    source_id: str
    event_id: str | None = None
    photos: list[PhotoEvidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def exact_vehicle_and_source(self):
        if any(p.vin != self.vin or p.source_id != self.source_id for p in self.photos):
            raise ValueError("Photo VIN and source must match the photo set")
        if self.event_id and any(p.event_id != self.event_id for p in self.photos):
            raise ValueError("Photo event must match the photo set")
        return self


class ReportRow(APIModel):
    key: str
    label: str
    value: str
    evidence_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class ReportParagraph(APIModel):
    text: str
    evidence_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class ReportEvent(APIModel):
    id: str
    title: str
    rows: list[ReportRow] = Field(default_factory=list)
    source_ids: list[str]


class PaidReportSection(APIModel):
    key: str
    title: str
    rows: list[ReportRow] = Field(default_factory=list)
    paragraphs: list[ReportParagraph] = Field(default_factory=list)
    collapsed: bool = False
    events: list[ReportEvent] = Field(default_factory=list)


class PaidReportReadiness(APIModel):
    identity_state: Literal["RESOLVED", "IDENTITY_INCOMPLETE", "VARIANT_CONFLICT"] = (
        "IDENTITY_INCOMPLETE"
    )
    state: Literal["READY", "NOT_ENOUGH_DATA_FOR_PAID_REPORT"]
    can_purchase: bool
    missing_requirements: list[str] = Field(default_factory=list)
    checks: dict[str, bool]


class PaidVehicleReport(APIModel):
    version: str = "1.0"
    language: SupportedLanguage
    vin: str
    title: str
    subtitle: str
    generated_at: datetime
    readiness: PaidReportReadiness
    notice: str | None = None
    sections: list[PaidReportSection]
    photo_sets: list[VehiclePhotoSet] = Field(default_factory=list)
    source_ids: list[str]

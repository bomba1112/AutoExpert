from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.models.enums import DataOrigin, EvidenceStatus
from app.schemas.common import APIModel


class NHTSARecallRecord(APIModel):
    campaign_number: str
    manufacturer: str
    report_received_date: str | None = None
    component: str
    summary: str
    consequence: str | None = None
    remedy: str | None = None
    notes: str | None = None
    make: str
    model: str
    model_year: int
    evidence_status: EvidenceStatus = EvidenceStatus.CONFIRMED
    data_origin: DataOrigin = DataOrigin.REAL


class NHTSAComplaintRecord(APIModel):
    odi_number: str
    incident_date: str | None = None
    components: str
    normalized_summary: str
    crash: bool = False
    fire: bool = False
    injuries: int = Field(default=0, ge=0)
    deaths: int = Field(default=0, ge=0)
    evidence_status: EvidenceStatus = EvidenceStatus.ESTIMATE
    data_origin: DataOrigin = DataOrigin.REAL


class NHTSAVINDecodeRecord(APIModel):
    vin: str
    make: str | None = None
    model: str | None = None
    model_year: int | None = None
    engine_model: str | None = None
    displacement_l: str | None = None
    transmission_speeds: str | None = None
    error_code: str | None = None
    error_text: str | None = None
    evidence_status: EvidenceStatus = EvidenceStatus.CONFIRMED
    data_origin: DataOrigin = DataOrigin.REAL


class NHTSAFetchResult(APIModel):
    status: EvidenceStatus
    records: list[dict] = Field(default_factory=list)
    retrieved_at: datetime
    from_cache: bool = False
    error: str | None = None
    source_url: str

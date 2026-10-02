from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import DataOrigin, EvidenceStatus, SourceUsageStatus
from app.models.vehicle_knowledge import VehicleKnowledgeProfile
from app.schemas.vin import VehicleDossier


class RealDataQualityError(ValueError):
    pass


@dataclass(frozen=True)
class RealProfileQualityReport:
    sources: int
    confirmed_evidence: int
    recalls: int
    manufacturer_communications: int
    dossier_sections_with_real_data: int
    dossier_sections_total: int


def validate_real_profile(
    profile: VehicleKnowledgeProfile,
    *,
    dossier: VehicleDossier | None = None,
) -> RealProfileQualityReport:
    if profile.data_origin != DataOrigin.REAL or profile.is_demo:
        raise RealDataQualityError("Real profile must be marked data_origin=REAL")
    if not profile.sources:
        raise RealDataQualityError("Real profile has no sources")
    source_ids = set()
    for source in profile.sources:
        if source.data_origin != DataOrigin.REAL or source.is_demo:
            raise RealDataQualityError("Real profile contains a DEMO source")
        if source.usage_status != SourceUsageStatus.ACTIVE:
            raise RealDataQualityError("Real profile contains an inactive source")
        source_ids.add(source.id)

    confirmed = 0
    recalls = 0
    communication_source_ids = set()
    for item in profile.evidence:
        if item.data_origin != DataOrigin.REAL or item.is_demo:
            raise RealDataQualityError("Real profile contains DEMO evidence")
        if item.source_id not in source_ids:
            raise RealDataQualityError("Evidence source is not linked to the profile")
        if item.status == EvidenceStatus.CONFIRMED:
            confirmed += 1
            if not item.source_id:
                raise RealDataQualityError("CONFIRMED evidence requires a source")
        if item.conditions.get("campaign_number"):
            recalls += 1
        if item.source.source_type == "MANUFACTURER_COMMUNICATION":
            communication_source_ids.add(item.source_id)

    populated = 0
    total = 0
    if dossier is not None:
        total = len(dossier.sections)
        for section in dossier.sections:
            has_grounded_claim = any(
                claim.status != EvidenceStatus.INSUFFICIENT_DATA for claim in section.claims
            )
            if has_grounded_claim or section.known_issues or section.key == "sources":
                populated += 1
    return RealProfileQualityReport(
        sources=len(source_ids),
        confirmed_evidence=confirmed,
        recalls=recalls,
        manufacturer_communications=len(communication_source_ids),
        dossier_sections_with_real_data=populated,
        dossier_sections_total=total,
    )

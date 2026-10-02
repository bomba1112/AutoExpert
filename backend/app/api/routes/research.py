from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DBSession
from app.models.enums import DataOrigin, OdometerRisk, ResearchJobStatus, VehicleIdentifierType
from app.models.research import ResearchJob
from app.models.vehicle_knowledge import VINCheck
from app.schemas.common import SourceSnapshot
from app.schemas.research import (
    DeveloperDossierAccessDTO,
    ProviderDefinitionDTO,
    ResearchJobCreate,
    ResearchJobDTO,
    VariantSelectionRequest,
)
from app.schemas.vin import VehicleDossier, VINHistoryPayload
from app.services.developer_access import DeveloperAccess
from app.services.dossier import profile_dto
from app.services.provider_registry import ProviderRegistry, default_provider_registry
from app.services.report_evidence import ensure_report_evidence
from app.services.research_pipeline import ResearchPipeline
from app.services.research_rights import (
    job_uses_restricted_epa,
    permitted_research_registry,
)

router = APIRouter(prefix="/research", tags=["vehicle-research"])


def get_provider_registry(db: DBSession) -> ProviderRegistry:
    return permitted_research_registry(db, default_provider_registry())


Registry = Annotated[ProviderRegistry, Depends(get_provider_registry)]


@router.get("/providers", response_model=list[ProviderDefinitionDTO])
def list_research_providers(
    registry: Registry,
    user: CurrentUser,
) -> list[ProviderDefinitionDTO]:
    del user
    return [item.definition.public_dto() for item in registry.providers]


@router.post("/jobs", response_model=ResearchJobDTO, status_code=status.HTTP_201_CREATED)
def create_research_job(
    value: ResearchJobCreate,
    db: DBSession,
    user: CurrentUser,
    registry: Registry,
) -> ResearchJobDTO:
    job = ResearchPipeline(db, registry).create_job(user_id=user.id, value=value)
    return _job_dto(job, db)


@router.get("/jobs/{job_id}", response_model=ResearchJobDTO)
def get_research_job(
    job_id: str,
    db: DBSession,
    user: CurrentUser,
) -> ResearchJobDTO:
    return _job_dto(_owned_job(db, user.id, job_id), db)


@router.post("/jobs/{job_id}/execute", response_model=ResearchJobDTO)
def execute_research_job(
    job_id: str,
    db: DBSession,
    user: CurrentUser,
    registry: Registry,
) -> ResearchJobDTO:
    job = _owned_job(db, user.id, job_id)
    if job.worker_queue:
        raise HTTPException(409, "QUEUED_JOB_REQUIRES_BOUNDED_WORKER")
    return _job_dto(ResearchPipeline(db, registry).execute(job), db)


@router.post("/jobs/{job_id}/variant-selection", response_model=ResearchJobDTO)
def select_research_variant(
    job_id: str,
    value: VariantSelectionRequest,
    db: DBSession,
    user: CurrentUser,
    registry: Registry,
) -> ResearchJobDTO:
    job = _owned_job(db, user.id, job_id)
    if job.worker_queue:
        raise HTTPException(409, "QUEUED_JOB_REQUIRES_EDITORIAL_REVIEW")
    try:
        selected = ResearchPipeline(db, registry).select_variant(job, value.candidate_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return _job_dto(selected, db)


@router.post(
    "/jobs/{job_id}/developer-dossier",
    response_model=DeveloperDossierAccessDTO,
    status_code=status.HTTP_200_OK,
)
def open_developer_dossier(
    job_id: str,
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
) -> DeveloperDossierAccessDTO:
    """Create an idempotent report context without VIN demo data or entitlements.

    This endpoint is intentionally available only to an authenticated resource owner
    while server-side DeveloperMode bypass is active.  It bridges an automatically
    researched profile into the existing dossier/chat UI and runs the independent
    history/owner evidence layers. It never creates payment or entitlement records.
    """

    if not access.bypass_paywall:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Developer dossier access requires DeveloperMode without paywall simulation",
        )
    job = _owned_job(db, user.id, job_id)
    if job.profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle profile not found for this research job",
        )
    if (
        job.status not in {ResearchJobStatus.COMPLETE, ResearchJobStatus.PARTIAL}
        or not job.dossier_snapshot
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Research job does not contain a completed vehicle dossier",
        )

    metrics = dict(job.metrics or {})
    existing_id = metrics.get("developer_dossier_check_id")
    existing = db.get(VINCheck, existing_id) if existing_id else None
    if existing is not None and existing.user_id == user.id:
        ensure_report_evidence(existing)
        db.commit()
        return DeveloperDossierAccessDTO(
            job_id=job.id,
            check_id=existing.id,
            profile_id=job.profile.id,
        )

    requested = job.requested_vehicle or {}
    identifier_type = requested.get("identifier_type", VehicleIdentifierType.VIN.value)
    identifier = requested.get("identifier") or requested.get("vin") or ""
    vin = identifier if identifier_type == VehicleIdentifierType.VIN.value else ""
    sources = [_source_snapshot(item).model_dump(mode="json") for item in job.profile.sources]
    empty_history = VINHistoryPayload(
        vin=vin,
        timeline=[],
        auctions=[],
        photos=[],
        damage_details=[],
        odometer_records=[],
        is_demo=False,
        data_origin=DataOrigin.REAL,
    )
    check = VINCheck(
        user_id=user.id,
        vehicle_profile_id=job.profile.id,
        normalized_vin=vin,
        language=job.language,
        found=False,
        records_count=0,
        photos_count=0,
        auctions_count=0,
        has_salvage_title=False,
        odometer_risk=OdometerRisk.UNKNOWN,
        full_history_payload=empty_history.model_dump(mode="json"),
        dossier_snapshot=job.dossier_snapshot,
        source_snapshot=sources,
        is_demo=job.profile.is_demo,
        data_origin=DataOrigin.REAL,
    )
    db.add(check)
    db.flush()
    ensure_report_evidence(check)
    metrics["developer_dossier_check_id"] = check.id
    job.metrics = metrics
    db.commit()
    return DeveloperDossierAccessDTO(
        job_id=job.id,
        check_id=check.id,
        profile_id=job.profile.id,
    )


def _owned_job(db: DBSession, user_id: str, job_id: str) -> ResearchJob:
    job = db.scalar(
        select(ResearchJob).where(ResearchJob.id == job_id, ResearchJob.user_id == user_id)
    )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research job not found",
        )
    if job_uses_restricted_epa(db, job):
        raise HTTPException(409, "EPA_COMMERCIAL_RIGHTS_UNRESOLVED")
    return job


def _job_dto(job: ResearchJob, db: DBSession) -> ResearchJobDTO:
    if job_uses_restricted_epa(db, job):
        raise HTTPException(409, "EPA_COMMERCIAL_RIGHTS_UNRESOLVED")
    return ResearchJobDTO(
        id=job.id,
        status=job.status,
        requested_vehicle=job.requested_vehicle,
        provider_steps=job.provider_steps,
        completed_capabilities=job.completed_capabilities,
        errors=job.errors,
        started_at=job.started_at,
        completed_at=job.completed_at,
        cache_hit=job.cache_hit,
        profile_id=job.vehicle_profile_id,
        profile=profile_dto(job.profile) if job.profile else None,
        dossier=(
            VehicleDossier.model_validate(job.dossier_snapshot) if job.dossier_snapshot else None
        ),
        resolution=job.resolution_snapshot or None,
        metrics=job.metrics,
        is_demo=job.is_demo,
    )


def _source_snapshot(source: object) -> SourceSnapshot:
    return SourceSnapshot(
        id=source.id,
        title=source.title,
        publisher=source.publisher,
        url=source.url,
        source_type=source.source_type,
        source_tier=source.source_tier,
        data_origin=source.data_origin,
        market=source.market,
        language=source.language,
        published_at=source.published_at.isoformat() if source.published_at else None,
        retrieved_at=source.retrieved_at.isoformat(),
        confidence=source.confidence,
        usage_status=source.usage_status,
        is_demo=source.is_demo,
    )

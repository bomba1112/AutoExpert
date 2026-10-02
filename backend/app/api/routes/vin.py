from __future__ import annotations

import base64
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DBSession
from app.core.config import get_settings
from app.db.seed_demo import seed_autoexpert2_demo, seed_autoexpert2_ford_demo
from app.models.enums import DataOrigin, EntitlementStatus, EntitlementType
from app.models.evidence import KnownIssue, SourceRecord
from app.models.vehicle_knowledge import (
    AutoExpertChatContext,
    VehicleKnowledgeProfile,
    VINCheck,
    VINEntitlement,
)
from app.pricing.vin import configured_vin_price
from app.providers.analytics import DatabaseAnalyticsProvider
from app.providers.database import DatabaseOwnerReviewProvider
from app.providers.payment import MockPaymentProvider
from app.providers.vin import (
    FORD_EXAMPLE_VIN,
    TOYOTA_DEMO_VIN,
    DeterministicDemoVINPrecheckProvider,
    VINPrecheckProvider,
)
from app.review_engine.engine import OwnerFeedbackEngine
from app.schemas.common import SourceSnapshot
from app.schemas.reviews import OwnerObservation
from app.schemas.vin import (
    RealPilotPrecheckCreate,
    VehicleDossier,
    VehicleKnowledgeProfileDTO,
    VINCheckSummary,
    VINFullReportResponse,
    VINHistoryPayload,
    VINPrecheckCreate,
    VINPrecheckTeaser,
    VINUnlockRequest,
    VINUnlockResponse,
)
from app.services.developer_access import DeveloperAccess, DeveloperAccessContext
from app.services.dossier import build_vehicle_dossier, profile_dto
from app.services.paid_report import build_paid_report, paid_readiness
from app.services.research_rights import profile_uses_restricted_epa, source_uses_restricted_epa
from app.services.vehicle_identity import source_scopes

router = APIRouter(prefix="/vin", tags=["vin"])


def get_vin_precheck_provider() -> VINPrecheckProvider:
    return DeterministicDemoVINPrecheckProvider()


VINProvider = Annotated[VINPrecheckProvider, Depends(get_vin_precheck_provider)]


def _qa_demo_enabled() -> bool:
    settings = get_settings()
    return settings.environment in {"development", "test"} and settings.demo_mode


@router.get("/profiles", response_model=list[VehicleKnowledgeProfileDTO])
def list_vehicle_profiles(db: DBSession, user: CurrentUser) -> list[VehicleKnowledgeProfileDTO]:
    del user
    qa_demo = _qa_demo_enabled()
    if qa_demo:
        seed_autoexpert2_demo(db)
        db.commit()
    profiles = list(
        db.scalars(
            select(VehicleKnowledgeProfile).order_by(
                VehicleKnowledgeProfile.make,
                VehicleKnowledgeProfile.model,
                VehicleKnowledgeProfile.year,
            )
        )
    )
    return [
        profile_dto(profile)
        for profile in profiles
        if qa_demo or profile.data_origin != DataOrigin.DEMO
        if not profile_uses_restricted_epa(db, profile)
    ]


@router.post(
    "/profiles/real-pilot",
    response_model=VehicleKnowledgeProfileDTO,
    status_code=status.HTTP_201_CREATED,
)
def prepare_real_camry_pilot(db: DBSession, user: CurrentUser) -> VehicleKnowledgeProfileDTO:
    del user
    if not get_settings().demo_mode or get_settings().environment == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pilot disabled")
    # Stage 3's reviewed manifest remains an explicit regression fixture only.
    # Keeping this import local prevents the manual seed from entering the
    # production application initialization or automatic research path.
    from app.db.seed_real_camry import seed_real_camry

    profile_id = seed_real_camry(db)
    return profile_dto(db.get(VehicleKnowledgeProfile, profile_id))


@router.post(
    "/profiles/{profile_id}/demo-precheck",
    response_model=VINPrecheckTeaser,
    status_code=status.HTTP_201_CREATED,
)
def create_real_profile_demo_precheck(
    profile_id: str,
    value: RealPilotPrecheckCreate,
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
) -> VINPrecheckTeaser:
    if not get_settings().demo_mode or get_settings().environment == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pilot disabled")
    profile = db.get(VehicleKnowledgeProfile, profile_id)
    if profile is None or profile.data_origin != DataOrigin.REAL:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Real pilot not found")
    provider = DeterministicDemoVINPrecheckProvider()
    vin = _fixture_vin_for_profile(profile, value.vin, provider)
    precheck = provider.precheck(vin)
    full_history = provider.full_history(vin)
    demo_source = _fixture_source(db, vin)
    _replace_fixture_source_ids(full_history, [demo_source.id])
    dossier_snapshot, source_snapshot = _profile_snapshots(db, profile, value.language)
    if demo_source.id not in {item["id"] for item in source_snapshot}:
        source_snapshot.append(_source_snapshot(demo_source).model_dump(mode="json"))
    check = VINCheck(
        user_id=user.id,
        vehicle_profile_id=profile.id,
        normalized_vin=vin,
        language=value.language,
        found=precheck.found,
        records_count=precheck.records_count,
        photos_count=precheck.photos_count,
        auctions_count=precheck.auctions_count,
        has_salvage_title=precheck.has_salvage_title,
        odometer_risk=precheck.odometer_risk,
        full_history_payload=full_history,
        dossier_snapshot=dossier_snapshot,
        source_snapshot=source_snapshot,
        is_demo=True,
        data_origin=DataOrigin.DEMO,
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    return _teaser(db, check, user.id, access)


@router.get("/checks", response_model=list[VINCheckSummary])
def list_vin_checks(
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
) -> list[VINCheckSummary]:
    checks = list(
        db.scalars(
            select(VINCheck).where(VINCheck.user_id == user.id).order_by(VINCheck.created_at.desc())
        )
    )
    return [
        VINCheckSummary(
            check_id=check.id,
            created_at=check.created_at,
            vin=check.normalized_vin,
            vehicle=(profile_dto(check.profile).model_dump(mode="json") if check.profile else None),
            records_count=check.records_count,
            photos_count=check.photos_count,
            is_unlocked=access.bypass_paywall or _has_entitlement(db, check, user.id),
            is_demo=check.is_demo,
        )
        for check in checks
        if _qa_demo_enabled() or not check.is_demo
        if not _check_uses_restricted_epa(db, check)
    ]


@router.post("/precheck", response_model=VINPrecheckTeaser, status_code=status.HTTP_201_CREATED)
def create_vin_precheck(
    value: VINPrecheckCreate,
    db: DBSession,
    user: CurrentUser,
    provider: VINProvider,
    access: DeveloperAccess,
) -> VINPrecheckTeaser:
    if not _qa_demo_enabled() and isinstance(
        provider, DeterministicDemoVINPrecheckProvider
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIN fixture unavailable")
    analytics = DatabaseAnalyticsProvider(db)
    analytics.track(
        "analysis_started",
        user_id=user.id,
        anonymous_id=None,
        properties={"flow": "vin_precheck", "provider": provider.name},
    )
    resolved = provider.resolve_vehicle(value.vin)
    precheck = provider.precheck(value.vin)
    if not _qa_demo_enabled() and precheck.is_demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIN fixture unavailable")
    profile = _resolve_profile(db, resolved)
    source_ids = [item.id for item in profile.sources] if profile else []
    full_history = provider.full_history(value.vin)
    _replace_fixture_source_ids(full_history, source_ids)

    dossier_snapshot: dict = {}
    source_snapshot: list[dict] = []
    if profile is not None:
        dossier_snapshot, source_snapshot = _profile_snapshots(db, profile, value.language)

    check = VINCheck(
        user_id=user.id,
        vehicle_profile_id=profile.id if profile else None,
        normalized_vin=value.vin,
        language=value.language,
        found=precheck.found,
        records_count=precheck.records_count,
        photos_count=precheck.photos_count,
        auctions_count=precheck.auctions_count,
        has_salvage_title=precheck.has_salvage_title,
        odometer_risk=precheck.odometer_risk,
        full_history_payload=full_history,
        dossier_snapshot=dossier_snapshot,
        source_snapshot=source_snapshot,
        is_demo=precheck.is_demo,
        data_origin=DataOrigin.DEMO if precheck.is_demo else DataOrigin.REAL,
    )
    db.add(check)
    analytics.track(
        "preview_generated",
        user_id=user.id,
        anonymous_id=None,
        properties={
            "flow": "vin_precheck",
            "records_count": precheck.records_count,
            "is_demo": precheck.is_demo,
        },
    )
    db.commit()
    db.refresh(check)
    return _teaser(db, check, user.id, access)


@router.get("/{check_id}/precheck", response_model=VINPrecheckTeaser)
def get_vin_precheck(
    check_id: str,
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
) -> VINPrecheckTeaser:
    return _teaser(db, _owned_check(db, user.id, check_id), user.id, access)


@router.post("/{check_id}/payments/mock", response_model=VINUnlockResponse)
def mock_unlock_vin_report(
    check_id: str,
    value: VINUnlockRequest,
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
) -> VINUnlockResponse:
    settings = get_settings()
    if access.bypass_paywall:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "DeveloperMode already provides access; enable Simulate User Paywall "
                "to test payment"
            ),
        )
    if not _qa_demo_enabled() or settings.payment_provider != "mock":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mock payment disabled")
    check = _owned_check(db, user.id, check_id, for_update=True)
    if not check.is_demo and (
        check.profile is None
        or not paid_readiness(check.profile, check.full_history_payload).can_purchase
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="NOT_ENOUGH_DATA_FOR_PAID_REPORT"
        )
    if check.is_demo and check.records_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A paid VIN report is not offered when no connected records are found",
        )
    amount, currency = configured_vin_price("AZ")
    if amount is None or currency is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="VIN price is not configured for this market",
        )
    existing = _active_entitlement(db, check, user.id)
    if existing is not None:
        return VINUnlockResponse(
            check_id=check.id,
            entitlement_id=existing.id,
            entitlement_type=existing.entitlement_type.value,
            provider=existing.provider,
            status="ALREADY_UNLOCKED",
            is_unlocked=True,
            amount=existing.amount,
            currency=existing.currency,
            is_demo=check.is_demo,
        )

    analytics = DatabaseAnalyticsProvider(db)
    analytics.track(
        "payment_started",
        user_id=user.id,
        anonymous_id=None,
        properties={"vin_check_id": check.id, "product": "VIN_CHECK_1"},
    )
    payment_provider = MockPaymentProvider(should_succeed=not value.simulate_failure)
    result = payment_provider.charge(
        report_id=check.id,
        user_id=user.id,
        amount=amount,
        currency=currency,
    )
    if not result.succeeded:
        db.commit()
        return VINUnlockResponse(
            check_id=check.id,
            entitlement_type=EntitlementType.VIN_REPORT_UNLOCKED.value,
            provider=payment_provider.name,
            status="FAILED",
            is_unlocked=False,
            amount=amount,
            currency=currency,
            is_demo=check.is_demo,
        )

    entitlement = VINEntitlement(
        user_id=user.id,
        vin_check_id=check.id,
        entitlement_type=EntitlementType.VIN_REPORT_UNLOCKED,
        status=EntitlementStatus.ACTIVE,
        provider=payment_provider.name,
        external_payment_id=result.external_id,
        amount=amount,
        currency=currency,
        provider_payload=result.provider_payload,
    )
    db.add(entitlement)
    db.flush()
    _ensure_legacy_chat_context(db, check, user.id)
    analytics.track(
        "payment_success",
        user_id=user.id,
        anonymous_id=None,
        properties={"vin_check_id": check.id, "product": "VIN_CHECK_1"},
    )
    db.commit()
    db.refresh(entitlement)
    return VINUnlockResponse(
        check_id=check.id,
        entitlement_id=entitlement.id,
        entitlement_type=entitlement.entitlement_type.value,
        provider=payment_provider.name,
        status="SUCCEEDED",
        is_unlocked=True,
        amount=amount,
        currency=currency,
        is_demo=check.is_demo,
    )


@router.get("/{check_id}", response_model=VINFullReportResponse)
def get_full_vin_report(
    check_id: str,
    db: DBSession,
    user: CurrentUser,
    access: DeveloperAccess,
) -> VINFullReportResponse:
    check = _owned_check(db, user.id, check_id)
    entitlement = _active_entitlement(db, check, user.id)
    if entitlement is None and not access.bypass_paywall:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="VIN report is locked",
        )
    if check.profile is None or not check.dossier_snapshot:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle profile is not available for this VIN report",
        )
    chat_context = _ensure_legacy_chat_context(db, check, user.id)
    DatabaseAnalyticsProvider(db).track(
        "report_opened",
        user_id=user.id,
        anonymous_id=None,
        properties={"vin_check_id": check.id, "flow": "vin"},
    )
    db.commit()
    return VINFullReportResponse(
        check_id=check.id,
        vin=check.normalized_vin,
        vehicle=profile_dto(check.profile),
        history=VINHistoryPayload.model_validate(check.full_history_payload),
        dossier=VehicleDossier.model_validate(check.dossier_snapshot),
        sources=[
            SourceSnapshot.model_validate(item)
            for item in source_scopes(check.profile, check.source_snapshot, check.language)
        ],
        chat_context_id=chat_context.id,
        entitlement_type=(
            entitlement.entitlement_type.value if entitlement else "DEVELOPER_BYPASS"
        ),
        is_demo=check.is_demo,
        vin_history_origin=check.data_origin,
        dossier_origin=check.profile.data_origin,
        developer_mode=access.enabled,
        simulate_user_paywall=access.simulate_user_paywall,
        paid_report=build_paid_report(check).model_dump(mode="json") if not check.is_demo else None,
    )


def _resolve_profile(db: DBSession, resolved: object | None) -> VehicleKnowledgeProfile | None:
    if resolved is None:
        return None
    profile = db.scalar(
        select(VehicleKnowledgeProfile).where(
            VehicleKnowledgeProfile.make == resolved.make,
            VehicleKnowledgeProfile.model == resolved.model,
            VehicleKnowledgeProfile.generation == resolved.generation,
            VehicleKnowledgeProfile.market == resolved.market,
            VehicleKnowledgeProfile.year == resolved.year,
            VehicleKnowledgeProfile.engine_code == resolved.engine_code,
            VehicleKnowledgeProfile.transmission == resolved.transmission,
            VehicleKnowledgeProfile.data_origin
            == (DataOrigin.DEMO if resolved.is_demo else DataOrigin.REAL),
        )
    )
    if (
        profile is None
        and _qa_demo_enabled()
        and resolved.is_demo
    ):
        if resolved.make == "Ford" and resolved.model == "Fusion":
            seed_autoexpert2_ford_demo(db)
        elif resolved.make == "Toyota" and resolved.model == "Camry":
            seed_autoexpert2_demo(db)
        db.flush()
        profile = db.scalar(
            select(VehicleKnowledgeProfile).where(
                VehicleKnowledgeProfile.make == resolved.make,
                VehicleKnowledgeProfile.model == resolved.model,
                VehicleKnowledgeProfile.generation == resolved.generation,
                VehicleKnowledgeProfile.market == resolved.market,
                VehicleKnowledgeProfile.year == resolved.year,
                VehicleKnowledgeProfile.engine_code == resolved.engine_code,
                VehicleKnowledgeProfile.transmission == resolved.transmission,
                VehicleKnowledgeProfile.data_origin == DataOrigin.DEMO,
            )
        )
    return None if profile_uses_restricted_epa(db, profile) else profile


@router.get("/{check_id}/report.pdf")
def export_paid_report_pdf(
    check_id: str, db: DBSession, user: CurrentUser, access: DeveloperAccess
):
    check = _owned_check(db, user.id, check_id)
    if not access.bypass_paywall and not _has_entitlement(db, check, user.id):
        raise HTTPException(status_code=402, detail="VIN report is locked")
    if check.profile is None or check.is_demo:
        raise HTTPException(status_code=409, detail="Real vehicle report required")
    from app.services.report_pdf import render_report_pdf

    report = build_paid_report(check)
    from app.services.vin_history_assets import photo_bytes

    try:
        assets = {p.id: photo_bytes(p) for group in report.photo_sets for p in group.photos}
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=409, detail="Report photograph unavailable") from error
    pdf = render_report_pdf(report, sources=check.source_snapshot, photo_assets=assets)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="AutoExpert_{check.normalized_vin}.pdf"',
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/{check_id}/photos/{photo_id}")
def get_vehicle_photo(
    check_id: str, photo_id: str, db: DBSession, user: CurrentUser, access: DeveloperAccess
):
    check = _owned_check(db, user.id, check_id)
    if not access.bypass_paywall and not _has_entitlement(db, check, user.id):
        raise HTTPException(status_code=402, detail="VIN report is locked")
    report = build_paid_report(check)
    photo = next((p for g in report.photo_sets for p in g.photos if p.id == photo_id), None)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photograph not found")
    from app.services.vin_history_assets import photo_bytes

    try:
        content = photo_bytes(photo)
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=409, detail="Photograph unavailable") from error
    mime = (
        "image/png"
        if content.startswith(b"\x89PNG")
        else ("image/webp" if content.startswith(b"RIFF") else "image/jpeg")
    )
    return Response(content, media_type=mime, headers={"Cache-Control": "private, no-store"})


@router.get("/{check_id}/diagnostics")
def paid_report_diagnostics(
    check_id: str, db: DBSession, user: CurrentUser, access: DeveloperAccess
):
    check = _owned_check(db, user.id, check_id)
    if not access.diagnostics_visible:
        raise HTTPException(status_code=404, detail="Developer diagnostics disabled")
    if check.profile is None:
        raise HTTPException(status_code=409, detail="Vehicle profile unavailable")
    return {
        "quality_gate": paid_readiness(check.profile, check.full_history_payload).model_dump(
            mode="json"
        ),
        "vin_history": check.full_history_payload.get("history_research", {}),
        "vin_events": check.full_history_payload.get("events", []),
        "photo_sets": check.full_history_payload.get("photo_sets", []),
        "owner_reliability": check.full_history_payload.get("owner_reliability", {}),
        "knowledge": check.profile.dossier_seed.get("knowledge_depth", {}),
        "identity_integrity": check.profile.dossier_seed.get("identity_integrity", {}),
        "wrong_variant_records_rejected": check.profile.dossier_seed.get("variant_rejections", []),
        "evidence": [
            {
                "id": e.id,
                "source_id": e.source_id,
                "status": e.status,
                "conditions": e.conditions,
                "statement": e.statement,
            }
            for e in check.profile.evidence
        ],
        "sources": check.source_snapshot,
    }


def _owned_check(
    db: DBSession,
    user_id: str,
    check_id: str,
    *,
    for_update: bool = False,
) -> VINCheck:
    query = select(VINCheck).where(VINCheck.id == check_id, VINCheck.user_id == user_id)
    if for_update:
        query = query.with_for_update()
    check = db.scalar(query)
    if check is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIN check not found")
    if not _qa_demo_enabled() and check.is_demo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIN check not found")
    if _check_uses_restricted_epa(db, check):
        raise HTTPException(status_code=409, detail="EPA_COMMERCIAL_RIGHTS_UNRESOLVED")
    return check


def _check_uses_restricted_epa(db: DBSession, check: VINCheck) -> bool:
    return profile_uses_restricted_epa(db, check.profile) or any(
        source_uses_restricted_epa(db, source) for source in (check.source_snapshot or [])
    )


def _active_entitlement(
    db: DBSession,
    check: VINCheck,
    user_id: str,
) -> VINEntitlement | None:
    return db.scalar(
        select(VINEntitlement).where(
            VINEntitlement.vin_check_id == check.id,
            VINEntitlement.user_id == user_id,
            VINEntitlement.entitlement_type == EntitlementType.VIN_REPORT_UNLOCKED,
            VINEntitlement.status == EntitlementStatus.ACTIVE,
        )
    )


def _has_entitlement(db: DBSession, check: VINCheck, user_id: str) -> bool:
    return _active_entitlement(db, check, user_id) is not None


def _teaser(
    db: DBSession,
    check: VINCheck,
    user_id: str,
    access: DeveloperAccessContext,
) -> VINPrecheckTeaser:
    unlocked = access.bypass_paywall or _has_entitlement(db, check, user_id)
    quality_ready = check.is_demo or bool(
        check.profile and paid_readiness(check.profile, check.full_history_payload).can_purchase
    )
    price, currency = (
        configured_vin_price("AZ")
        if (check.records_count > 0 or not check.is_demo)
        and not access.bypass_paywall
        and quality_ready
        else (None, None)
    )
    no_records, caution = _no_records_copy(check.language, check.records_count)
    if not check.is_demo and check.records_count == 0:
        from app.services.report_evidence_sections import history_status_text

        no_records, caution = history_status_text(check.full_history_payload, check.language)
    return VINPrecheckTeaser(
        check_id=check.id,
        vin=check.normalized_vin,
        vehicle=profile_dto(check.profile) if check.profile else None,
        found=check.found,
        records_count=check.records_count,
        photos_count=check.photos_count,
        auctions_count=check.auctions_count,
        has_salvage_title=check.has_salvage_title,
        odometer_risk=check.odometer_risk,
        details_locked=not unlocked,
        can_purchase=(check.records_count > 0 or not check.is_demo)
        and not unlocked
        and quality_ready,
        blurred_preview_data_url=(
            _blurred_preview(check.photos_count, is_demo=check.is_demo)
            if check.records_count > 0
            else None
        ),
        hidden_photos_count=max(0, check.photos_count - 1),
        price=price,
        currency=currency,
        no_records_message=no_records,
        caution_message=caution,
        demo_notice=_demo_notice(check.language) if check.is_demo else None,
        is_demo=check.is_demo,
        developer_mode=access.enabled,
        simulate_user_paywall=access.simulate_user_paywall,
    )


def _ensure_legacy_chat_context(
    db: DBSession,
    check: VINCheck,
    user_id: str,
) -> AutoExpertChatContext:
    existing = db.scalar(
        select(AutoExpertChatContext).where(
            AutoExpertChatContext.user_id == user_id,
            AutoExpertChatContext.vin_check_id == check.id,
        )
    )
    if existing is not None:
        return existing
    context = AutoExpertChatContext(
        user_id=user_id,
        vin_check_id=check.id,
        vehicle_profile_snapshot=(
            profile_dto(check.profile).model_dump(mode="json") if check.profile else {}
        ),
        vin_history_snapshot=VINHistoryPayload.model_validate(
            check.full_history_payload
        ).model_dump(mode="json"),
        report_snapshot=check.dossier_snapshot,
        sources_snapshot=check.source_snapshot,
        system_constraints={
            "facts_must_come_from_context": True,
            "preserve_evidence_status": True,
            "specific_vehicle_requires_inspection": True,
        },
        is_demo=check.is_demo,
    )
    db.add(context)
    db.flush()
    return context


def _fixture_vin_for_profile(
    profile: VehicleKnowledgeProfile,
    requested_vin: str | None,
    provider: DeterministicDemoVINPrecheckProvider,
) -> str:
    if requested_vin:
        normalized = requested_vin.upper()
        resolved = provider.resolve_vehicle(normalized)
        if resolved and resolved.make == profile.make and resolved.model == profile.model:
            return normalized
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Requested VIN does not match the selected vehicle profile fixture",
        )
    candidates: list[str] = []
    if profile.make == "Ford" and profile.model == "Fusion":
        candidates.append(FORD_EXAMPLE_VIN)
    elif profile.make == "Toyota" and profile.model == "Camry":
        candidates.append(TOYOTA_DEMO_VIN)
    for vin in candidates:
        resolved = provider.resolve_vehicle(vin)
        if resolved and resolved.make == profile.make and resolved.model == profile.model:
            return vin
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="No identity-compatible DEMO VIN-history fixture exists for this profile",
    )


def _fixture_source(db: DBSession, vin: str) -> SourceRecord:
    if vin == FORD_EXAMPLE_VIN:
        profile_id = seed_autoexpert2_ford_demo(db)
    else:
        profile_id = seed_autoexpert2_demo(db)
    db.flush()
    profile = db.get(VehicleKnowledgeProfile, profile_id)
    source = next((item for item in profile.sources if item.is_demo), None)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DEMO VIN-history source is not available",
        )
    return source


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


def _profile_snapshots(
    db: DBSession,
    profile: VehicleKnowledgeProfile,
    language: str,
) -> tuple[dict, list[dict]]:
    known_issues = list(
        db.scalars(
            select(KnownIssue).where(KnownIssue.vehicle_variant_id == profile.vehicle_variant_id)
        )
    )
    rows = DatabaseOwnerReviewProvider(db).observations_for(profile.vehicle_variant_id)
    official_rows = [
        item
        for item in rows
        if item.source.source_type == "OWNER_SUBMISSIONS_GOVERNMENT_REPOSITORY"
    ]
    owner_rows = [item for item in rows if item not in official_rows]

    def observations(values):  # noqa: ANN001, ANN202
        return [
            OwnerObservation(
                id=item.id,
                material_identity_key=item.material_identity_key,
                owner_identity_key=item.owner_identity_key,
                topic=item.topic,
                component=item.component,
                sentiment=item.sentiment,
                summary=item.summary,
                source_id=item.source_id,
                mileage_km=item.mileage_km,
                observed_at=item.observed_at.isoformat() if item.observed_at else None,
                is_demo=item.is_demo,
            )
            for item in values
        ]

    dossier = build_vehicle_dossier(
        profile,
        language=language,
        known_issues=known_issues,
        owner_feedback=OwnerFeedbackEngine().aggregate(observations(owner_rows)),
        owner_source_ids=list(dict.fromkeys(item.source_id for item in owner_rows)),
        official_complaints_feedback=OwnerFeedbackEngine().aggregate(observations(official_rows)),
        official_complaint_source_ids=list(dict.fromkeys(item.source_id for item in official_rows)),
    )
    return (
        dossier.model_dump(mode="json"),
        [_source_snapshot(item).model_dump(mode="json") for item in profile.sources],
    )


def _replace_fixture_source_ids(payload: dict, source_ids: list[str]) -> None:
    for collection in (
        "timeline",
        "auctions",
        "photos",
        "damage_details",
        "odometer_records",
    ):
        for item in payload.get(collection, []):
            item["source_ids"] = source_ids


def _no_records_copy(language: str, records_count: int) -> tuple[str | None, str | None]:
    if records_count > 0:
        return None, None
    if language == "az":
        return (
            "Qoşulmuş mənbələrdə bu VIN üzrə qeyd tapılmadı. Məlumat yoxdursa, "
            "ödənişli VIN hesabatı təklif etmirik.",
            "Bu, qəza və ya digər hadisələrin olmadığına zəmanət vermir.",
        )
    if language == "en":
        return (
            "No records for this VIN were found in connected sources. We do not offer a paid "
            "VIN report when no data is available.",
            "This is not a guarantee that no collision or other event occurred.",
        )
    return (
        "В подключённых источниках записи по этому VIN не найдены. Мы не предлагаем "
        "платный VIN-отчёт, если данных нет.",
        "Это не является гарантией отсутствия ДТП или других событий.",
    )


def _demo_notice(language: str) -> str:
    if language == "az":
        return "DEMO DATA: məlumatlar sintetikdir və real VIN tarixçəsi deyil."
    if language == "en":
        return "DEMO DATA: the records are synthetic and are not real VIN history."
    return "DEMO DATA: сведения синтетические и не являются реальной историей VIN."


def _blurred_preview(photo_count: int, *, is_demo: bool = True) -> str:
    hidden = max(0, photo_count - 1)
    count_label = f"+{hidden} DEMO" if is_demo else f"+{hidden}"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="420">
    <defs><filter id="b"><feGaussianBlur stdDeviation="18"/></filter></defs>
    <rect width="720" height="420" fill="#111b24"/>
    <g filter="url(#b)"><rect x="70" y="65" width="580" height="290" rx="34" fill="#7b8790"/>
    <circle cx="210" cy="325" r="54" fill="#26323c"/>
    <circle cx="520" cy="325" r="54" fill="#26323c"/></g>
    <rect x="0" y="330" width="720" height="90" fill="#0b1117" fill-opacity=".86"/>
    <text x="360" y="386" fill="#f2c35a" font-size="34"
      text-anchor="middle" font-family="sans-serif">{count_label}</text>
    </svg>"""
    encoded = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"

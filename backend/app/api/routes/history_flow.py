"""Authenticated, mock-only VIN history checkout endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, DBSession
from app.core.config import get_settings
from app.models.history_flow import (
    HistoryAsset,
    ProviderTransaction,
    VehicleHistoryReport,
    VinCheckRequest,
)
from app.providers.history_fixture import FixtureHistoryProvider
from app.schemas.history_flow import (
    HistoryCheckCreate,
    HistoryCheckRead,
    HistoryReportRead,
    MockHistoryPayment,
)
from app.services.history_flow import (
    check_read,
    create_check,
    entitlement,
    fetch_report,
    mock_payment,
    owned_check,
    publish_normalized,
    report_read,
)

router = APIRouter(prefix="/vin/history", tags=["vin-history"])


def get_history_provider() -> FixtureHistoryProvider:
    return FixtureHistoryProvider()


HistoryProvider = Annotated[FixtureHistoryProvider, Depends(get_history_provider)]


def _mock_enabled() -> None:
    settings = get_settings()
    if (
        settings.environment == "production"
        or not settings.demo_mode
        or settings.payment_provider != "mock"
    ):
        raise HTTPException(404, "History fixture unavailable")


def _owned(db: DBSession, user_id: str, check_id: str, *, lock: bool = False) -> VinCheckRequest:
    check = owned_check(db, user_id, check_id, lock=lock)
    if check is None or (get_settings().environment == "production" and check.is_mock):
        raise HTTPException(404, "VIN check not found")
    return check


@router.post("/checks", response_model=HistoryCheckRead, status_code=201)
def start_history_check(
    value: HistoryCheckCreate, db: DBSession, user: CurrentUser, provider: HistoryProvider
) -> HistoryCheckRead:
    _mock_enabled()
    try:
        check = create_check(
            db, user_id=user.id, vin=value.vin, language=value.language, provider=provider
        )
    except IntegrityError:
        db.rollback()
        check = db.scalar(
            select(VinCheckRequest).where(
                VinCheckRequest.user_id == user.id,
                VinCheckRequest.vin == value.vin,
                VinCheckRequest.provider_id == provider.id,
                VinCheckRequest.product == "VIN_HISTORY",
            )
        )
        if check is None:
            raise HTTPException(409, "VIN check already processing") from None
    return check_read(db, check, user.id)


@router.get("/checks", response_model=list[HistoryCheckRead])
def list_history_checks(db: DBSession, user: CurrentUser) -> list[HistoryCheckRead]:
    checks = db.scalars(
        select(VinCheckRequest)
        .where(VinCheckRequest.user_id == user.id)
        .order_by(VinCheckRequest.created_at.desc())
    )
    return [
        check_read(db, check, user.id)
        for check in checks
        if get_settings().environment != "production" or not check.is_mock
    ]


@router.get("/checks/{check_id}", response_model=HistoryCheckRead)
def get_history_check(check_id: str, db: DBSession, user: CurrentUser) -> HistoryCheckRead:
    return check_read(db, _owned(db, user.id, check_id), user.id)


@router.post("/checks/{check_id}/payments/mock", response_model=HistoryCheckRead)
def pay_history_mock(
    check_id: str,
    value: MockHistoryPayment,
    db: DBSession,
    user: CurrentUser,
    provider: HistoryProvider,
) -> HistoryCheckRead:
    _mock_enabled()
    check = _owned(db, user.id, check_id, lock=True)
    try:
        mock_payment(
            db, check, user_id=user.id, provider=provider, simulate_failure=value.simulate_failure
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    except IntegrityError:
        # A concurrent double-click can race the first SELECT, especially on
        # SQLite where FOR UPDATE is ignored. Unique DB keys win; reload the
        # committed owner-owned result rather than creating another charge.
        db.rollback()
        check = _owned(db, user.id, check_id)
        if entitlement(db, check, user.id) is None:
            raise HTTPException(409, "Payment already processing") from None
    return check_read(db, check, user.id)


@router.post("/checks/{check_id}/retry", response_model=HistoryCheckRead)
def retry_history_fetch(
    check_id: str, db: DBSession, user: CurrentUser, provider: HistoryProvider
) -> HistoryCheckRead:
    _mock_enabled()
    check = _owned(db, user.id, check_id)
    if entitlement(db, check, user.id) is None:
        raise HTTPException(402, "History report is locked")
    if check.status not in {"PAID", "PROVIDER_REQUESTED", "FAILED_RETRYABLE"}:
        raise HTTPException(409, "Retry unavailable for current state")
    fetch_report(db, check, provider=provider)
    return check_read(db, check, user.id)


@router.post("/checks/{check_id}/provider/mock/callback", response_model=HistoryCheckRead)
def repeatable_mock_provider_callback(
    check_id: str, db: DBSession, user: CurrentUser, provider: HistoryProvider
) -> HistoryCheckRead:
    """Test-only repeat callback. Real webhook authorization is not yet configured."""
    _mock_enabled()
    check = _owned(db, user.id, check_id)
    if entitlement(db, check, user.id) is None:
        raise HTTPException(402, "History report is locked")
    txn = db.scalar(
        select(ProviderTransaction).where(
            ProviderTransaction.request_id == check.id, ProviderTransaction.kind == "REPORT"
        )
    )
    if txn is None:
        raise HTTPException(409, "Provider request not started")
    raw = provider.get_report(f"fixture:{check.vin}")
    normalized = provider.normalize(raw)
    publish_normalized(
        db,
        check,
        txn,
        normalized,
        raw=raw,
        asset_bytes=provider.get_assets(normalized["provider_report_id"]),
    )
    return check_read(db, check, user.id)


@router.get("/checks/{check_id}/report", response_model=HistoryReportRead)
def get_history_report(
    check_id: str,
    db: DBSession,
    user: CurrentUser,
    language: str = Query(default="ru", pattern="^(ru|az|en)$"),
) -> HistoryReportRead:
    check = _owned(db, user.id, check_id)
    if entitlement(db, check, user.id) is None:
        raise HTTPException(402, "History report is locked")
    if (
        db.scalar(select(VehicleHistoryReport).where(VehicleHistoryReport.request_id == check.id))
        is None
    ):
        raise HTTPException(409, check.status)
    return report_read(db, check, language=language)


@router.get("/checks/{check_id}/assets/{asset_id}")
def get_history_asset(check_id: str, asset_id: str, db: DBSession, user: CurrentUser) -> Response:
    check = _owned(db, user.id, check_id)
    if entitlement(db, check, user.id) is None:
        raise HTTPException(402, "History report is locked")
    report = db.scalar(
        select(VehicleHistoryReport).where(VehicleHistoryReport.request_id == check.id)
    )
    if report is None:
        raise HTTPException(409, "History report unavailable")
    asset = db.scalar(
        select(HistoryAsset).where(
            HistoryAsset.id == asset_id,
            HistoryAsset.report_id == report.id,
            HistoryAsset.display_rights_confirmed.is_(True),
        )
    )
    if asset is None or asset.payload is None:
        raise HTTPException(404, "History asset not found")
    if asset.media_type not in {"image/jpeg", "image/png", "image/webp"} and not (
        check.is_mock
        and check.provider_id == "local_history_fixture"
        and asset.media_type == "image/svg+xml"
    ):
        raise HTTPException(409, "Asset format not supported")
    return Response(
        content=asset.payload,
        media_type=asset.media_type,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; sandbox",
        },
    )

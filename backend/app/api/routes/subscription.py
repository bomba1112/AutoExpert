"""The subscription screen's API (product phase, stage 6), behind subscription_v1. Rights only:
no real payment; the store purchase is a stub outside production (entitlements.purchase_stub)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.dependencies import CurrentUser, DBSession
from app.services import entitlements

router = APIRouter(prefix="/subscription", tags=["subscription"])
Language = Literal["ru", "az", "en"]


class PurchaseIn(BaseModel):
    store: Literal["APP_STORE", "GOOGLE_PLAY"]


def _enabled() -> None:
    if not entitlements.enabled():
        raise HTTPException(404, "SUBSCRIPTION_DISABLED")


@router.get("")
def status(db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    data = entitlements.offer(db, user, language)
    db.commit()
    return data


@router.post("/trial", status_code=201)
def trial(db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    try:
        entitlements.start_trial(db, user)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None
    db.commit()
    return entitlements.offer(db, user, language)


@router.post("/purchase", status_code=201)
def purchase(
    value: PurchaseIn, db: DBSession, user: CurrentUser, language: Language = "ru"
) -> dict:
    """App Store / Google Play are not connected yet: outside production this activates a month
    without any charge; in production it answers 501 STORE_NOT_CONNECTED."""
    _enabled()
    try:
        entitlements.purchase_stub(db, user, value.store)
    except ValueError as exc:
        raise HTTPException(501, str(exc)) from None
    db.commit()
    return entitlements.offer(db, user, language)


@router.post("/cancel")
def cancel(db: DBSession, user: CurrentUser, language: Language = "ru") -> dict:
    _enabled()
    entitlements.cancel(db, user)
    db.commit()
    return entitlements.offer(db, user, language)

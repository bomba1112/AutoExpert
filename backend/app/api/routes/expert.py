# ruff: noqa: E501
"""The Auto Expert opinion on one car (UI-by-reference prompt, section 3), behind the
expert_opinion_v1 flag: a Turbo.az listing link (fetched once on the user's request), a VIN, the
listing text the user pasted, or what the user knows."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import CurrentUser, DBSession
from app.services import listing_opinion

router = APIRouter(prefix="/expert", tags=["expert"])


class Manual(BaseModel):
    make: str = Field(max_length=60)
    model: str = Field(max_length=80)
    year: int | None = Field(default=None, ge=1950, le=2100)
    engine: str | None = Field(default=None, max_length=40)
    fuel: str | None = Field(default=None, max_length=40)
    transmission: str | None = Field(default=None, max_length=40)
    drivetrain: str | None = Field(default=None, max_length=40)
    mileage_km: int | None = Field(default=None, ge=0, le=3_000_000)


class OpinionRequest(BaseModel):
    query: str | None = Field(default=None, max_length=600)
    text: str | None = Field(default=None, max_length=60_000)
    manual: Manual | None = None
    language: Literal["ru", "az", "en"] = "ru"


@router.post("/opinion")
def expert_opinion(value: OpinionRequest, db: DBSession, user: CurrentUser) -> dict:
    if not listing_opinion.enabled():
        raise HTTPException(404, "EXPERT_OPINION_DISABLED")
    if not (value.query or value.text or value.manual):
        raise HTTPException(422, "INPUT_REQUIRED")
    result = listing_opinion.opinion(db, query=value.query, text=value.text,
                                     manual=value.manual.model_dump() if value.manual else None, language=value.language)
    db.commit()  # the listing page cache
    return result

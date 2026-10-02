"""Owned, user-assisted listing intake endpoints; no live site access."""

from fastapi import APIRouter, HTTPException

from app.api.dependencies import CurrentUser, DBSession
from app.schemas.listing_intake import ListingIntakeCreate, ListingIntakeRead
from app.services.listing_intake import ListingInputError, create_intake, get_intake

router = APIRouter(prefix="/listings/intake", tags=["listing-intake"])


@router.post("", response_model=ListingIntakeRead)
def create_listing_intake(value: ListingIntakeCreate, db: DBSession, user: CurrentUser):
    try:
        return create_intake(db, user.id, value)
    except ListingInputError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/{intake_id}", response_model=ListingIntakeRead)
def read_listing_intake(intake_id: str, db: DBSession, user: CurrentUser):
    result = get_intake(db, user.id, intake_id)
    if result is None:
        raise HTTPException(404, "Listing intake not found")
    return result

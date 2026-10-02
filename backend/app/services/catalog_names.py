"""Reuse catalog names across legacy compact and newer spaced normalization."""

from sqlalchemy import select

from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant


def compact_name(value):
    return "".join(c for c in str(value or "").casefold() if c.isalnum())


def existing_name(db, name, *, make_id=None):
    """Match labels only; never infer shared generations, markets or technical facts."""
    entity = VehicleMake if make_id is None else VehicleModel
    query = select(entity)
    if make_id is not None:
        query = query.where(VehicleModel.make_id == make_id)
    rows = list(db.scalars(query))
    exact = [r for r in rows if r.name.casefold() == name.casefold()]
    matches = exact or [r for r in rows if compact_name(r.name) == compact_name(name)]
    if len(matches) > 1:
        if make_id is not None:
            published = [
                row
                for row in matches
                if db.scalar(
                    select(VehicleVariant.id)
                    .join(VehicleGeneration, VehicleVariant.generation_id == VehicleGeneration.id)
                    .where(
                        VehicleGeneration.model_id == row.id,
                        VehicleVariant.published_revision_id.is_not(None),
                    )
                    .limit(1)
                )
            ]
            if len(published) == 1:
                return published[0]
        raise ValueError("AMBIGUOUS_CATALOG_NAME_REQUIRES_REVIEW")
    return matches[0] if matches else None

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.schemas.analysis import AnalysisCreate


class VehicleNotResolvedError(ValueError):
    pass


def _normalize(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


class VehicleRepository:
    def __init__(self, session: Session):
        self.session = session

    def resolve(self, request: AnalysisCreate) -> VehicleVariant:
        # This legacy report path consumes raw VehicleVariant columns. Production
        # catalogue responses use a separate fact-level rights projection.
        if get_settings().environment == "production":
            raise VehicleNotResolvedError(
                "Legacy analysis is not available for publication"
            )
        load = (
            joinedload(VehicleVariant.generation)
            .joinedload(VehicleGeneration.model)
            .joinedload(VehicleModel.make)
        )
        if request.vehicle_variant_id:
            variant = self.session.scalar(
                select(VehicleVariant)
                .options(load)
                .where(VehicleVariant.id == request.vehicle_variant_id)
            )
            if variant is None:
                raise VehicleNotResolvedError("Vehicle variant was not found")
            if variant.catalog_key:
                from app.services.catalog_buyer import records

                if not any(v.id == variant.id for v, _ in records(self.session)):
                    raise VehicleNotResolvedError(
                        "Catalogue source is not available for publication"
                    )
            if variant.market != request.vehicle.country:
                raise VehicleNotResolvedError("Vehicle variant does not match the selected market")
            return variant

        statement = (
            select(VehicleVariant)
            .join(VehicleGeneration)
            .join(VehicleModel)
            .join(VehicleMake)
            .options(load)
            .where(
                VehicleVariant.catalog_key.is_(None),
                VehicleVariant.market == request.vehicle.country,
                VehicleMake.normalized_name == _normalize(request.vehicle.make),
                VehicleModel.normalized_name == _normalize(request.vehicle.model),
                or_(
                    VehicleVariant.year_from.is_(None),
                    VehicleVariant.year_from <= request.vehicle.year,
                ),
                or_(
                    VehicleVariant.year_to.is_(None), VehicleVariant.year_to >= request.vehicle.year
                ),
            )
        )
        if request.vehicle.generation:
            generation = request.vehicle.generation.casefold()
            statement = statement.where(
                or_(
                    func.lower(VehicleGeneration.name) == generation,
                    func.lower(VehicleGeneration.code) == generation,
                )
            )
        candidates = list(self.session.scalars(statement))
        if request.vehicle.engine:
            exact = [
                item
                for item in candidates
                if item.engine and _normalize(item.engine) == _normalize(request.vehicle.engine)
            ]
            candidates = exact or candidates
        if request.vehicle.transmission:
            exact = [
                item
                for item in candidates
                if item.transmission
                and _normalize(item.transmission) == _normalize(request.vehicle.transmission)
            ]
            candidates = exact or candidates
        if len(candidates) != 1:
            raise VehicleNotResolvedError(
                "Vehicle modification is missing or ambiguous; select an exact variant"
            )
        return candidates[0]

from collections import defaultdict

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.dependencies import DBSession
from app.core.config import get_settings
from app.models.catalog import (
    CountryProfile,
    RegionProfile,
    VehicleGeneration,
    VehicleModel,
    VehicleVariant,
)
from app.schemas.analysis import CatalogCountry, CatalogResponse, CatalogVariant

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/options", response_model=CatalogResponse)
def catalog_options(db: DBSession) -> CatalogResponse:
    settings = get_settings()
    variants_query = (
        select(VehicleVariant)
        .where(VehicleVariant.catalog_key.is_(None))
        .options(
            joinedload(VehicleVariant.generation)
            .joinedload(VehicleGeneration.model)
            .joinedload(VehicleModel.make)
        )
    )
    countries_query = select(CountryProfile)
    if settings.environment != "production" and settings.demo_mode:
        variants_query = variants_query.where(VehicleVariant.is_demo.is_(True))
        countries_query = countries_query.where(CountryProfile.is_demo.is_(True))
    else:
        variants_query = variants_query.where(VehicleVariant.is_demo.is_(False))
        countries_query = countries_query.where(CountryProfile.is_demo.is_(False))

    # Legacy variants have no field-level publication rights. Keep the research
    # catalogue available locally, but do not advertise its raw specifications.
    variants = (
        []
        if settings.environment == "production"
        else list(db.scalars(variants_query.order_by(VehicleVariant.name)))
    )
    countries = list(db.scalars(countries_query.order_by(CountryProfile.country_code)))
    regions = list(db.scalars(select(RegionProfile).order_by(RegionProfile.name)))
    cities_by_country: dict[str, list[str]] = defaultdict(list)
    for region in regions:
        if region.city and region.city not in cities_by_country[region.country_id]:
            cities_by_country[region.country_id].append(region.city)

    currencies = {country.country_code: country.currency for country in countries}
    return CatalogResponse(
        countries=[
            CatalogCountry(
                code=country.country_code,
                currency=country.currency,
                cities=cities_by_country[country.id],
                is_demo=country.is_demo,
            )
            for country in countries
        ],
        variants=[
            CatalogVariant(
                id=variant.id,
                country=variant.market,
                make=variant.generation.model.make.name,
                model=variant.generation.model.name,
                generation=variant.generation.name,
                generation_code=variant.generation.code,
                year_from=variant.year_from,
                year_to=variant.year_to,
                engine=variant.engine,
                transmission=variant.transmission,
                drivetrain=variant.drivetrain,
                body=variant.body,
                fuel=variant.fuel,
                currency=currencies.get(variant.market, ""),
                is_demo=variant.is_demo,
            )
            for variant in variants
        ],
    )

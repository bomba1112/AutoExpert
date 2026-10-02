"""Executable acquisition policy. Public access is not a reuse licence."""

from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.models.knowledge_ops import SourceRegistry

EPA_URL = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"


def seed_registry(db):
    definitions = [
        (
            "epa",
            "DOE / EPA FuelEconomy.gov",
            "https://www.fueleconomy.gov/feg/ws/index.shtml",
            "LOCAL_RESEARCH",
            "epa-csv-v1",
            [EPA_URL],
        ),
        (
            "nhtsa",
            "NHTSA / vPIC",
            "https://vpic.nhtsa.dot.gov/api/",
            "EXISTING_ADAPTER",
            "existing-vpic",
            [],
        ),
        (
            "kr-recalls",
            "Korea Automobile Recall Center",
            "https://www.car.go.kr/eng/main.do",
            "NEEDS_PERMISSION",
            "manual",
            [],
        ),
        (
            "jp-mlit",
            "Japan MLIT",
            "https://www.mlit.go.jp/jidosha/carinf/rcl/recall_searchinfo.html",
            "SEARCH_SUSPENDED",
            "manual",
            [],
        ),
        ("cn-miit", "China MIIT", "https://www.miit.gov.cn/", "NEEDS_PERMISSION", "manual", []),
        ("cn-samr", "China SAMR", "https://www.samrdprc.org.cn/", "NEEDS_PERMISSION", "manual", []),
        (
            "eu-safety-gate",
            "EU Safety Gate",
            "https://ec.europa.eu/safety-gate-alerts/screen/webReport",
            "NEEDS_PERMISSION",
            "manual",
            [],
        ),
        (
            "euroncap",
            "Euro NCAP",
            "https://www.euroncap.com/home/",
            "NEEDS_PERMISSION",
            "manual",
            [],
        ),
        ("iihs", "IIHS", "https://www.iihs.org/ratings", "NEEDS_PERMISSION", "manual", []),
        ("az-editorial", "AZ licensed editorial documents", None, "NEEDS_PERMISSION", "manual", []),
    ]
    for key, title, docs, state, adapter, urls in definitions:
        market = {
            "epa": "US",
            "nhtsa": "US",
            "kr-recalls": "KR",
            "jp-mlit": "JP",
            "cn-miit": "CN",
            "cn-samr": "CN",
            "eu-safety-gate": "EU",
            "euroncap": "EU",
            "iihs": "US",
            "az-editorial": "AZ",
        }[key]
        metadata = {
            "owner": title,
            "markets": [market],
            "data_types": {
                "epa": ["configuration", "test_cycle_consumption"],
                "nhtsa": ["identity", "recall", "complaint", "manufacturer_communication"],
                "az-editorial": ["market_observation", "local_cost", "licensed_documents"],
            }.get(key, ["official_documents"]),
            "authentication": "NONE_PUBLIC" if key in {"epa", "nhtsa"} else "VERIFY_PER_DOCUMENT",
            "storage_rights": "NON_COMMERCIAL_RESEARCH" if key == "epa" else "UNVERIFIED",
            "display_rights": "NON_COMMERCIAL_RESEARCH" if key == "epa" else "UNVERIFIED",
            "resale_rights": "UNVERIFIED",
        }
        research_ids = (
            [
                "nhtsa_vpic",
                "nhtsa_safety_ratings_variants",
                "nhtsa_recalls",
                "nhtsa_complaints",
                "nhtsa_manufacturer_communications",
            ]
            if key == "nhtsa"
            else ["epa_vehicle_configuration"]
            if key == "epa"
            else []
        )
        existing = db.get(SourceRegistry, key)
        if existing:
            existing.config = {**metadata, **existing.config}
            if "research_provider_ids" not in existing.config:
                existing.config = {**existing.config, "research_provider_ids": research_ids}
            continue
        db.add(
            SourceRegistry(
                id=key,
                title=title,
                state=state,
                config={
                    **metadata,
                    "documentation_url": docs,
                    "adapter": adapter,
                    "allowed_download_urls": urls,
                    "checked_at": "2026-09-18",
                    "commercial_reuse": False,
                    "rights": "NON_COMMERCIAL_SCIENTIFIC_EDUCATIONAL"
                    if key == "epa"
                    else "UNVERIFIED",
                    "rights_url": "https://www.fueleconomy.gov/feg/ORNL-disclaimer.htm"
                    if key == "epa"
                    else None,
                    "access": "PUBLIC_DOWNLOAD" if urls else "MANUAL_REVIEW",
                    "cost_model": "FREE" if urls else "UNKNOWN",
                    "verified_rate_limit": None,
                    "request_budget": 1 if urls else 0,
                    "research_provider_ids": research_ids,
                    "freshness_days": {
                        "specifications": 365,
                        "recalls": 7,
                        "prices": 30,
                        "rights": 90,
                    },
                    "limitations": "Vehicle photographs excluded; commercial permission unresolved."
                    if key == "epa"
                    else "No automatic acquisition or publication without documented rights.",
                },
            )
        )
    # These live endpoints have separate rights from the vehicles.csv ZIP.
    # My MPG also contains owner-submitted material and needs its own decision.
    epa_live_sources = (
        (
            "epa-vehicle-api",
            "FuelEconomy.gov vehicle API (rights review)",
            "https://www.fueleconomy.gov/ws/rest/vehicle/menu/model",
            "epa_vehicle_configuration",
            "vehicle_configuration_and_fuel_economy",
        ),
        (
            "epa-my-mpg",
            "FuelEconomy.gov My MPG owner logs (rights review)",
            "https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles",
            "epa_my_mpg",
            "owner_submitted_fuel_logs",
        ),
    )
    for source_id, title, dataset_url, provider_id, data_type in epa_live_sources:
        if db.get(SourceRegistry, source_id) is not None:
            continue
        db.add(
            SourceRegistry(
                id=source_id,
                title=title,
                state="LOCAL_RESEARCH",
                paused=False,
                config={
                    "owner": "US Department of Energy / Environmental Protection Agency",
                    "markets": ["US"],
                    "data_types": [data_type],
                    "dataset_url": dataset_url,
                    "documentation_url": "https://www.fueleconomy.gov/feg/ws/index.shtml",
                    "rights_url": "https://www.fueleconomy.gov/feg/ORNL-disclaimer.htm",
                    "checked_at": "2026-09-28",
                    "commercial_reuse": False,
                    "research_provider_ids": [provider_id],
                    "limitations": "Endpoint-specific commercial reuse has not been established.",
                },
            )
        )
    # This entry covers only Wikidata's structured entity/statement data. It
    # does not confer rights to article text, media, or third-party references.
    if db.get(SourceRegistry, "wikidata-structured-cc0") is None:
        db.add(
            SourceRegistry(
                id="wikidata-structured-cc0",
                title="Wikidata structured statements (CC0)",
                state="APPROVED",
                paused=False,
                config={
                    "owner": "Wikimedia Foundation / Wikidata contributors",
                    "markets": ["US"],
                    "data_types": ["structured_entity_statements"],
                    "dataset_url": "https://www.wikidata.org/wiki/Special:EntityData",
                    "documentation_url": "https://www.wikidata.org/wiki/Wikidata:Database_download",
                    "rights_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                    "rights": "CC0_1.0_STRUCTURED_DATA_ONLY",
                    "checked_at": "2026-09-28",
                    "commercial_reuse": True,
                    "storage_rights": "CC0",
                    "display_rights": "CC0",
                    "resale_rights": "CC0",
                    "access": "PUBLIC_STRUCTURED_DATA",
                    "cost_model": "FREE",
                    "limitations": (
                        "Entity/Property/Lexeme/EntitySchema statements only; "
                        "no Wikipedia text, Commons media, images or third-party material. "
                        "A global model entity does not establish a US annual configuration."
                    ),
                },
            )
        )
    # The vPIC Vehicle API is a distinct dataset from other NHTSA feeds. Its
    # Data.gov Access & Use metadata currently says "unknown-license", so
    # public API access alone cannot make its fields production evidence.
    if db.get(SourceRegistry, "nhtsa-vpic-vehicle-api") is None:
        db.add(
            SourceRegistry(
                id="nhtsa-vpic-vehicle-api",
                title="NHTSA vPIC Vehicle API (dataset-specific rights review)",
                state="LOCAL_RESEARCH",
                paused=False,
                config={
                    "owner": "National Highway Traffic Safety Administration",
                    "markets": ["US"],
                    "data_types": ["vehicle_identity"],
                    "dataset_url": (
                        "https://catalog.data.gov/dataset/"
                        "nhtsa-product-information-catalog-and-vehicle-listing-vpic-vehicle-api-json"
                    ),
                    "documentation_url": "https://vpic.nhtsa.dot.gov/api/",
                    "rights_url": (
                        "https://catalog.data.gov/dataset/"
                        "nhtsa-product-information-catalog-and-vehicle-listing-vpic-vehicle-api-json"
                    ),
                    "access_and_use_license": "unknown-license",
                    "checked_at": "2026-09-28",
                    "commercial_reuse": False,
                    "limitations": (
                        "Access & Use license is unknown; cached model-year identity is "
                        "review-only and never confirms exact mechanics."
                    ),
                },
            )
        )
    db.commit()


def require_source(db, source_id, *, acquire=False, production=None):
    source = db.get(SourceRegistry, source_id)
    if source is None:
        raise ValueError("SOURCE_NOT_REGISTERED")
    if source.paused:
        raise ValueError("SOURCE_PAUSED")
    if source.state not in {"APPROVED", "LOCAL_RESEARCH"}:
        raise ValueError("SOURCE_PERMISSION_REQUIRED")
    production = get_settings().environment == "production" if production is None else production
    if production and not source.config.get("commercial_reuse"):
        raise ValueError("COMMERCIAL_RIGHTS_REQUIRED")
    if acquire and source.config.get("cost_model") != "FREE":
        raise ValueError("PAID_ACQUISITION_NOT_AUTHORIZED")
    if acquire and source.config.get("backoff_until"):
        try:
            until = datetime.fromisoformat(source.config["backoff_until"])
            if until.tzinfo is None:
                until = until.replace(tzinfo=UTC)
            if until > utcnow():
                raise ValueError("SOURCE_BACKOFF_ACTIVE")
        except (TypeError, OverflowError):
            raise ValueError("INVALID_SOURCE_BACKOFF") from None
    return source


def registry_view(db):
    return [
        {"id": s.id, "title": s.title, "state": s.state, "paused": s.paused, **s.config}
        for s in db.scalars(select(SourceRegistry).order_by(SourceRegistry.id))
    ]


def utcnow():
    return datetime.now(UTC)

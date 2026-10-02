"""Production must never turn an EPA candidate or a status string into evidence."""

from copy import deepcopy

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.knowledge_ops import SourceRegistry
from app.models.user import User
from app.schemas.knowledge import BuyerFilters
from app.services import catalog_buyer as buyer
from app.services.commercial_fact_overlay import upsert_claim
from app.services.listing_intake import _candidate

FACTORY = "https://www.toyota.com/content/dam/toyota/brochures/pdf/2018/camry.pdf"
RIGHTS = "https://www.copyright.gov/register/tx-databases.html"


def candidate(db):
    make = VehicleMake(name="Toyota", normalized_name="toyota")
    model = VehicleModel(make=make, name="Camry", normalized_name="camry")
    generation = VehicleGeneration(model=model, name="Generation unverified", code="UNRESOLVED")
    db.add_all(
        [
            SourceRegistry(
                id="epa",
                title="EPA",
                state="LOCAL_RESEARCH",
                paused=False,
                config={"commercial_reuse": False},
            ),
            SourceRegistry(
                id="factory-toyota-us",
                title="Toyota",
                state="LOCAL_RESEARCH",
                paused=False,
                config={"commercial_reuse": False, "factory_identity_evidence": True},
            ),
        ]
    )
    catalog = {
        "make": "Toyota",
        "model": "Camry",
        "model_year": 2018,
        "original_market": "US",
        "generation": "Generation unverified",
        "generation_code": "UNRESOLVED",
        "configuration": "EPA research configuration",
        "source_registry_id": "epa",
        "source_url": "https://www.fueleconomy.gov/ws/rest/vehicle/1",
        "publication_scope": "LOCAL_RESEARCH",
        "revision_id": "epa-revision",
        "published_at": "2026-09-20T00:00:00+00:00",
        "facts": {
            "powertrain": {"value": "ICE", "status": "CONFIRMED"},
            "fuel": {"value": "GASOLINE", "status": "CONFIRMED"},
            "engine_displacement": {"value": "2.5", "status": "CONFIRMED"},
            "engine_description": {"value": "2.5 L I4", "status": "CONFIRMED"},
            "transmission_description": {"value": "Automatic (S8)", "status": "CONFIRMED"},
            "transmission_family": {"value": "AUTOMATIC_UNSPECIFIED", "status": "CONFIRMED"},
            "drivetrain": {"value": "FWD", "status": "CONFIRMED"},
            "seats": {"value": 5, "status": "CONFIRMED"},
            "fuel_combined": {"value": 7.4, "status": "CONFIRMED"},
        },
    }
    variant = VehicleVariant(
        generation=generation,
        market="US",
        name="EPA research configuration",
        year_from=2018,
        year_to=2018,
        is_demo=False,
        published_revision_id="epa-revision",
        specifications={"catalog": catalog},
    )
    db.add(variant)
    db.flush()
    return variant, catalog


def claim(db, variant, catalog, key, *, status="COMMERCIAL_OK", value=None, scope=None):
    identity = key in {"make", "model", "model_year", "original_market"}
    fact_value = catalog[key] if identity else catalog["facts"][key]["value"]
    evidence_scope = {
        "make": "Toyota",
        "model": "Camry",
        "model_year": 2018,
        "original_market": "US",
        "granularity": "MODEL_YEAR" if identity else "EXACT_CONFIGURATION",
        "source_record_id": "toyota-2018-brochure",
        "source_authenticity": "OFFICIAL_PUBLISHER",
        "extraction_scope": "ISOLATED_FACT",
        "source_document_kind": "BROCHURE",
        "az_rights_reference": "https://www.wipo.int/wipolex/en/legislation/details/22657",
        "configuration_keys": {
            "engine_displacement": "2.5",
            "engine_description": "2.5 L I4",
            "transmission_description": "Automatic (S8)",
            "drivetrain": "FWD",
        },
    }
    evidence_scope.update(scope or {})
    return upsert_claim(
        db,
        variant_id=variant.id,
        fact_name=key,
        value=fact_value if value is None else value,
        source_id="factory-toyota-us",
        evidence_scope=evidence_scope,
        reuse_status=status,
        source_url=FACTORY,
        locator=f"2018 Camry brochure · {key}",
        rights_basis="FACTUAL_EXTRACTION",
        rights_reference=RIGHTS,
        rights_checked_at="2026-09-28",
    )


def test_development_consumer_catalog_uses_rights_cleared_projection(
    db_session, client, monkeypatch
):
    variant, catalog = candidate(db_session)
    internal_catalog = deepcopy(catalog)
    internal_catalog.update(
        model_year=2019,
        configuration="Research-only configuration",
        revision_id="epa-internal-2019",
    )
    internal = VehicleVariant(
        generation=variant.generation,
        market="US",
        name="Research-only configuration",
        year_from=2019,
        year_to=2019,
        is_demo=False,
        published_revision_id="epa-internal-2019",
        specifications={"catalog": internal_catalog},
    )
    db_session.add(internal)
    for key in (
        "make",
        "model",
        "model_year",
        "original_market",
        "powertrain",
        "fuel",
        "engine_displacement",
        "engine_description",
        "transmission_description",
        "drivetrain",
    ):
        claim(db_session, variant, catalog, key)
    db_session.flush()
    monkeypatch.setattr(get_settings(), "environment", "development")

    assert len(buyer.records(db_session)) == 2
    facets = client.get("/api/v1/knowledge/facets")
    assert facets.status_code == 200
    assert facets.json()["counts"]["published_versions"] == 1
    base = client.get("/api/v1/knowledge/facets", params={"catalog_scope": "US_BASE_2000"})
    strict = client.get(
        "/api/v1/knowledge/facets", params={"catalog_scope": "US_CONFIRMED_2000"}
    )
    assert base.json()["counts"]["published_versions"] == 1
    assert strict.json()["counts"]["published_versions"] == 0
    search = client.post(
        "/api/v1/knowledge/search",
        json={"catalog_scope": "US_BASE_2000", "year_min": 2019, "year_max": 2019},
    )
    assert search.status_code == 200
    assert search.json()["matched_versions"] == 0
    assert search.json()["uncertain_versions"] == 0
    visible_search = client.post(
        "/api/v1/knowledge/search",
        json={"catalog_scope": "US_BASE_2000", "year_min": 2018, "year_max": 2018},
    )
    assert visible_search.json()["matched_versions"] == 1
    resolve = client.post(
        "/api/v1/knowledge/resolve",
        json={
            "catalog_scope": "US_BASE_2000",
            "make": "Toyota", "model": "Camry", "year": 2019,
        },
    )
    assert resolve.status_code == 200
    assert resolve.json()["candidate_count"] == 0
    assert client.get(f"/api/v1/knowledge/vehicles/{internal.id}").status_code == 404
    visible = client.get(f"/api/v1/knowledge/vehicles/{variant.id}")
    assert visible.status_code == 200
    assert visible.json()["source_url"] == FACTORY
    assert "fuel_combined" not in visible.json()["facts"]

    user = User(
        email="consumer@example.test",
        password_hash=hash_password("isolated-test-password"),
        preferred_language="ru",
        country_code="AZ",
    )
    db_session.add(user)
    db_session.flush()
    headers = {"Authorization": "Bearer " + create_access_token(user.id)}
    ownership = {"start_date": "2026-01-01", "current_odometer_km": 0}
    compare = {"variant_ids": [variant.id, internal.id]}
    assert client.post(
        f"/api/v1/knowledge/vehicles/{internal.id}/save", json={}, headers=headers
    ).status_code == 404
    assert client.get(
        "/api/v1/knowledge/ownership/evidence", params={"variant_id": internal.id}
    ).status_code == 404
    assert client.post(
        "/api/v1/knowledge/ownership/compare",
        json={
            "scenario": ownership,
            "members": [
                {"variant_id": variant.id, "current_odometer_km": 0},
                {"variant_id": internal.id, "current_odometer_km": 0},
            ],
        },
    ).status_code == 404
    assert client.post(
        f"/api/v1/knowledge/vehicles/{internal.id}/ownership", json=ownership
    ).status_code == 404
    assert client.post(
        f"/api/v1/knowledge/vehicles/{internal.id}/ownership/save",
        json={"scenario": ownership, "expected_scenario_id": "0" * 64},
        headers=headers,
    ).status_code == 404
    assert client.post("/api/v1/knowledge/compare", json=compare).status_code == 404
    assert client.post(
        "/api/v1/knowledge/compare/save", json=compare, headers=headers
    ).status_code == 404


def test_fact_level_overlay_admits_core_without_leaking_research_fields(
    db_session, client, monkeypatch
):
    variant, catalog = candidate(db_session)
    monkeypatch.setattr(get_settings(), "environment", "production")
    assert buyer.active_us_rows(buyer.records(db_session)) == []

    for key in (
        "make",
        "model",
        "model_year",
        "original_market",
        "powertrain",
        "fuel",
        "engine_displacement",
        "engine_description",
        "transmission_description",
        "drivetrain",
    ):
        claim(db_session, variant, catalog, key)
    claim(db_session, variant, catalog, "transmission_family", status="INTERNAL_RESEARCH")
    db_session.flush()

    rows = buyer.active_us_rows(buyer.records(db_session))
    assert len(rows) == 1
    # Internal-candidate source state cannot override independent fact rights.
    db_session.get(SourceRegistry, "epa").state = "NEEDS_PERMISSION"
    db_session.get(SourceRegistry, "epa").paused = True
    db_session.flush()
    assert len(buyer.active_us_rows(buyer.records(db_session))) == 1
    projected = rows[0][1]
    assert projected["commercial_fact_overlay"] is True
    assert "seats" not in projected["facts"]
    assert "fuel_combined" not in projected["facts"]
    assert "transmission_family" not in projected["facts"]
    candidate_card = _candidate(rows[0][0], projected)
    assert candidate_card["engine_displacement"] == "2.5"
    assert candidate_card["powertrain"] == "ICE"
    assert candidate_card["transmission_family"] is None
    assert candidate_card["cylinders"] is None
    assert projected["generation"] is None
    assert "EPA" not in repr(projected)

    response = client.get(f"/api/v1/knowledge/vehicles/{variant.id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_url"] == FACTORY
    assert "EPA research configuration" not in repr(payload)
    assert "fueleconomy.gov" not in repr(payload)
    assert payload["facts"]["engine_displacement"]["reuse_status"] == "COMMERCIAL_OK"
    assert "fuel_combined" not in payload["facts"]
    assert "evidence_scope" not in repr(payload)
    assert "locator" not in repr(payload)
    assert payload["generation"] is None

    facets = client.get("/api/v1/knowledge/facets", params={"catalog_scope": "US_BASE_2000"})
    assert facets.status_code == 200
    assert facets.json()["counts"]["models"] == 1
    body = buyer.search(db_session, BuyerFilters(catalog_scope="US_BASE_2000", body=["SEDAN"]))
    assert body["matched_versions"] == 0
    exact_at = buyer.search(
        db_session, BuyerFilters(catalog_scope="US_BASE_2000", transmission="AT")
    )
    assert exact_at["matched_versions"] == 0
    broad = buyer.search(
        db_session,
        BuyerFilters(catalog_scope="US_BASE_2000", transmission="AUTOMATIC_UNSPECIFIED"),
    )
    assert broad["matched_versions"] == 0  # family itself has not cleared rights


def test_status_cannot_bypass_rights_or_exact_applicability(db_session, monkeypatch):
    variant, catalog = candidate(db_session)
    monkeypatch.setattr(get_settings(), "environment", "production")
    keys = (
        "make",
        "model",
        "model_year",
        "original_market",
        "powertrain",
        "fuel",
        "engine_displacement",
        "engine_description",
        "transmission_description",
        "drivetrain",
    )
    for key in keys:
        claim(db_session, variant, catalog, key)
    assert len(buyer.active_us_rows(buyer.records(db_session))) == 1
    item = claim(
        db_session,
        variant,
        catalog,
        "drivetrain",
        scope={
            "configuration_keys": {
                "engine_displacement": "2.5",
                "engine_description": "2.5 L I4",
                "transmission_description": "Automatic (S8)",
                "drivetrain": "AWD",
            }
        },
    )
    assert item.reuse_status == "COMMERCIAL_OK"
    assert buyer.active_us_rows(buyer.records(db_session)) == []

    # Reusing a mirrored PDF cannot be authorized by a status string alone.
    item.evidence_scope = {
        **item.evidence_scope,
        "configuration_keys": {
            "engine_displacement": "2.5",
            "engine_description": "2.5 L I4",
            "transmission_description": "Automatic (S8)",
            "drivetrain": "FWD",
        },
    }
    item.source_url = "https://www.auto-brochures.com/toyota/camry.pdf"
    db_session.flush()
    assert buyer.active_us_rows(buyer.records(db_session)) == []


def test_republication_of_same_fact_is_idempotent(db_session):
    variant, catalog = candidate(db_session)
    first = claim(db_session, variant, catalog, "make")
    second = claim(db_session, variant, catalog, "make")
    assert first.id == second.id


def test_source_change_updates_projection_version(db_session, monkeypatch):
    variant, catalog = candidate(db_session)
    monkeypatch.setattr(get_settings(), "environment", "production")
    for key in (
        "make",
        "model",
        "model_year",
        "original_market",
        "powertrain",
        "fuel",
        "engine_displacement",
        "engine_description",
        "transmission_description",
        "drivetrain",
    ):
        claim(db_session, variant, catalog, key)
    before = buyer.version(buyer.active_us_rows(buyer.records(db_session)))
    item = claim(db_session, variant, catalog, "drivetrain")
    item.source_url = "https://www.toyota.com/content/dam/toyota/brochures/2018/camry.pdf"
    db_session.flush()
    after = buyer.version(buyer.active_us_rows(buyer.records(db_session)))
    assert before != after

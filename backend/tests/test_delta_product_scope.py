"""Public USA MY2012+ defaults and production isolation for local QA data."""

from types import SimpleNamespace

from app.api.routes.knowledge import ConsumerBuyerFilters, ResolverInput
from app.core.config import get_settings
from app.providers.vin import DEMO_VIN
from app.services import catalog_buyer as buyer
from app.services import listing_intake as intake


def _auth(client):
    response = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"})
    assert response.status_code == 201
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_consumer_schema_defaults_keep_legacy_research_scopes_available():
    assert ConsumerBuyerFilters().catalog_scope == "US_BASE_2000"
    assert ConsumerBuyerFilters().year_min == 2012
    assert ResolverInput().catalog_scope == "US_BASE_2000"
    assert ConsumerBuyerFilters(catalog_scope="US_CONFIRMED_2000").catalog_scope == (
        "US_CONFIRMED_2000"
    )


def test_consumer_projection_keeps_historical_rows_internal(monkeypatch, db_session):
    rows = [
        (SimpleNamespace(id="old"), {"make": "BMW", "model": "3 Series", "model_year": 2000}),
        (SimpleNamespace(id="current"), {"make": "BMW", "model": "3 Series", "model_year": 2012}),
    ]
    monkeypatch.setattr(buyer, "records", lambda db, **kwargs: rows)
    monkeypatch.setattr(buyer, "active_us_rows", lambda values: values)
    visible = intake.production_visible_us_rows(db_session)
    assert [variant.id for variant, _ in visible] == ["current"]
    assert [variant.id for variant, _ in rows] == ["old", "current"]


def test_empty_consumer_calls_use_2012_base_defaults(client):
    facets = client.get("/api/v1/knowledge/facets")
    assert facets.status_code == 200
    search = client.post("/api/v1/knowledge/search", json={})
    assert search.status_code == 200
    assert search.json()["filters"]["catalog_scope"] == "US_BASE_2000"
    assert search.json()["filters"]["year_min"] == 2012
    old = client.post("/api/v1/knowledge/resolve", json={"year": 2000})
    assert old.status_code == 200
    assert old.json()["status"] == "NOT_IN_CATALOG"


def test_fluids_group_is_absent_without_reusable_facts_and_rows_expose_rights():
    catalog = {
        "make": "Toyota",
        "model": "Camry",
        "model_year": 2018,
        "original_market": "US",
        "source_url": "https://example.invalid/source",
        "facts": {},
    }
    plain = buyer.vehicle_profile(catalog, "ru")
    assert "fluids" not in {group["key"] for group in plain["technical"]}
    catalog["facts"]["engine_oil_viscosity"] = {
        "value": "0W-20",
        "status": "CONFIRMED",
        "reuse_status": "COMMERCIAL_OK",
    }
    fluid = next(
        group
        for group in buyer.vehicle_profile(catalog, "az")["technical"]
        if group["key"] == "fluids"
    )
    assert fluid["rows"][0]["reuse_status"] == "COMMERCIAL_OK"


def test_production_hides_local_vin_fixture_even_if_demo_flag_remains_true(client):
    headers = _auth(client)
    qa = client.get("/api/v1/meta/client-config").json()
    assert qa["qa_mode"] is True and qa["vin_demo"]["sample_vin"]
    precheck = client.post(
        "/api/v1/vin/precheck", headers=headers, json={"vin": DEMO_VIN, "language": "ru"}
    )
    assert precheck.status_code == 201
    check_id = precheck.json()["check_id"]

    settings = get_settings()
    original = settings.environment
    original_developer = settings.developer_mode
    settings.environment = "production"
    settings.developer_mode = True  # Runtime misconfiguration must still be inert.
    try:
        config = client.get("/api/v1/meta/client-config").json()
        assert config["qa_mode"] is False
        assert config["demo_mode"] is False
        assert config["vin_demo"] is None
        assert config["developer"]["enabled"] is False
        assert config["concept_products"] == {"active": False}
        assert client.post("/api/v1/auth/demo", json={}).status_code == 404
        assert client.get("/api/v1/vin/checks", headers=headers).json() == []
        assert client.get("/api/v1/vin/profiles", headers=headers).json() == []
        assert client.get(f"/api/v1/vin/{check_id}/precheck", headers=headers).status_code == 404
        assert client.get(f"/api/v1/vin/{check_id}", headers=headers).status_code == 404
        assert client.post(
            "/api/v1/vin/precheck", headers=headers, json={"vin": DEMO_VIN, "language": "ru"}
        ).status_code == 404
        assert client.post(
            f"/api/v1/vin/{check_id}/payments/mock", headers=headers, json={}
        ).status_code == 404
    finally:
        settings.environment = original
        settings.developer_mode = original_developer

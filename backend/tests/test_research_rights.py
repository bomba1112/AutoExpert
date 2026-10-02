"""Production must not publish legacy EPA research through alternate buyer APIs."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from app.core.config import get_settings
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.enums import ResearchJobStatus
from app.models.knowledge_ops import SourceRegistry
from app.models.research import ResearchJob
from app.models.vehicle_knowledge import VehicleKnowledgeProfile, VINCheck
from app.repositories.vehicles import VehicleNotResolvedError, VehicleRepository
from app.schemas.analysis import AnalysisCreate
from app.services.buyer_experience import persist_report
from app.services.knowledge_registry import seed_registry
from app.services.provider_registry import default_provider_registry
from app.services.research_rights import (
    permitted_research_registry,
    profile_uses_restricted_epa,
)
from test_commercial_fact_overlay import candidate, claim


def login(client):
    response = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"})
    assert response.status_code == 201
    payload = response.json()
    return {"Authorization": "Bearer " + payload["access_token"]}, payload["user"]["id"]


def test_production_rejects_stored_epa_job_and_dossier(db_session, client, monkeypatch):
    headers, user_id = login(client)
    db_session.add(
        SourceRegistry(
            id="epa",
            title="EPA",
            state="LOCAL_RESEARCH",
            paused=False,
            config={"commercial_reuse": False},
        )
    )
    profile = VehicleKnowledgeProfile(
        make="Toyota",
        model="Camry",
        generation="Unknown",
        market="USA",
        year=2019,
        freshness_at=datetime.now(UTC),
        dossier_seed={
            "provider_ids": ["epa_vehicle_configuration"],
            "knowledge_depth": {"epa_candidates": [{"id": "legacy-epa-row"}]},
        },
        is_demo=False,
    )
    job = ResearchJob(
        user_id=user_id,
        profile=profile,
        request_key="legacy-epa-job",
        status=ResearchJobStatus.COMPLETE,
        language="ru",
        requested_vehicle={"make": "Toyota", "model": "Camry", "year": 2019},
        provider_steps=[{"provider_id": "epa_vehicle_configuration", "records_count": 1}],
        completed_capabilities=["fuel_economy"],
        errors=[],
        resolution_snapshot={"selected_candidate_id": "epa:legacy-epa-row"},
        dossier_snapshot={"raw_epa_mpg": 34},
        metrics={},
        is_demo=False,
    )
    db_session.add(job)
    check = VINCheck(
        user_id=user_id,
        profile=profile,
        normalized_vin="4T1BF1FK5KU123456",
        language="ru",
        found=True,
        records_count=1,
        dossier_snapshot={"raw_epa_mpg": 34},
        source_snapshot=[
            {
                "source_type": "GOVERNMENT_FUEL_ECONOMY_DATA",
                "url": "https://www.fueleconomy.gov/ws/rest/vehicle/123",
            }
        ],
        is_demo=False,
    )
    db_session.add(check)
    db_session.flush()

    monkeypatch.setattr(get_settings(), "environment", "production")
    registry = permitted_research_registry(db_session, default_provider_registry())
    assert not any(p.definition.id.startswith("epa_") for p in registry.providers)
    assert client.get(f"/api/v1/research/jobs/{job.id}", headers=headers).status_code == 409
    assert (
        client.post(
            "/api/v1/reports/buyer/dossiers", json={"job_id": job.id}, headers=headers
        ).status_code
        == 409
    )
    assert client.get("/api/v1/vin/checks", headers=headers).json() == []
    assert client.get(f"/api/v1/vin/{check.id}", headers=headers).status_code == 409
    assert not profile_uses_restricted_epa(db_session, SimpleNamespace(dossier_seed={}, sources=[]))
    assert profile_uses_restricted_epa(
        db_session,
        SimpleNamespace(
            dossier_seed={},
            sources=[SimpleNamespace(source_type="GOVERNMENT_FUEL_ECONOMY_DATA", url="")],
        )
    )


def test_epa_csv_rights_do_not_clear_api_or_owner_logs(db_session, monkeypatch):
    monkeypatch.setattr(get_settings(), "environment", "production")
    db_session.add(
        SourceRegistry(
            id="epa",
            title="EPA CSV",
            state="APPROVED",
            paused=False,
            config={
                "commercial_reuse": True,
                "rights_url": "https://example.gov/csv-rights",
                "checked_at": "2026-09-28",
            },
        )
    )
    db_session.flush()
    registry = permitted_research_registry(db_session, default_provider_registry())
    assert not any(p.definition.id.startswith("epa_") for p in registry.providers)

    db_session.add(
        SourceRegistry(
            id="epa-vehicle-api",
            title="EPA vehicle API",
            state="APPROVED",
            paused=False,
            config={
                "commercial_reuse": True,
                "rights_url": "https://example.gov/api-rights",
                "checked_at": "2026-09-28",
            },
        )
    )
    db_session.flush()
    registry = permitted_research_registry(db_session, default_provider_registry())
    ids = {p.definition.id for p in registry.providers}
    assert "epa_vehicle_configuration" in ids
    assert "epa_my_mpg" not in ids
    assert profile_uses_restricted_epa(
        db_session,
        SimpleNamespace(
            dossier_seed={"provider_ids": ["epa_my_mpg"]},
            sources=[
                SimpleNamespace(
                    source_type="PUBLIC_OWNER_LOG",
                    url="https://www.fueleconomy.gov/ws/rest/ympg/shared/vehicles",
                )
            ],
        ),
    )


def test_registry_seeds_distinct_live_epa_rights_decisions(db_session):
    seed_registry(db_session)
    for source_id, provider_id in (
        ("epa-vehicle-api", "epa_vehicle_configuration"),
        ("epa-my-mpg", "epa_my_mpg"),
    ):
        source = db_session.get(SourceRegistry, source_id)
        assert source.state == "LOCAL_RESEARCH"
        assert source.config["commercial_reuse"] is False
        assert source.config["research_provider_ids"] == [provider_id]


def test_production_hides_stored_epa_buyer_report(db_session, client, monkeypatch):
    headers, user_id = login(client)
    report = persist_report(
        db_session,
        user_id,
        "ru",
        {"kind": "MODEL"},
        {lang: {"title": "Legacy EPA report", "subtitle": "34 mpg"} for lang in ("ru", "az", "en")},
        {
            "sources": [
                {
                    "source_type": "GOVERNMENT_FUEL_ECONOMY_DATA",
                    "url": "https://www.fueleconomy.gov/ws/rest/vehicle/123",
                }
            ],
            "official_consumption": 6.9,
        },
    )
    monkeypatch.setattr(get_settings(), "environment", "production")
    assert client.get("/api/v1/reports/buyer", headers=headers).json() == []
    assert client.get(f"/api/v1/reports/buyer/{report.id}", headers=headers).status_code == 409
    assert client.get(f"/api/v1/reports/buyer/{report.id}/pdf", headers=headers).status_code == 409
    assert client.get("/api/v1/reports", headers=headers).json() == []
    assert client.get(f"/api/v1/reports/{report.id}", headers=headers).status_code == 409


def test_production_hides_legacy_catalog_options_and_direct_id(db_session, client, monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_mode", False)
    make = VehicleMake(name="Toyota", normalized_name="toyota")
    model = VehicleModel(make=make, name="Camry", normalized_name="camry")
    generation = VehicleGeneration(model=model, name="Unknown", code="UNKNOWN")
    variant = VehicleVariant(
        generation=generation,
        market="US",
        name="EPA research variant",
        year_from=2019,
        year_to=2019,
        engine="2.5L",
        is_demo=False,
        specifications={"raw_epa_mpg": 34},
    )
    db_session.add(variant)
    db_session.flush()
    assert any(
        row["id"] == variant.id for row in client.get("/api/v1/catalog/options").json()["variants"]
    )

    monkeypatch.setattr(get_settings(), "environment", "production")
    assert client.get("/api/v1/catalog/options").json()["variants"] == []
    request = AnalysisCreate.model_validate(
        {
            "vehicle_variant_id": variant.id,
            "vehicle": {
                "country": "US",
                "make": "Toyota",
                "model": "Camry",
                "year": 2019,
                "currency": "USD",
            },
            "usage_profile": {"monthly_mileage_km": 1000, "city_share": 0.5},
        }
    )
    with pytest.raises(VehicleNotResolvedError, match="Legacy analysis"):
        VehicleRepository(db_session).resolve(request)


def test_safe_knowledge_projection_cannot_enter_raw_analysis_pipeline(
    db_session, client, monkeypatch
):
    headers, _ = login(client)
    variant, catalog = candidate(db_session)
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
    monkeypatch.setattr(get_settings(), "environment", "production")
    assert client.get(f"/api/v1/knowledge/vehicles/{variant.id}").status_code == 200
    response = client.post(
        "/api/v1/analyses/preview",
        headers=headers,
        json={
            "vehicle_variant_id": variant.id,
            "vehicle": {
                "country": "US",
                "make": "Toyota",
                "model": "Camry",
                "year": 2018,
                "currency": "USD",
            },
            "usage_profile": {"monthly_mileage_km": 1000, "city_share": 0.5},
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Legacy analysis is not available for publication"

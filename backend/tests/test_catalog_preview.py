# ruff: noqa: E501, F811
"""Preview publication of the 2021-2026 US configurations (owner decision 2026-10-03): shown in
the preview catalogue behind preview_us_configurations, never in production; the publisher
changes no existing variant, claim or technical_evidence row and is idempotent."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from app.core.config import get_settings
from app.models.catalog import VehicleVariant
from app.models.enums import EvidenceCategory
from app.models.evidence import SourceRecord, TechnicalEvidence
from app.models.knowledge_ops import SourceRegistry
from app.schemas.knowledge import ImportManifest
from app.services import catalog_buyer as buyer
from app.services import catalog_preview, us_tech_facts
from app.services.knowledge_import import enqueue, epa_record, process_job, publish_job, review_job
from app.services.listing_intake import production_visible_us_rows
from sqlalchemy import select
from test_published_knowledge import editorial  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("publish_us_config_preview", ROOT / "scripts" / "publish_us_config_preview.py")
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


@pytest.fixture(autouse=True)
def flags():
    settings = get_settings()
    original = settings.environment, settings.preview_us_configurations, settings.show_us_tech_facts
    catalog_preview.clear_cache()
    us_tech_facts.clear_cache()
    yield
    settings.environment, settings.preview_us_configurations, settings.show_us_tech_facts = original
    catalog_preview.clear_cache()
    us_tech_facts.clear_cache()


def publish_epa(db, actor, epa_id: str, year: str, trany: str = "Automatic (S8)") -> VehicleVariant:
    record = epa_record({"id": epa_id, "make": "Test make", "baseModel": "Test model", "model": "Test model", "year": year,
                         "fuelType1": "Regular Gasoline", "displ": "2.5", "trany": trany, "drive": "Front-Wheel Drive",
                         "VClass": "Midsize Cars"})
    job = enqueue(db, ImportManifest(source_id="epa", parser="manifest-json-v1", records=[record],
                                     selection_basis="Isolated preview publication test only"))
    process_job(db, job.id)
    review_job(db, job, actor, note="Reviewed isolated preview fixture", approve=True)
    publish_job(db, job, actor, note="Publish isolated preview fixture")
    return next(v for v in db.scalars(select(VehicleVariant)) if (v.specifications.get("catalog") or {}).get("external_key") == epa_id)


def configuration(db, variant: VehicleVariant, key: str, epa_ids: list[str], transmission: str = "Automatic (S8)") -> TechnicalEvidence:
    source = SourceRecord(title="EPA", publisher="EPA", url="https://fueleconomy.gov", source_type="EPA",
                          retrieved_at=variant.created_at, confidence="HIGH")
    db.add(source)
    db.flush()
    generation = variant.generation
    row = TechnicalEvidence(
        source_id=source.id, category=EvidenceCategory.OTHER, title="configuration", statement=key, status="CONFIRMED",
        confidence="HIGH", scope_level="CONFIGURATION", display_level="FACT", make_id=generation.model.make_id,
        generation_id=generation.id, year_from=variant.year_from, year_to=variant.year_from, configuration_key=key,
        fact_key="configuration", value=key, natural_key=f"cfg-{key}",
        conditions={"identity": {"powertrain": "ICE", "drivetrain": "FWD", "displacement_l": "2.5", "epa_transmission": transmission,
                                 "aspiration": "NATURALLY_ASPIRATED", "epa_ids": epa_ids, "research_layer_only": True}, "line": "Test model"})
    db.add(row)
    db.commit()
    return row


@pytest.fixture
def preview(db_session, editorial):
    _, actor = editorial
    db_session.add(SourceRegistry(id="epa", title="Isolated EPA source fixture", state="LOCAL_RESEARCH",
                                  config={"commercial_reuse": False, "cost_model": "FREE"}))
    db_session.commit()
    variant = publish_epa(db_session, actor, "777001", "2022")
    configuration(db_session, variant, "test-make-test-model-us-2022-2.5l-4cyl-ice-a-s8-fwd", ["777001"])
    return db_session, variant


def test_publisher_links_records_and_changes_nothing_existing(preview):
    db, variant = preview
    before = publisher.fingerprint(db)
    entries, summary = publisher.plan(db, (2021, 2026))
    assert summary["status"] == {"LINK": 1} and summary["pairs"] == 1
    result = publisher.apply(db, entries, (2021, 2026))
    assert result["added"] == 1 and result["stale_after"] == 0
    after = publisher.fingerprint(db)
    assert before["vehicle_variants"] == after["vehicle_variants"]
    assert before["commercial_fact_claims"] == after["commercial_fact_claims"]
    assert before["technical_evidence"] == after["technical_evidence"]
    assert publisher.apply(db, entries, (2021, 2026))["added"] == 0  # idempotent


def test_preview_rows_only_outside_production(preview, client):
    db, variant = preview
    entries, _ = publisher.plan(db, (2021, 2026))
    publisher.apply(db, entries, (2021, 2026))
    production_before = [v.id for v, _ in production_visible_us_rows(db)]
    settings = get_settings()

    settings.environment, settings.preview_us_configurations = "development", None
    rows = catalog_preview.preview_rows(db)
    assert [v.id for v, _ in rows] == [variant.id] and rows[0][1]["preview_only"]
    assert client.get("/api/v1/meta/client-config").json()["us_configurations_preview"]["enabled"] is True
    card = client.get(f"/api/v1/knowledge/vehicles/{variant.id}").json()
    assert card["preview"] is True and card["us_configuration_key"].endswith("-fwd")
    found = client.post("/api/v1/knowledge/search", json={}).json()
    assert any(item["id"] == variant.id and item.get("preview") for item in found["matches"])
    assert us_tech_facts.configuration_for_variant(db, variant.id) == "test-make-test-model-us-2022-2.5l-4cyl-ice-a-s8-fwd"
    assert [v.id for v, _ in production_visible_us_rows(db)] == production_before  # production rows unchanged

    settings.preview_us_configurations = False
    catalog_preview.clear_cache()
    assert catalog_preview.preview_rows(db) == []
    assert client.get(f"/api/v1/knowledge/vehicles/{variant.id}").status_code == 404

    settings.environment, settings.preview_us_configurations = "production", True  # hard guard
    catalog_preview.clear_cache()
    assert catalog_preview.enabled() is False and catalog_preview.preview_rows(db) == []
    assert "us_configurations_preview" not in client.get("/api/v1/meta/client-config").json()


def test_stale_and_shared_variants_are_held(preview, editorial):
    db, variant = preview
    _, actor = editorial
    shared = publish_epa(db, actor, "777002", "2023")
    configuration(db, shared, "test-make-test-model-us-2023-2.5l-4cyl-ice-a-s8-fwd", ["777002"])
    configuration(db, shared, "test-make-test-model-us-2023-2.5l-4cyl-ice-a-s8-fwd-twin", ["777002"])
    entries, summary = publisher.plan(db, (2021, 2026))
    assert summary["status"] == {"LINK": 1, "SHARED_VARIANT": 2}
    publisher.apply(db, entries, (2021, 2026))
    # a variant republished after the preview record was made is left out until the record is refreshed
    variant.published_revision_id = "republished"
    db.commit()
    catalog_preview.clear_cache()
    assert catalog_preview.preview_rows(db) == []


def test_variant_with_several_configurations_takes_the_matching_gearbox(db_session, editorial):
    _, actor = editorial
    db_session.add(SourceRegistry(id="epa", title="Isolated EPA source fixture", state="LOCAL_RESEARCH",
                                  config={"commercial_reuse": False, "cost_model": "FREE"}))
    db_session.commit()
    variant = publish_epa(db_session, actor, "777003", "2022", trany="Automatic (AV-S1)")
    catalog = variant.specifications["catalog"]
    variant.specifications = {"catalog": {**catalog, "facts": {**catalog["facts"], "transmission_family": {"value": "CVT", "status": "CONFIRMED"}}}}
    db_session.commit()
    dct = configuration(db_session, variant, "elantra-like-2.0l-turbo-ice-a-am-s8-fwd", ["1"], transmission="Automatic (AM-S8)")
    cvt = configuration(db_session, variant, "elantra-like-2.0l-ice-a-av-s1-fwd", ["2"], transmission="Automatic (AV-S1)")
    for row in (dct, cvt):
        row.vehicle_variant_id = variant.id
    db_session.commit()
    assert us_tech_facts.configuration_for_variant(db_session, variant.id) == "elantra-like-2.0l-ice-a-av-s1-fwd"
    assert buyer.records(db_session, production_safe=False, variant_ids=set())  == []


def test_web_preview_marks_preview_rows(client):
    views = client.get("/preview/catalog-views.js").text
    assert "v.preview?" in views and "current.preview?" in views  # badge; save and compare hidden for preview rows
    copy = client.get("/preview/catalog-copy.js").text
    assert "previewBadge" in copy and "previewNote" in copy

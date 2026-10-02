"""Synthetic fixtures stay in isolated test databases; no external calls."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.models.catalog import VehicleVariant
from app.models.evidence import MarketListing, TechnicalEvidence
from app.models.knowledge_ops import CatalogRevision, SourceRegistry
from app.models.user import User
from app.schemas.knowledge import BuyerFilters, CatalogRecord, CostScenario, ImportManifest
from app.services.catalog_buyer import (
    answer_catalog_question,
    costs,
    coverage,
    normalized,
    records,
    resolve,
    save_dossier,
    search,
)
from app.services.knowledge_import import (
    document_text,
    enqueue,
    epa_record,
    private_path,
    process_job,
    publish_job,
    review_job,
    store_document,
)
from app.services.knowledge_registry import seed_registry
from sqlalchemy import func, select


def record(key="one", model="Test model", **kwargs):
    facts = {
        "engine_displacement": {"value": "1.6", "unit": "L", "locator": "table 1"},
        "powertrain": {"value": "ICE", "locator": "table 1"},
        "fuel": {"value": "GASOLINE", "locator": "table 1"},
        "fuel_combined": {"value": "6.25", "unit": "L/100km", "locator": "table 2"},
        "transmission_family": {"value": "AUTOMATIC_UNSPECIFIED", "locator": "table 1"},
        "drivetrain": {"value": "FWD", "locator": "table 1"},
    }
    return CatalogRecord(
        external_key=key,
        make="Test make",
        model=model,
        configuration="Test version",
        original_market="US",
        model_year=2020,
        facts=facts,
        source_url="https://example.test/official",
        **kwargs,
    )


@pytest.fixture
def editorial(db_session, tmp_path, monkeypatch):
    # Synthetic make belongs only to this isolated fixture's scope, never production policy.
    from app.services import catalog_buyer
    from app.services.catalog_scope import scope_policy

    rules = scope_policy()
    monkeypatch.setattr(
        catalog_buyer, "scope_policy",
        lambda: {**rules, "primary_makes": [*rules["primary_makes"], "Test make"]},
    )
    monkeypatch.setattr(get_settings(), "knowledge_data_dir", str(tmp_path))
    source = SourceRegistry(
        id="test-source",
        title="Isolated test source",
        state="APPROVED",
        config={"commercial_reuse": True, "cost_model": "FREE"},
    )
    user = User(
        email="operator@example.test",
        password_hash=hash_password("test-only-password"),
        preferred_language="ru",
        country_code="AZ",
        is_admin=True,
    )
    db_session.add_all([source, user])
    db_session.commit()
    return source, user


def staged(db, rows, dry_run=False):
    manifest = ImportManifest(
        source_id="test-source",
        parser="manifest-json-v1",
        records=rows,
        selection_basis="Isolated test fixtures only",
        dry_run=dry_run,
    )
    job = enqueue(db, manifest)
    while job.state in {"QUEUED", "RUNNING"}:
        job = process_job(db, job.id, batch_size=1)
    return job, manifest


def published(db, user, rows=None):
    job, _ = staged(db, rows or [record()])
    review_job(db, job, user, note="Reviewed isolated test source", approve=True)
    publish_job(db, job, user, note="Publish isolated test only")
    return list(
        db.scalars(select(VehicleVariant).where(VehicleVariant.published_revision_id.is_not(None)))
    )


def synthetic_consumer_rows(monkeypatch):
    # These calculation tests use an isolated editorial make outside the
    # commercial buyer scope. Rights isolation is tested separately.
    from app.api.routes import knowledge as routes

    monkeypatch.setattr(routes, "production_visible_us_rows", records)


def test_import_resume_idempotency_and_publication_gate(db_session, editorial):
    source, user = editorial
    manifest = ImportManifest(
        source_id=source.id,
        parser="manifest-json-v1",
        records=[record(), record("two", "Second model")],
        selection_basis="Isolated idempotency test",
    )
    job = enqueue(db_session, manifest)
    assert enqueue(db_session, manifest).id == job.id
    process_job(db_session, job.id, batch_size=1)
    assert job.cursor == 1 and job.state == "QUEUED"
    assert records(db_session) == []
    process_job(db_session, job.id, batch_size=1)
    assert job.state == "STAGED" and job.cursor == 2
    with pytest.raises(ValueError, match="REVIEW_REQUIRED"):
        publish_job(db_session, job, user, note="No review yet")
    review_job(db_session, job, user, note="Explicit test review", approve=True)
    assert publish_job(db_session, job, user, note="Test publication") == 2
    assert coverage(db_session)["models"] == 2
    assert coverage(db_session)["verified_generations"] == 0
    assert db_session.scalar(select(func.count()).select_from(CatalogRevision)) == 2


def test_dry_run_never_publishes(db_session, editorial):
    _, user = editorial
    job, _ = staged(db_session, [record()], dry_run=True)
    assert job.state == "DRY_RUN"
    with pytest.raises(ValueError, match="CLEAN_STAGING_REQUIRED"):
        review_job(db_session, job, user, note="Cannot publish dry run", approve=True)
    assert not records(db_session)


def test_cancellation_stops_before_records(db_session, editorial):
    manifest = ImportManifest(
        source_id="test-source",
        parser="manifest-json-v1",
        records=[record()],
        selection_basis="Cancellation test fixture",
    )
    job = enqueue(db_session, manifest)
    job.cancel_requested = True
    db_session.commit()
    process_job(db_session, job.id)
    assert job.state == "CANCELLED" and job.cursor == 0


def test_lease_prevents_double_work(db_session, editorial):
    job = enqueue(
        db_session,
        ImportManifest(
            source_id="test-source",
            parser="manifest-json-v1",
            records=[record()],
            selection_basis="Lease test fixture",
        ),
    )
    job.lease_until = datetime.now(UTC) + timedelta(minutes=1)
    job.state = "RUNNING"
    db_session.commit()
    process_job(db_session, job.id)
    assert job.cursor == 0


def test_quarantine_blocks_publication(db_session, editorial):
    _, user = editorial
    doc = store_document(db_session, "test-source", b'[{"make":"bad"}]')
    db_session.commit()
    job = enqueue(
        db_session,
        ImportManifest(
            source_id="test-source",
            parser="manifest-json-v1",
            document_id=doc.id,
            selection_basis="Malformed test import",
        ),
    )
    process_job(db_session, job.id)
    assert job.metrics["quarantined"] == 1
    with pytest.raises(ValueError):
        review_job(db_session, job, user, note="Blocked malformed input", approve=True)


def test_raw_document_checksum_and_dedup(db_session, editorial):
    doc = store_document(db_session, "test-source", b"[]")
    db_session.commit()
    assert store_document(db_session, "test-source", b"[]").id == doc.id
    private_path(doc.storage_key).write_bytes(b"[{}]")
    job = enqueue(
        db_session,
        ImportManifest(
            source_id="test-source",
            parser="manifest-json-v1",
            document_id=doc.id,
            selection_basis="Tampered document fixture",
        ),
    )
    process_job(db_session, job.id)
    assert job.state == "FAILED" and job.errors[-1]["code"] == "RAW_DOCUMENT_CHANGED"


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/private",
        "https://example.com",
        "file:///secret",
        "https://user:pass@www.fueleconomy.gov/feg/epadata/vehicles.csv.zip",
    ],
)
def test_acquisition_allowlist_blocks_arbitrary_urls(db_session, editorial, url):
    with pytest.raises(ValueError, match="DOWNLOAD_URL_NOT_ALLOWLISTED"):
        enqueue(
            db_session,
            ImportManifest(
                source_id="test-source",
                parser="epa-csv-v1",
                download_url=url,
                selection_basis="SSRF regression test",
            ),
        )


def test_zip_bomb_and_extra_files_rejected():
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as z:
        z.writestr("data.csv", "x" * 1000000)
    with pytest.raises(ValueError, match="EXPANSION"):
        document_text(out.getvalue())
    out = BytesIO()
    with ZipFile(out, "w") as z:
        z.writestr("file.csv", "a,b")
        z.writestr("../script.exe", "unsafe")
    with pytest.raises(ValueError, match="SINGLE_CSV"):
        document_text(out.getvalue())


def test_editorial_lock_rolls_back_whole_batch(db_session, editorial):
    source, user = editorial
    original = published(db_session, user)[0]
    revision_id = original.published_revision_id
    original.editorial_locked = True
    db_session.commit()
    job, _ = staged(
        db_session,
        [record("two", "New model"), record().model_copy(update={"revision_note": "Changed"})],
    )
    review_job(db_session, job, user, note="Test explicit revision", approve=True)
    with pytest.raises(ValueError, match="EDITORIAL_OVERRIDE_PROTECTED"):
        publish_job(db_session, job, user, note="Atomic publish check")
    assert len(records(db_session)) == 1
    assert db_session.get(VehicleVariant, original.id).published_revision_id == revision_id


def test_production_rights_gate_and_pause(db_session, editorial, monkeypatch):
    source, user = editorial
    published(db_session, user)
    source.config = {**source.config, "commercial_reuse": False}
    source.state = "LOCAL_RESEARCH"
    db_session.commit()
    assert len(records(db_session)) == 1
    monkeypatch.setattr(get_settings(), "environment", "production")
    assert records(db_session) == []
    monkeypatch.setattr(get_settings(), "environment", "test")
    source.paused = True
    db_session.commit()
    assert len(records(db_session)) == 1
    with pytest.raises(ValueError, match="SOURCE_PAUSED"):
        enqueue(
            db_session,
            ImportManifest(
                source_id=source.id,
                parser="manifest-json-v1",
                records=[record()],
                selection_basis="Paused source test",
            ),
        )


def test_budget_and_at_unknown_are_separate_not_matches(db_session, editorial):
    _, user = editorial
    published(db_session, user)
    r = search(db_session, BuyerFilters(budget_max_minor=2000000, transmission="AT"))
    assert r["matches"] == [] and r["uncertain_models"] == 1
    assert set(r["needs_confirmation"][0]["missing"]) == {"budget", "transmission_construction"}
    assert not r["constraints_relaxed"]


def test_budget_uses_fresh_exact_variant_asking_price(db_session, editorial):
    _, user = editorial
    v = published(db_session, user)[0]
    row = MarketListing(
        vehicle_variant_id=v.id,
        source_id=v.specification_source_id,
        external_key="test-listing",
        country="AZ",
        make="Test make",
        model="Test model",
        year=2020,
        price=Decimal("19999.99"),
        currency="AZN",
        url="https://example.test/listing",
        observed_at=datetime.now(UTC),
        is_demo=False,
    )
    db_session.add(row)
    db_session.commit()
    r = search(db_session, BuyerFilters(budget_max_minor=2000000))
    assert (
        r["matched_models"] == 1 and r["matches"][0]["asking_prices"][0]["price_minor"] == 1999999
    )
    row.observed_at = datetime.now(UTC) - timedelta(days=31)
    db_session.commit()
    assert search(db_session, BuyerFilters(budget_max_minor=2000000))["uncertain_models"] == 1


def test_no_implicit_nat_aspiration_or_unknown_any_collapse(db_session, editorial):
    _, user = editorial
    published(db_session, user)
    r = search(db_session, BuyerFilters(engine="GASOLINE_NA"))
    assert r["matched_models"] == 0 and "aspiration" in r["needs_confirmation"][0]["missing"]
    r = search(db_session, BuyerFilters(market_preference="UNKNOWN"))
    assert "MARKET_NOT_CHOSEN" in r["matches"][0]["tradeoffs"]
    r = search(db_session, BuyerFilters(market_preference="ANY"))
    assert "MARKET_NOT_CHOSEN" not in r["matches"][0]["tradeoffs"]


def test_reviewed_market_import_drives_exact_budget_without_duplicate_or_silent_conflict(
    db_session, editorial
):
    from app.schemas.knowledge import MarketObservationInput

    source, user = editorial
    row = record()
    row.market_observations = [
        MarketObservationInput(
            source_id=source.id,
            external_key="listing-1",
            price="19999.99",
            observed_at=datetime.now(UTC) - timedelta(hours=1),
            source_url="https://example.test/licensed-listing",
            locator="signed export row 1",
            identity_basis="Exact market, year, engine and drivetrain checked by editor",
        )
    ]
    job, _ = staged(db_session, [row])
    assert db_session.scalar(select(func.count()).select_from(MarketListing)) == 0
    review_job(
        db_session, job, user, note="Verified source and listing applicability", approve=True
    )
    publish_job(db_session, job, user, note="Publish reviewed exact-version observation")
    result = search(db_session, BuyerFilters(budget_max_minor=2000000))
    assert result["matched_versions"] == 1
    assert result["matches"][0]["asking_prices"][0]["price_minor"] == 1999999
    revised = row.model_copy(deep=True)
    revised.revision_note = "Metadata-only review repeat"
    published(db_session, user, [revised])
    assert db_session.scalar(select(func.count()).select_from(MarketListing)) == 1
    conflicting = row.model_copy(deep=True)
    conflicting.market_observations[0].price = Decimal("18000.00")
    conflict_job, _ = staged(db_session, [conflicting])
    review_job(db_session, conflict_job, user, note="Test conflicting asking price", approve=True)
    with pytest.raises(ValueError, match="MARKET_OBSERVATION_CONFLICT"):
        publish_job(db_session, conflict_job, user, note="Never overwrite dated observation")
    changed_identity = row.model_copy(deep=True)
    changed_identity.market_observations = []
    changed_identity.facts["engine_displacement"].value = "2.0"
    published(db_session, user, [changed_identity])
    assert search(db_session, BuyerFilters(budget_max_minor=2000000))["matched_versions"] == 0


def test_new_comparison_supports_three_versions_and_az_ru_text(
    client, db_session, editorial, monkeypatch
):
    synthetic_consumer_rows(monkeypatch)
    _, user = editorial
    variants = published(
        db_session, user, [record(), record("two", "Second"), record("three", "Third")]
    )
    ids = [v.id for v in variants]
    for lang in ("az", "ru"):
        r = client.post("/api/v1/knowledge/compare", json={"variant_ids": ids, "language": lang})
        assert r.status_code == 200 and len(r.json()["members"]) == 3
        assert (
            "\u0420\u00b0" not in r.json()["verdict"] and "\u0419\u2122" not in r.json()["verdict"]
        )
    assert (
        client.post("/api/v1/knowledge/compare", json={"variant_ids": ids + ids[:1]}).status_code
        == 422
    )


def test_resolver_exact_conflict_unknown_and_unsupported(db_session, editorial):
    _, user = editorial
    published(db_session, user)
    q = {"make": "Test make", "model": "Test model", "year": 2020}
    assert resolve(db_session, q)["status"] == "EXACT"
    assert resolve(db_session, {**q, "engine": "2.0"})["status"] == "CONTRADICTION"
    assert resolve(db_session, {**q, "trim": "Limited"})["status"] == "MULTIPLE"
    assert resolve(db_session, {**q, "market": "KR"})["status"] == "UNSUPPORTED"
    assert resolve(db_session, {**q, "model": "Not present"})["status"] == "NOT_IN_CATALOG"


def test_transition_year_retains_multiple_variants(db_session, editorial):
    _, user = editorial
    published(
        db_session,
        user,
        [
            record(generation="Old", generation_code="A"),
            record("two", generation="New", generation_code="B"),
        ],
    )
    assert (
        resolve(db_session, {"make": "Test make", "model": "Test model", "year": 2020})["status"]
        == "MULTIPLE"
    )
    # Labels preserve two candidates but cannot certify their documentary identity.
    assert coverage(db_session)["verified_generations"] == 0


def test_az_search_normalization():
    assert normalized("İSTANBUL / ƏLI") == normalized("istanbul əlı")


def test_money_decimal_no_double_count_and_unknown_resale():
    c = record().model_dump(mode="json")
    s = CostScenario(
        monthly_km=1000,
        months=24,
        purchase_price="20000",
        resale_price="17000",
        fuel_price="1.10",
        maintenance="600",
        repair_reserve="400",
        other_costs="200",
        price_date=date(2026, 9, 18),
        price_source="User scenario",
    )
    r = costs(c, s)
    assert r["purchase_separate"] == "20000.00"
    assert r["components"]["energy"] == "1650.00"
    assert r["total"] == "5850.00"
    assert costs(c, s.model_copy(update={"resale_price": None}))["total"] is None
    assert costs(c, CostScenario())["known_subtotal"] is None


def test_phev_needs_mode_share_and_bev_never_uses_gasoline():
    c = record().model_dump(mode="json")
    c["facts"]["powertrain"]["value"] = "PHEV"
    assert costs(c, CostScenario(fuel_price="1.1"))["components"]["energy"] is None
    c["facts"]["powertrain"]["value"] = "BEV"
    assert costs(c, CostScenario(fuel_price="1.1"))["components"]["energy"] is None


def test_epa_parser_does_not_invent_generation_body_na_or_at():
    r = epa_record(
        {
            "id": "999",
            "make": "Test",
            "model": "Car",
            "year": "2020",
            "fuelType1": "Regular Gasoline",
            "trany": "Automatic (AV-S6)",
            "VClass": "Compact Cars",
            "comb08": "30",
            "displ": "1.8",
            "atvType": "Hybrid",
        }
    )
    assert r.generation is None
    assert "body" not in r.facts and "aspiration" not in r.facts and "gears" not in r.facts
    assert r.facts["transmission_family"].value == "VARIABLE_UNSPECIFIED"
    assert r.facts["powertrain"].value == "HEV"
    assert r.facts["fuel_combined"].value == "7.84"


def test_existing_report_save_snapshot_bilingual_and_grounded_chat(db_session, editorial):
    _, user = editorial
    v = published(db_session, user)[0]
    c = v.specifications["catalog"]
    report = save_dossier(db_session, user, v, c, "az", {})
    assert report.input_snapshot["vin"] is None and not report.is_demo
    ru = report.generated_sections["translations"]["ru"]
    az = report.generated_sections["translations"]["az"]
    assert ru["generated_at"] == az["generated_at"]
    assert ru["sections"][0]["key"] == "conclusion"
    text, evidence = answer_catalog_question(report, "Что при 2000 км в месяц?", "ru")
    assert "125.0 L" in text and evidence["source_ids"] and evidence["evidence_ids"]
    source_id = c["facts"]["fuel_combined"]["source_id"]
    assert evidence["source_ids"] == [source_id]
    assert db_session.scalar(select(func.count()).select_from(TechnicalEvidence)) == 6


def test_admin_routes_require_actual_admin_and_registration_cannot_claim_role(
    client, db_session, editorial, monkeypatch
):
    monkeypatch.setattr(get_settings(), "admin_email", "admin@example.com")
    source, user = editorial
    assert client.get("/api/v1/knowledge/admin").status_code == 401
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": get_settings().admin_email,
            "password": "Test-password-56789",
            "preferred_language": "ru",
            "country_code": "AZ",
        },
    )
    assert r.status_code == 201 and not r.json()["user"]["is_admin"]
    h = {"Authorization": "Bearer " + r.json()["access_token"]}
    assert client.get("/api/v1/knowledge/admin", headers=h).status_code == 403
    admin = {"Authorization": "Bearer " + create_access_token(user.id, is_admin=True)}
    assert client.get("/api/v1/knowledge/admin", headers=admin).status_code == 200


def test_public_browse_and_protected_document_and_assets(client, db_session, editorial):
    _, user = editorial
    published(db_session, user)
    # Editorial test publications outside the consumer scope stay available to
    # direct review services but cannot enter the rights-cleared browse API.
    assert client.get("/api/v1/knowledge/facets").json()["counts"]["models"] == 0
    assert client.post("/api/v1/knowledge/search", json={}).status_code == 200
    assert (
        client.post("/api/v1/knowledge/admin/documents/test-source", content=b"[]").status_code
        == 401
    )
    assert client.get("/api/v1/knowledge/assets/not-an-id/original").status_code == 422
    assert client.get("/api/v1/knowledge/assets/not-an-id/card").status_code == 404


def test_registry_does_not_grant_commercial_rights(db_session):
    seed_registry(db_session)
    epa = db_session.get(SourceRegistry, "epa")
    assert epa.state == "LOCAL_RESEARCH" and not epa.config["commercial_reuse"]
    assert db_session.get(SourceRegistry, "jp-mlit").state == "SEARCH_SUSPENDED"
    epa.paused = True
    db_session.commit()
    seed_registry(db_session)
    assert epa.paused


@pytest.mark.parametrize(
    "kwargs",
    [
        {"year_min": 2025, "year_max": 2020},
        {"budget_min_minor": 200, "budget_max_minor": 100},
        {"market_preference": "SELECTED", "markets": []},
        {"priorities": ["cost"] * 4},
    ],
)
def test_filter_constraints_rejected_not_cleared(kwargs):
    with pytest.raises(ValueError):
        BuyerFilters(**kwargs)


def auth(user):
    return {"Authorization": "Bearer " + create_access_token(user.id, is_admin=user.is_admin)}


def test_resolver_decimal_and_estimate_are_not_confirmed(db_session, editorial):
    _, user = editorial
    v = published(db_session, user)[0]
    assert (
        resolve(db_session, {"make": "Test make", "model": "Test model", "engine": "1.60"})[
            "status"
        ]
        == "EXACT"
    )
    from app.services.catalog_buyer import fact_display, fact_value

    fact = {"value": "6.25", "status": "ESTIMATE", "labels": {"az": "6,25"}}
    assert fact_value({"facts": {"x": fact}}, "x") is None
    assert "Təxmini" in fact_display(fact, "az")
    assert v.published_revision_id


def test_editorial_correction_is_staged_with_visible_diff(client, db_session, editorial):
    _, user = editorial
    v = published(db_session, user)[0]
    url = f"/api/v1/knowledge/admin/variants/{v.id}"
    result = client.get(url, headers=auth(user)).json()
    corrected = result["record"]
    corrected["facts"]["engine_displacement"]["value"] = "2.0"
    corrected["revision_note"] = "Documented correction for isolated test"
    draft = client.post(url + "/draft", headers=auth(user), json=corrected)
    assert draft.status_code == 200
    assert draft.json()["state"] == "STAGED" and not draft.json()["published"]
    assert v.published_revision_id == result["revision_id"]
    detail = client.get(
        "/api/v1/knowledge/admin/imports/" + draft.json()["job_id"], headers=auth(user)
    ).json()
    change = detail["revisions"][0]["changes"]["facts"]["engine_displacement"]
    assert change["before"]["value"] == "1.6" and change["after"]["value"] == "2.0"


@pytest.mark.parametrize("atv", ["FCV", "eFCV"])
def test_hydrogen_epa_rows_are_not_combustion_engines(atv):
    r = epa_record(
        {
            "id": "999",
            "make": "Test",
            "model": "Fuel cell",
            "year": "2020",
            "fuelType1": "Hydrogen",
            "atvType": atv,
        }
    )
    assert r.facts["powertrain"].value == "FCEV"


@pytest.mark.parametrize("engine", ["MHEV", "EREV", "FCEV"])
def test_additional_powertrain_filters_are_not_gasoline_aliases(db_session, editorial, engine):
    _, user = editorial
    a, b = record(), record("alternative", "Alternative")
    b.facts["powertrain"].value = engine
    published(db_session, user, [a, b])
    result = search(db_session, BuyerFilters(engine=engine))
    assert result["matched_versions"] == 1
    assert result["matches"][0]["model"] == "Alternative"


def test_rollback_restores_active_evidence_keeps_saved_snapshot(client, db_session, editorial):
    from app.providers.database import DatabaseTechnicalDataProvider

    _, user = editorial
    v = published(db_session, user)[0]
    old_revision = v.published_revision_id
    saved = save_dossier(db_session, user, v, v.specifications["catalog"], "ru", {})
    saved_json = saved.generated_sections.copy()
    updated = record()
    updated.facts["engine_displacement"].value = "2.0"
    published(db_session, user, [updated])
    assert v.published_revision_id != old_revision
    rows = DatabaseTechnicalDataProvider(db_session).evidence_for(v.id, "US")
    assert len(rows) == 6
    assert all(r.conditions["revision_id"] == v.published_revision_id for r in rows)
    result = client.post(
        f"/api/v1/knowledge/admin/variants/{v.id}/review",
        headers=auth(user),
        json={"action": "rollback", "note": "Revert an isolated factual edit"},
    )
    assert result.status_code == 200
    assert v.published_revision_id == old_revision
    assert v.specifications["catalog"]["facts"]["engine_displacement"]["value"] == "1.6"
    assert saved.generated_sections == saved_json


def test_saved_comparison_uses_existing_report_with_decimal_scenarios(
    client, db_session, editorial, monkeypatch
):
    from app.models.analysis import Report

    synthetic_consumer_rows(monkeypatch)
    _, user = editorial
    variants = published(db_session, user, [record(), record("two", "Second")])
    payload = {
        "variant_ids": [v.id for v in variants],
        "language": "az",
        "scenarios": [
            {
                "fuel_price": "1.10",
                "price_date": "2026-09-18",
                "price_source": "Isolated user scenario",
            }
        ]
        * 2,
    }
    assert client.post("/api/v1/knowledge/compare/save", json=payload).status_code == 401
    response = client.post("/api/v1/knowledge/compare/save", json=payload, headers=auth(user))
    assert response.status_code == 200, response.text
    report = db_session.get(Report, response.json()["id"])
    assert report.user_id == user.id and report.input_snapshot["kind"] == "COMPARISON"
    assert report.generated_sections["translations"]["az"]["sections"][0]["key"] == "expert_verdict"
    assert report.evidence_bundle["ownership_costs"][0]["components"]["energy"] == "1650.00"
    assert report.evidence_bundle["ownership_costs"][0]["total"] is None


def test_editorial_claim_requires_applicable_evidence_and_exposes_public_sources(
    client, db_session, editorial
):
    from app.models.evidence import TechnicalEvidence
    from sqlalchemy import select

    _, user = editorial
    versions = published(
        db_session, user, [record(), record("second", "Second"), record("other", "Other")]
    )
    own = db_session.scalar(
        select(TechnicalEvidence).where(TechnicalEvidence.vehicle_variant_id == versions[0].id)
    )
    other = db_session.scalar(
        select(TechnicalEvidence).where(TechnicalEvidence.vehicle_variant_id == versions[2].id)
    )
    payload = {
        "slug": "isolated-article",
        "variant_ids": [versions[0].id, versions[1].id],
        "translations": {
            lang: {"title": "Isolated article", "limitations": "Source scope applies"}
            for lang in ("ru", "az")
        },
        "claims": [{"evidence_ids": [other.id]}],
    }
    endpoint = "/api/v1/knowledge/admin/publications"
    assert client.post(endpoint, headers=auth(user), json=payload).status_code == 422
    payload["claims"] = [{"evidence_ids": [own.id]}]
    draft = client.post(endpoint, headers=auth(user), json=payload)
    assert draft.status_code == 200, draft.text
    assert client.get("/api/v1/knowledge/publications").json() == []
    pid = draft.json()["id"]
    reviewed = client.post(
        endpoint + f"/{pid}/review",
        headers=auth(user),
        json={"action": "publish", "note": "Reviewed source and both translations"},
    )
    assert reviewed.status_code == 200
    from app.models.knowledge_ops import EditorialPublication

    assert db_session.get(EditorialPublication, pid).state == "PUBLISHED"
    # Legacy editorial prose has not passed fact-level commercial review.
    assert client.get("/api/v1/knowledge/publications?language=az").json() == []
    assert client.put(f"/api/v1/knowledge/favorites/{pid}").status_code == 401
    assert client.put(f"/api/v1/knowledge/favorites/{pid}", headers=auth(user)).status_code == 200
    assert pid in client.get("/api/v1/knowledge/favorites", headers=auth(user)).json()


def test_asset_qa_rights_applicability_and_private_original(client, db_session, editorial):
    import json

    from app.models.knowledge_ops import VehicleAsset
    from PIL import Image

    _, user = editorial
    r = record(generation="G1", facelift="pre")
    r.facts["body"] = r.facts["fuel"].model_copy(update={"value": "SEDAN"})
    v = published(db_session, user, [r])[0]
    image = BytesIO()
    Image.new("RGB", (600, 400), "white").save(image, "PNG")
    meta = {
        "variant_ids": [v.id],
        "make": "Test make",
        "model": "Test model",
        "source_url": "https://example.test/image",
        "rights_reference": "Isolated test image rights",
        "commercial_reuse": True,
        "generation": "G1",
        "facelift": "pre",
        "body": "SEDAN",
        "market": "US",
        "year_from": 2020,
        "year_to": 2020,
        "generated": True,
    }
    upload = client.post(
        "/api/v1/knowledge/admin/assets",
        params={"metadata": json.dumps(meta)},
        content=image.getvalue(),
        headers=auth(user),
    )
    assert upload.status_code == 200, upload.text
    asset_id = upload.json()["id"]
    assert upload.json()["state"] == "IMAGE_QA"
    assert client.get(f"/api/v1/knowledge/assets/{asset_id}/card").status_code == 404
    assert client.get(f"/api/v1/knowledge/admin/assets/{asset_id}/preview").status_code == 401
    preview = client.get(f"/api/v1/knowledge/admin/assets/{asset_id}/preview", headers=auth(user))
    assert preview.status_code == 200 and preview.headers["cache-control"] == "private, no-store"
    asset = db_session.get(VehicleAsset, asset_id)
    asset.applicability = {**asset.applicability, "facelift": "wrong"}
    db_session.commit()
    url = f"/api/v1/knowledge/admin/assets/{asset_id}/review"
    decision = {"action": "approve", "note": "Manual image applicability review"}
    assert client.post(url, headers=auth(user), json=decision).status_code == 409
    asset.applicability = {**asset.applicability, "facelift": "pre"}
    db_session.commit()
    assert client.post(url, headers=auth(user), json=decision).status_code == 200
    assert client.get(f"/api/v1/knowledge/assets/{asset_id}/card").status_code == 200
    assert client.get(f"/api/v1/knowledge/assets/{asset_id}/original").status_code == 422
    asset.rights = {**asset.rights, "commercial_reuse": False}
    db_session.commit()
    assert client.get(f"/api/v1/knowledge/assets/{asset_id}/card").status_code == 404


def test_research_off_queue_cancel_owner_and_sync_bypass(
    client, db_session, editorial, monkeypatch
):
    from app.models.enums import ResearchJobStatus
    from app.schemas.research import ResearchJobCreate
    from app.services.catalog_research import enqueue_research, work_research

    _, user = editorial
    request = ResearchJobCreate(vehicle={"make": "Test", "model": "Car", "year": 2020})
    monkeypatch.setattr(get_settings(), "knowledge_worker_enabled", False)
    with pytest.raises(ValueError, match="WORKER_NOT_CONFIGURED"):
        enqueue_research(db_session, user, request)
    monkeypatch.setattr(get_settings(), "knowledge_worker_enabled", True)
    job = enqueue_research(db_session, user, request)
    assert enqueue_research(db_session, user, request).id == job.id
    assert job.status == ResearchJobStatus.QUEUED and job.worker_attempts == 0
    assert (
        client.post(f"/api/v1/research/jobs/{job.id}/execute", headers=auth(user)).status_code
        == 409
    )
    outsider = User(
        email="outsider@example.test",
        password_hash="test",
        preferred_language="ru",
        country_code="AZ",
    )
    db_session.add(outsider)
    db_session.commit()
    url = f"/api/v1/knowledge/research/{job.id}"
    assert client.get(url, headers=auth(outsider)).status_code == 404
    assert (
        client.post(
            url + "/control",
            headers=auth(outsider),
            json={"action": "cancel", "note": "Try to cancel someone else's job"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            url + "/control",
            headers=auth(user),
            json={"action": "cancel", "note": "Cancel this test research job"},
        ).status_code
        == 200
    )
    assert work_research(db_session, job.id).errors == ["CANCELLED"]


def test_research_policy_pause_rights_budget_and_failure(db_session, editorial, monkeypatch):
    from app.models.enums import ResearchJobStatus
    from app.providers.official_nhtsa import OfficialProviderUnavailable
    from app.schemas.research import ResearchJobCreate
    from app.services.catalog_research import (
        BudgetHTTP,
        enqueue_research,
        permitted_registry,
        work_research,
    )

    _, user = editorial
    seed_registry(db_session)
    http = BudgetHTTP()
    try:
        ids = {p.definition.id for p in permitted_registry(db_session, http).providers}
        assert "epa_vehicle_configuration" in ids and "manufacturer_owner_manual" not in ids
        db_session.get(SourceRegistry, "epa").paused = True
        db_session.get(SourceRegistry, "nhtsa").paused = True
        db_session.commit()
        assert not permitted_registry(db_session, http).providers
        http.used = 12
        with pytest.raises(OfficialProviderUnavailable, match="BUDGET_EXHAUSTED"):
            http._request("https://example.test/no-network")
        http.used = 0
        http.cancelled = lambda: True
        with pytest.raises(OfficialProviderUnavailable, match="CANCELLED"):
            http._request("https://example.test/no-network")
    finally:
        http.client.close()
    monkeypatch.setattr(get_settings(), "knowledge_worker_enabled", True)
    job = enqueue_research(
        db_session, user, ResearchJobCreate(vehicle={"make": "Test", "model": "Car", "year": 2020})
    )
    result = work_research(db_session, job.id)
    assert result.status == ResearchJobStatus.FAILED
    assert result.errors == ["NO_PERMITTED_RESEARCH_SOURCE"]
    assert result.worker_lease_until is None and result.metrics["network_calls"] == 0

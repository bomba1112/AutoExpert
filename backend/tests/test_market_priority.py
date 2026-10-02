# ruff: noqa: F811
"""Synthetic market fixtures; no Turbo data, credentials or external network."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from app.models.catalog import VehicleVariant
from app.models.knowledge_ops import MarketDiscoveryRevision
from app.schemas.knowledge import ImportManifest
from app.schemas.market_discovery import MarketDiscoveryRecord
from app.services.knowledge_import import (
    enqueue,
    process_job,
    publish_job,
    review_job,
    store_document,
)
from app.services.market_discovery import parse_csv, published
from app.services.market_priority import build_queue, distribution, normalize_market_claim, policy
from pydantic import ValidationError
from sqlalchemy import func, select
from test_published_knowledge import editorial  # noqa: F401


def record(**kwargs):
    data = dict(
        external_key="example-one",
        make="BMW",
        model="Example model",
        observed_at=datetime.now(UTC) - timedelta(hours=1),
        source_url="https://example.test/models/one",
        locator="Synthetic export rows 1-2",
        listing_count=2,
        count_method="COMPLETE_EXPORT",
        inventory_scope="ACTIVE_LOCAL",
        distribution_scope="COMPLETE",
        listings=[
            dict(
                listing_id="one",
                source_url="https://example.test/autos/one",
                active=True,
                market_raw="Amerika",
                model_year=2020,
            ),
            dict(
                listing_id="two",
                source_url="https://example.test/autos/two",
                active=True,
                market_raw="Rəsmi diler",
                model_year=2021,
            ),
        ],
        selection_method="Synthetic complete export",
        limitations={"az": "Test", "ru": "Тест"},
    )
    data.update(kwargs)
    return MarketDiscoveryRecord(**data)


def permission(source):
    source.config = {
        **source.config,
        "allowed_observation_hosts": ["example.test"],
        "market_discovery_permission": {
            "reference": "synthetic-test-only",
            "local_storage": True,
            "method": "PERMITTED_EXPORT",
        },
    }


def test_official_dealer_is_channel_and_countries_remain_separate():
    assert normalize_market_claim("Rəsmi diler") == {
        "market": "UNKNOWN",
        "region": "UNKNOWN",
        "channel": "OFFICIAL_DEALER",
    }
    assert normalize_market_claim("Almaniya")["market"] == "DE"
    assert normalize_market_claim("Almaniya")["region"] == "EU"
    assert normalize_market_claim("Koreya")["market"] == "KR"
    d = distribution(record().model_dump(mode="json"))
    assert d["markets"] == {"US": 1, "UNKNOWN": 1}
    assert d["sales_channels"]["OFFICIAL_DEALER"] == 1


def test_dedupe_order_only_sold_and_partial_sample_not_extrapolated():
    r = record().model_dump(mode="json")
    r["listings"] += [
        r["listings"][0],
        {**r["listings"][0], "listing_id": "sold", "active": False},
        {**r["listings"][0], "listing_id": "order", "order_only": True},
    ]
    r["listing_count"] = 10000
    r["distribution_scope"] = "SAMPLE"
    value = record(**r)
    rules = policy()
    rules.pop("primary_basis", None)
    q = build_queue([value.model_dump(mode="json")], [], rules, us_sources_available=True)
    row = q["PRIMARY_US_MARKET_QUEUE"][0]
    assert row["priority"]["local_prevalence"] == 2
    assert row["priority"]["score"] == "1.0000"
    assert row["us_listing_count_or_sample_lower_bound"] == 1
    assert row["verification_status"] == "SELLER_CLAIM_NOT_TECHNICALLY_VERIFIED"


def test_stale_discovery_and_unknown_counts_do_not_manufacture_secondary_presence():
    r = record(make="Other make", observed_at=datetime.now(UTC) - timedelta(days=9))
    rules = policy()
    rules.pop("primary_basis", None)
    q = build_queue([r.model_dump(mode="json")], [], rules, us_sources_available=True)
    assert not q.get("SECONDARY_US_MARKET_QUEUE")
    assert q["models"][0]["batch_status"] == "STALE_DISCOVERY_REFRESH_REQUIRED"


def test_owner_brand_instruction_does_not_require_turbo_counts():
    catalog = [
        {
            "make": "BMW",
            "model": "3 Series",
            "model_year": 2020,
            "original_market": "US",
            "source_url": "https://example.test/official",
            "source_registry_id": "epa",
        },
        {
            "make": "Random brand",
            "model": "Rare model",
            "model_year": 2020,
            "original_market": "US",
            "source_url": "https://example.test/official",
            "source_registry_id": "epa",
        },
    ]
    q = build_queue([], catalog, policy(), us_sources_available=True)
    assert len(q["PRIMARY_US_MARKET_QUEUE"]) == 1
    item = q["PRIMARY_US_MARKET_QUEUE"][0]
    assert item["make"] == "BMW" and item["listing_count"] is None
    assert item["priority"]["score"] is None and item["research_model_years"] == [2020]
    assert item["us_variant_present"] == "OFFICIAL_US_SOURCE_CONFIGURATION"
    assert not q.get("SECONDARY_US_MARKET_QUEUE") and q["discovery_records"] == 0
    assert not q.get("PRIMARY_OTHER_MARKET_QUEUE")
    assert not any(r["make"] == "Skoda" for r in q["models"])


def test_strict_market_schema_rejects_metadata_false_totals_and_conflicting_duplicates():
    with pytest.raises(ValidationError):
        record(account={"id": "forbidden"})
    with pytest.raises(ValidationError):
        record(listing_count=50)
    r = record().model_dump(mode="json")
    with pytest.raises(ValidationError):
        record(listings=r["listings"] + [dict(r["listings"][0], market_raw="Koreya")])
    with pytest.raises(ValueError, match="SCHEMA_DRIFT"):
        parse_csv("make,model,session\nBMW,Example,x")


def test_reviewed_market_publication_preserves_catalogue_and_resumes(db_session, editorial):
    source, user = editorial
    permission(source)
    db_session.commit()
    manifest = ImportManifest(
        source_id=source.id,
        parser="market-discovery-json-v1",
        market_records=[record()],
        selection_basis="Synthetic permitted market export",
    )
    before = db_session.scalar(select(func.count()).select_from(VehicleVariant))
    job = enqueue(db_session, manifest)
    assert enqueue(db_session, manifest).id == job.id
    process_job(db_session, job.id, batch_size=1)
    assert not published(db_session)
    review_job(db_session, job, user, approve=True, note="Synthetic review")
    publish_job(db_session, job, user, note="Synthetic discovery publication")
    assert len(published(db_session)) == 1
    assert db_session.scalar(select(func.count()).select_from(VehicleVariant)) == before
    assert db_session.scalar(select(func.count()).select_from(MarketDiscoveryRevision)) == 1
    assert "reviewer" not in published(db_session)[0]


def test_permission_revocation_blocks_import_and_discovery(db_session, editorial):
    source, _ = editorial
    with pytest.raises(ValueError, match="PERMISSION"):
        enqueue(
            db_session,
            ImportManifest(
                source_id=source.id,
                parser="market-discovery-json-v1",
                market_records=[record()],
                selection_basis="Synthetic missing permission",
            ),
        )


def test_schema_drift_quarantines_raw_batch(db_session, editorial):
    source, _ = editorial
    permission(source)
    db_session.commit()
    doc = store_document(
        db_session,
        source.id,
        json.dumps(
            [{**record().model_dump(mode="json"), "session": "synthetic-forbidden"}]
        ).encode(),
    )
    job = enqueue(
        db_session,
        ImportManifest(
            source_id=source.id,
            parser="market-discovery-json-v1",
            document_id=doc.id,
            selection_basis="Synthetic schema drift",
        ),
    )
    process_job(db_session, job.id)
    assert job.state == "FAILED" and job.errors
    assert db_session.scalar(select(func.count()).select_from(MarketDiscoveryRevision)) == 0


def test_source_label_resolution_is_same_year_and_never_overwrites_family():
    from app.services.priority_source_identity import source_model

    catalog = [
        {
            "make": "BMW",
            "model": "3 Series",
            "model_year": 2025,
            "original_market": "US",
            "configuration": "330i Sedan",
            "external_key": "fixture-one",
        }
    ]
    models = [{"Make_Name": "BMW", "Model_Name": "330i"}, {"Make_Name": "BMW", "Model_Name": "330"}]
    result = source_model("BMW", "3 Series", 2025, models, catalog)
    assert result["model"] == "330i" and result["catalog_external_key"] == "fixture-one"
    assert source_model("BMW", "3 Series", 2024, models, catalog) is None
    assert catalog[0]["model"] == "3 Series"


def test_shared_official_archive_cache_checks_bytes_and_counts_requests(tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.providers.official_nhtsa import OfficialProviderUnavailable
    from app.services.catalog_research import BudgetHTTP
    from app.services.priority_research_http import PriorityHTTP

    monkeypatch.setattr(get_settings(), "knowledge_data_dir", str(tmp_path))

    def synthetic(self, url, headers=None):
        self.used += 1
        return b"fixture only", 1

    monkeypatch.setattr(BudgetHTTP, "_request", synthetic)
    url = "https://static.nhtsa.gov/odi/ffdd/tsbs/fixture.zip"
    a, b = PriorityHTTP(), PriorityHTTP()
    try:
        assert a.get_bytes(url) == (b"fixture only", 1)
        assert b.get_bytes(url) == (b"fixture only", 0)
        assert a.used == 1 and b.used == 0 and b.cache_hits == 1
        next((tmp_path / "priority-official-cache").glob("*.bin")).write_bytes(b"tampered")
        with pytest.raises(OfficialProviderUnavailable, match="CHECKSUM"):
            b.get_bytes(url)
    finally:
        a.client.close()
        b.client.close()

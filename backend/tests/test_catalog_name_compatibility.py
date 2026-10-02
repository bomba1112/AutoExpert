"""Regression: published spaced names and compact research names share identities."""

from datetime import UTC, datetime

import pytest
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.enums import ConfidenceLevel, ResearchJobStatus
from app.models.evidence import SourceRecord
from app.schemas.research import ResearchJobCreate, VehicleResearchRequest
from app.services.catalog_names import existing_name
from app.services.catalog_research import retry_failed_research
from app.services.provider_registry import ProviderRegistry
from app.services.research_pipeline import ResearchPipeline
from sqlalchemy import func, select


@pytest.mark.parametrize("stored_key", ["mercedes benz", "mercedesbenz"])
def test_research_reuses_published_canonical_names(db_session, stored_key):
    make = VehicleMake(name="Mercedes-Benz", normalized_name=stored_key)
    db_session.add(make)
    db_session.flush()
    model = VehicleModel(make_id=make.id, name="E-Class", normalized_name="e class")
    source = SourceRecord(
        title="Isolated source",
        publisher="Fixture",
        url="https://example.test/source",
        source_type="OFFICIAL",
        retrieved_at=datetime.now(UTC),
        confidence=ConfidenceLevel.HIGH,
    )
    db_session.add_all([model, source])
    db_session.flush()
    resolution = {
        "make": "MERCEDES-BENZ",
        "model": "E-Class",
        "engine_candidates": [],
        "engine_code_candidates": [],
        "transmission_candidates": [],
        "drivetrain_candidates": [],
        "unresolved_fields": ["engine", "transmission"],
    }
    result = ResearchPipeline(db_session, ProviderRegistry([]))._catalog_variant(
        VehicleResearchRequest(make="Mercedes-Benz", model="E-Class", year=2026),
        resolution,
        {},
        source,
    )
    assert result.generation.model_id == model.id
    assert result.engine is None and result.transmission is None
    assert make.normalized_name == stored_key
    assert db_session.scalar(select(func.count()).select_from(VehicleMake)) == 1
    assert db_session.scalar(select(func.count()).select_from(VehicleModel)) == 1


def test_name_ambiguity_requires_review(db_session):
    db_session.add_all(
        [
            VehicleMake(name="Test-Make", normalized_name="test-make"),
            VehicleMake(name="Test Make", normalized_name="test make"),
        ]
    )
    db_session.flush()
    with pytest.raises(ValueError, match="AMBIGUOUS_CATALOG_NAME"):
        existing_name(db_session, "TESTMAKE")
    assert existing_name(db_session, "Test-Make").name == "Test-Make"


def test_duplicate_model_name_prefers_sole_published_canonical_without_moving_legacy_rows(
    db_session,
):
    make = VehicleMake(name="Hyundai", normalized_name="hyundai")
    db_session.add(make)
    db_session.flush()
    canonical = VehicleModel(make_id=make.id, name="Santa Fe", normalized_name="santa fe")
    legacy = VehicleModel(make_id=make.id, name="Santa Fe", normalized_name="santafe")
    db_session.add_all([canonical, legacy])
    db_session.flush()
    live_generation = VehicleGeneration(model_id=canonical.id, name="NC", code="NC")
    old_generation = VehicleGeneration(model_id=legacy.id, name="unverified", code="UNRESOLVED")
    db_session.add_all([live_generation, old_generation])
    db_session.flush()
    db_session.add_all(
        [
            VehicleVariant(
                generation_id=live_generation.id,
                market="US",
                name="reviewed",
                specifications={},
                published_revision_id="reviewed-revision",
            ),
            VehicleVariant(
                generation_id=old_generation.id,
                market="US",
                name="legacy",
                specifications={},
            ),
        ]
    )
    db_session.flush()
    assert existing_name(db_session, "Santa Fe", make_id=make.id).id == canonical.id
    assert db_session.get(VehicleModel, legacy.id) is legacy

    # A second independently published candidate restores the review guard.
    db_session.add(
        VehicleVariant(
            generation_id=old_generation.id,
            market="US",
            name="other-reviewed",
            specifications={},
            published_revision_id="other-reviewed-revision",
        )
    )
    db_session.flush()
    with pytest.raises(ValueError, match="AMBIGUOUS_CATALOG_NAME"):
        existing_name(db_session, "Santa Fe", make_id=make.id)


def test_failed_retry_preserves_history_and_respects_budget(db_session):
    from app.models.user import User

    actor = User(email="retry@example.test", password_hash="test", country_code="AZ")
    db_session.add(actor)
    db_session.flush()
    job = ResearchPipeline(db_session, ProviderRegistry([])).create_job(
        user_id=actor.id,
        value=ResearchJobCreate(vehicle={"make": "Test", "model": "Car", "year": 2020}),
    )
    job.worker_queue = "CATALOG_REVIEW"
    job.status = ResearchJobStatus.FAILED
    job.worker_attempts = 1
    job.errors = ["WORKER_FAILED"]
    job.metrics = {"network_calls": 4}
    assert retry_failed_research(db_session, job)
    assert job.status == ResearchJobStatus.QUEUED and job.worker_attempts == 1
    assert job.metrics["retry_history"][0]["errors"] == ["WORKER_FAILED"]
    assert not retry_failed_research(db_session, job)
    job.status = ResearchJobStatus.FAILED
    job.cancel_requested = True
    assert not retry_failed_research(db_session, job)
    job.cancel_requested = False
    job.worker_attempts = 2
    assert not retry_failed_research(db_session, job)

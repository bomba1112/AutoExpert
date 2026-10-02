"""Basic readiness and combination boundaries, using isolated synthetic source fixtures."""

# ruff: noqa: F811
import copy

import pytest
from app.schemas.knowledge import BuyerFilters
from app.services.catalog_buyer import records, resolve, search
from app.services.catalog_verification import base_catalog_counts, base_catalog_ready, dossier_full
from app.services.market_priority import base_catalog_batch, policy
from test_factory_verification import apply, proof  # noqa: F401
from test_published_knowledge import editorial  # noqa: F401


def basic(value):
    value = copy.deepcopy(value)
    value["generation_code"] = "SYNTHETIC-G1"
    ref = value["facts"]["engine_description"]["documentary_source"]
    value["facts"]["body"] = dict(
        value="SEDAN", locator="Synthetic body column", documentary_source=ref
    )
    value["facts"]["engine_displacement"] = dict(
        value=1.6, unit="L", locator="Synthetic engine column", documentary_source=ref
    )
    value["facts"]["powertrain"] = dict(
        value="ICE", locator="Synthetic powertrain column", documentary_source=ref
    )
    value["facts"]["fuel"] = dict(
        value="GASOLINE", locator="Synthetic fuel column", documentary_source=ref
    )
    return value


def test_basic_catalog_does_not_require_dossier_prices_or_images(db_session, proof):
    actor, base, value = proof
    apply(db_session, actor, basic(value))
    c = base.specifications["catalog"]
    assert base_catalog_ready(c)
    assert not dossier_full(c)
    count = base_catalog_counts([(base, c), (base, c)])
    assert count["models"] == count["generations"] == 1
    assert count["engine_transmission_combinations"] == 1


def test_ready_filter_and_resolver_respect_generation_and_combination(db_session, proof):
    actor, base, value = proof
    apply(db_session, actor, basic(value))
    query = dict(
        make="Test make",
        model="Test model",
        year=2020,
        market="US",
        engine="1.6",
        transmission="AT",
        drivetrain="FWD",
        generation="SYNTHETIC-G1",
        catalog_ready_only=True,
    )
    result = resolve(db_session, query)
    assert result["status"] == "EXACT"
    assert result["candidates"][0]["id"] == base.id
    wrong = resolve(db_session, {**query, "generation": "SYNTHETIC-G2"})
    assert wrong["status"] == "CONTRADICTION"
    assert "generation" in wrong["conflicts"]
    wrong = resolve(db_session, {**query, "transmission": "DCT"})
    assert wrong["status"] == "CONTRADICTION"
    found = search(
        db_session,
        BuyerFilters(
            makes=["Test make"],
            models=["Test model"],
            generations=["SYNTHETIC-G1"],
            catalog_ready_only=True,
            transmission="AT",
            body=["SEDAN"],
        ),
    )
    assert [x["id"] for x in found["matches"]] == [base.id]


def test_documented_exclusion_preserves_variant_but_removes_buyer_candidate(db_session, proof):
    actor, base, value = proof
    value = basic(value)
    value["identity_verification"] = None
    value["facts"]["catalog_applicability"] = dict(
        value="EXCLUDED",
        locator="Synthetic factory contradiction",
        documentary_source=value["facts"]["body"]["documentary_source"],
    )
    apply(db_session, actor, value)
    assert base.published_revision_id
    assert base.id not in {v.id for v, _ in records(db_session)}


def test_active_base_manifest_is_batch_scoped_and_no_longer_frozen_to_51():
    rules = policy()
    assert rules["work_mode"] == "BUILD_BASE_CATALOG"
    batch = base_catalog_batch()
    assert batch["families"]
    # A small current batch is valid; prove the pipeline itself has no eight-family cap.
    sample = copy.deepcopy(batch["families"][0])
    expanded = {"batch_id": "synthetic-many", "selection_status": "test", "families": []}
    for index in range(12):
        member = copy.deepcopy(sample)
        member["id"] = f"synthetic-{index}"
        expanded["families"].append(member)
    assert len(base_catalog_batch(rules, expanded)["families"]) == 12
    assert not batch["turbo_counts_required"]
    assert "ownership_cost" in batch["deferred_workstreams"]
    assert not {"images", "ownership_cost", "deep_dossier"} & set(batch["readiness_gates"])
    sample.update(make="Skoda", model="Octavia", market="EU")
    manifest = {"batch_id": "synthetic", "selection_status": "test", "families": [sample]}
    with pytest.raises(ValueError, match="OUTSIDE_OWNER_CATALOG_SCOPE"):
        base_catalog_batch(rules, manifest)
    sample.update(make="Toyota", market="EU")
    with pytest.raises(ValueError, match="OUTSIDE_ACTIVE_CATALOG_MARKETS"):
        base_catalog_batch(rules, manifest)
    sample.update(market="US", year_from=1999)
    with pytest.raises(ValueError, match="OUTSIDE_ACTIVE_CATALOG_YEARS"):
        base_catalog_batch(rules, manifest)
    assert len(rules["primary_makes"]) == 17
    assert "confirmed_seating" not in batch["readiness_gates"]

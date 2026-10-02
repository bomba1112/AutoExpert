"""Range gaps, queue discipline and legacy scope are correctness boundaries."""

# ruff: noqa: F811
import copy

import pytest
from app.schemas.catalog_verification import DocumentaryReference
from app.services.catalog_verification import identity_verified, range_verified
from app.services.market_priority import policy, verification_batch
from test_factory_verification import apply, proof  # noqa: F401
from test_published_knowledge import editorial  # noqa: F401


def range_value(value):
    result = copy.deepcopy(value)
    result["identity_verification"]["range_scope"] = {
        "family_scope_id": "fixture-us",
        "configuration_group": "Synthetic 1.6 / 6AT / FWD only",
        "model_year_from": 2019,
        "model_year_to": 2021,
        "exclusions": ["Other engines, markets and years"],
    }
    for refs in result["identity_verification"]["field_evidence"].values():
        ref = copy.deepcopy(refs[0])
        refs[:] = [{**ref, "model_year": y} for y in range(2019, 2022)]
    return result


def test_each_year_must_be_evidenced_for_each_identity_field(db_session, proof):
    actor, base, value = proof
    value = range_value(value)
    value["identity_verification"]["field_evidence"]["engine_description"].pop(1)
    old = base.published_revision_id
    with pytest.raises(ValueError, match="IDENTITY_RANGE_EVIDENCE_GAP"):
        apply(db_session, actor, value)
    assert base.published_revision_id == old


def test_documented_range_is_valid_but_does_not_expand_other_record_scope(db_session, proof):
    actor, base, value = proof
    value = range_value(value)
    apply(db_session, actor, value)
    assert identity_verified(base.specifications["catalog"])
    assert range_verified(base.specifications["catalog"])
    assert base.specifications["catalog"]["model_year"] == 2020


def test_record_outside_documented_range_cannot_publish(db_session, proof):
    actor, _, value = proof
    value = range_value(value)
    value["identity_verification"]["range_scope"].update(model_year_from=2017, model_year_to=2018)
    with pytest.raises(ValueError, match="RECORD_OUTSIDE_IDENTITY_RANGE"):
        apply(db_session, actor, value)


def test_reference_cannot_mix_single_year_and_range(proof):
    _, _, value = proof
    ref = value["identity_verification"]["field_evidence"]["market"][0]
    with pytest.raises(ValueError, match="ONE_DOCUMENT_YEAR_SCOPE_REQUIRED"):
        DocumentaryReference(**{**ref, "model_year_from": 2019, "model_year_to": 2021})


def test_local_prevalence_and_year_scope_outrank_source_convenience():
    rules = policy()
    import json

    from app.services.market_priority import POLICY_PATH

    manifest = json.loads(
        (POLICY_PATH.parents[2] / rules["active_verification_manifest"]).read_text()
    )
    cohort = {"cohort": [{"make": r["make"], "model": r["model"]} for r in manifest["families"]]}
    manifest["families"][0].update(local_relevance_tier=1, source_availability_rank=0)
    manifest["families"][1].update(local_relevance_tier=2, source_availability_rank=10000)
    manifest["families"][2].update(
        local_relevance_tier=1, local_generation_year_priority=2, source_availability_rank=10000
    )
    result = verification_batch(rules, manifest, cohort)
    assert [r["make"] for r in result["families"]] == ["Mercedes-Benz", "Kia", "Hyundai"]
    assert not result["turbo_counts_required"]
    assert result["bmw_330i_my2025_role"] == "PIPELINE_PROOF_ONLY"


def test_manifest_cannot_expand_random_families_or_force_non_us():
    import json

    from app.services.market_priority import POLICY_PATH

    rules = policy()
    manifest = json.loads(
        (POLICY_PATH.parents[2] / rules["active_verification_manifest"]).read_text()
    )
    cohort = {"cohort": [{"make": r["make"], "model": r["model"]} for r in manifest["families"]]}
    manifest["families"][0]["model"] = "Unresearched model"
    with pytest.raises(ValueError, match="OUTSIDE_FROZEN_OWNER_COHORT"):
        verification_batch(rules, manifest, cohort)
    manifest["families"][0]["model"] = "C-Class"
    manifest["families"][0]["market"] = "EU"
    with pytest.raises(ValueError, match="NON_US_REQUIRES_SEPARATE_MANIFEST"):
        verification_batch(rules, manifest, cohort)

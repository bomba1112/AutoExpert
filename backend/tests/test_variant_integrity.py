"""Stage 6.4: real Santa Fe regression plus explicit synthetic variant boundaries."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.providers.knowledge_public import _matches_identity
from app.schemas.research import ProviderResult, VehicleResearchRequest
from app.services.knowledge_coverage import applicability, synthesize_facts
from app.services.knowledge_depth import selected_epa
from app.services.paid_report import build_paid_report, paid_readiness
from app.services.provider_registry import default_provider_registry
from app.services.research_pipeline import ResearchPipeline
from app.services.vehicle_identity import (
    applicability_class,
    filter_results,
    identity_target,
    integrity_from_findings,
    narrative_scope,
    powertrain_type,
)

VIN = "KM8S5DA19NU054949"
CAPTURE = json.loads((Path(__file__).parent / "fixtures/stage6_4_identity.json").read_text())
IDENTITY = next(r for r in CAPTURE if r["capability"] == "vehicle_identity")["records"][0]
EPA = next(r for r in CAPTURE if r["capability"] == "fuel_economy")["records"]
REQUEST = VehicleResearchRequest(vin=VIN, make="Hyundai", model="Santa Fe", year=2022)
TARGET = identity_target(REQUEST, IDENTITY)


def atom(topic, subtopic, value, *, scope=None, exact=True, authority="B", source="vpic"):
    return dict(
        topic=topic,
        subtopic=subtopic,
        value=value,
        status="CONFIRMED",
        applicability=scope or {**TARGET, "vin": VIN},
        exact_vin=exact,
        authority=authority,
        source_ids=[source],
        evidence_ids=[source + subtopic],
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        ("HEV (Hybrid Electric Vehicle) - Level Unknown", "HEV"),
        ("PHEV (Plug-in Hybrid Electric Vehicle)", "PHEV"),
        ("Mild HEV (Hybrid Electric Vehicle)", "MHEV"),
        ("BEV (Battery Electric Vehicle)", "BEV"),
        ("Not Electrified", "ICE"),
        (None, "UNKNOWN"),
    ],
)
def test_explicit_powertrain_types_and_unknown(value, expected):
    assert (
        powertrain_type({"electrification_level": value, "fuel_type_primary": "Gasoline"})
        == expected
    )


def test_real_problem_vin_and_epa_trim_powertrain_isolation():
    assert IDENTITY["vin"] == VIN and powertrain_type(IDENTITY) == "HEV"
    assert IDENTITY["engine_hp"] == "177.2"
    matched = [r for r in EPA if _matches_identity(r, IDENTITY)]
    assert [r["id"] for r in matched] == ["43993"]
    assert matched[0]["trany"] == "Automatic (AM-S6)"
    # Original provider returned HEV, Blue HEV and PHEV: none was selected safely.
    result = ProviderResult.model_validate(
        next(r for r in CAPTURE if r["capability"] == "fuel_economy")
    )
    assert selected_epa(result, IDENTITY) is None
    assert selected_epa(result.model_copy(update={"records": matched}), IDENTITY)["id"] == "43993"


@pytest.mark.parametrize(
    "left,right",
    [("ICE", "HEV"), ("HEV", "ICE"), ("HEV", "PHEV"), ("PHEV", "HEV"), ("MHEV", "HEV")],
)
def test_same_model_engine_and_trim_cannot_merge_powertrains(left, right):
    target = {**TARGET, "powertrain_type": left}
    scope = {**TARGET, "powertrain_type": right}
    assert applicability(target, scope) == "MISMATCH"
    findings, _ = synthesize_facts(
        [atom("engine", "system_combined_power_hp", 999, scope=scope)], target
    )
    assert not findings


@pytest.mark.parametrize(
    "field,value",
    [
        ("drivetrain", "FWD"),
        ("displacement", 2.5),
        ("trim", "Blue"),
        ("fuel", "Diesel"),
        ("market", "JDM"),
        ("vin", "3FA6P0HD0KR114795"),
    ],
)
def test_incompatible_dimensions_rejected(field, value):
    assert applicability(TARGET, {**TARGET, field: value}) == "MISMATCH"


def test_unknown_hybrid_type_does_not_confirm_variant():
    target = {**TARGET, "powertrain_type": "UNKNOWN"}
    findings, _ = synthesize_facts(
        [atom("engine", "battery_capacity_kwh", 1.49, exact=False)], target
    )
    assert findings[0]["status"] == "ESTIMATE"


def test_separate_engine_and_system_power_and_provenance():
    findings, conflicts = synthesize_facts(
        [
            atom("engine", "engine_power_hp", 177.2),
            atom("engine", "system_combined_power_hp", 226, source="synthetic-OEM-spec"),
        ],
        TARGET,
    )
    gate = integrity_from_findings(TARGET, findings, conflicts)
    assert gate["fields"]["engine_power_hp"]["value"] == 177.2
    assert gate["fields"]["system_combined_power_hp"]["value"] == 226
    assert (
        gate["fields"]["engine_power_hp"]["source_ids"]
        != gate["fields"]["system_combined_power_hp"]["source_ids"]
    )
    assert not conflicts


def test_exact_vin_wins_model_wide_and_retains_conflict_without_false_source():
    broad = {k: TARGET[k] for k in ("make", "model", "year", "market")}
    findings, conflicts = synthesize_facts(
        [
            atom("engine", "engine_power_hp", 177.2),
            atom("engine", "engine_power_hp", 281, exact=False, scope=broad, source="model"),
        ],
        TARGET,
    )
    assert findings[0]["value"] == 177.2
    assert findings[0]["source_ids"] == ["vpic"]
    assert conflicts[0]["resolution"] == "EXACT_VIN_AUTHORITY"


def test_oem_exact_vin_precedes_decoder_and_preserves_conflict():
    findings, conflicts = synthesize_facts(
        [
            atom("transmission", "gears", 8),
            atom("transmission", "gears", 6, authority="OEM_VIN", source="synthetic-vin-build"),
        ],
        TARGET,
    )
    assert findings[0]["value"] == 6
    assert conflicts[0]["resolution"] == "OEM_VIN_AUTHORITY"


def test_decoder_vs_exact_configuration_conflict_blocks_ready():
    scope = {k: v for k, v in TARGET.items() if k != "vin"}
    findings, conflicts = synthesize_facts(
        [
            atom("transmission", "gears", 8),
            atom("transmission", "gears", 6, exact=False, scope=scope, source="epa"),
        ],
        TARGET,
    )
    assert findings[0]["value"] is None
    gate = integrity_from_findings(TARGET, findings, conflicts)
    assert gate["state"] == "VARIANT_CONFLICT"
    from test_paid_vehicle_report import sample_profile

    profile = sample_profile()
    profile.dossier_seed["knowledge_depth"]["contradictions"] = conflicts
    assert paid_readiness(profile).identity_state == "VARIANT_CONFLICT"
    assert not paid_readiness(profile).can_purchase


def test_mixed_hev_phev_recall_stays_model_wide_and_is_not_discarded():
    base = {k: TARGET[k] for k in ("make", "model", "year", "market")}
    scope = narrative_scope(
        "certain 2021-2022 Santa Fe, Santa Fe HEV, Elantra HEV and Santa Fe PHEV vehicles", base
    )
    assert "powertrain_type" not in scope
    assert applicability_class(scope) == "MODEL_YEAR"
    assert applicability(TARGET, scope) == "MATCH"


def test_filter_keeps_model_recall_but_rejects_other_engine_and_phev():
    result = ProviderResult(
        provider_id="nhtsa_recalls",
        capability="recalls",
        status="CONFIRMED",
        source_url="https://api.nhtsa.gov/recalls",
        retrieved_at=datetime.now(UTC),
        records=[
            {
                "campaign_number": "wrong-engine",
                "summary": "Santa Fe vehicles equipped with 2.5L turbocharged engines",
            },
            {"campaign_number": "wrong-hybrid", "summary": "Santa Fe PHEV vehicles"},
            {
                "campaign_number": "model-recall",
                "summary": "Santa Fe vehicles with rearview camera faults",
            },
        ],
    )
    results, rejected = filter_results([result], TARGET)
    assert [r["campaign_number"] for r in results[0].records] == ["model-recall"]
    assert len(rejected) == 2
    assert results[0].records[0]["applicability_class"] == "MODEL_YEAR"


def test_real_captured_hybrid_pipeline_suppresses_wrong_gear_and_labels_power(db_session):
    from app.services.variant_resolver import VehicleVariantResolver

    rows = [ProviderResult.model_validate(r) for r in CAPTURE]
    rows[1].records = [r for r in rows[1].records if _matches_identity(r, IDENTITY)]
    resolution = VehicleVariantResolver().resolve(REQUEST, [IDENTITY], [])
    profile, _, _ = ResearchPipeline(db_session, default_provider_registry())._persist_profile(
        request=REQUEST,
        request_key="test-vin",
        resolution=resolution,
        results=rows,
        plan=[{"status": "TEST_CAPTURE_REPLAY"}],
    )
    assert profile.transmission is None
    assert profile.dossier_seed["identity_integrity"]["state"] == "VARIANT_CONFLICT"
    assert all("applicability_class" in e.conditions for e in profile.evidence)
    check = SimpleNamespace(
        is_demo=False,
        profile=profile,
        language="ru",
        normalized_vin=VIN,
        full_history_payload={},
        dossier_snapshot={"sections": []},
        source_snapshot=[],
    )
    report = build_paid_report(check)
    all_rows = {r.key: r.value for s in report.sections for r in s.rows}
    assert "HEV" in all_rows["identity.powertrain_type"]
    assert all_rows["engine.engine_power_hp"] == "177.2"
    assert all_rows["engine.system_combined_power_hp"] == "Не подтверждено"
    assert "transmission.gears" not in all_rows
    assert not report.readiness.can_purchase
    assert "Точная модификация" in report.notice
    # Rerunning a VIN creates an independent profile revision without collision.
    profile2, _, _ = ResearchPipeline(db_session, default_provider_registry())._persist_profile(
        request=REQUEST,
        request_key="test-vin-revision",
        resolution=resolution,
        results=rows,
        plan=[{"status": "TEST_CAPTURE_REPLAY"}],
    )
    assert profile2.id != profile.id


def test_stale_profile_cannot_be_ready_even_with_other_data():
    from test_paid_vehicle_report import sample_profile

    profile = sample_profile()
    profile.dossier_seed.pop("identity_integrity")
    assert not paid_readiness(profile).checks["identity_integrity"]

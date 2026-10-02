"""The exception router must keep all EPA tuples nonpublished and group real blockers."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "route_us_catalog_exceptions", ROOT / "scripts/route_us_catalog_exceptions.py"
)
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)


def candidate(epa_id, model, year, drive="front-wheel drive", trany="automatic (s6)"):
    return {
        "epa_vehicle_id": epa_id,
        "make": "Kia",
        "model": model,
        "model_year": year,
        "epa_model": model,
        "normalized_powertrain": {"drive": drive, "trany": trany},
    }


def joined(epa_id, model, year, classification="CANDIDATE_NEW", reason="NEW"):
    return {
        "epa_vehicle_id": epa_id,
        "make": "Kia",
        "model": model,
        "model_year": year,
        "classification": classification,
        "reason": reason,
        "matched_variant_id": "published-1" if classification != "CANDIDATE_NEW" else None,
    }


def generation(model, year, epa_id, resolution, labels=None):
    return {
        "make": "Kia",
        "model": model,
        "observed_model_years": [year],
        "epa_vehicle_ids_by_year": {str(year): [epa_id]},
        "generation_resolution": resolution,
        "generation_candidates": [{"label": label} for label in labels or []],
    }


def vpic(model, year, status="VPIC_EXACT_BASE_MODEL"):
    return {
        "make": "Kia",
        "model": model,
        "model_year": year,
        "status": status,
        "epa_model_example": model,
        "vpic_response_url": f"https://vpic.nhtsa.dot.gov/example/{model}/{year}",
    }


def group(model, year, epa_id):
    return {
        "make": "Kia",
        "model": model,
        "model_year_start": year,
        "model_year_end": year,
        "normalized_powertrain_key": f"powertrain-{epa_id}",
        "epa_models": [model],
        "epa_vehicle_ids_by_year": {str(year): [epa_id]},
    }


def test_ordinary_generation_gap_routes_to_automation_and_real_conflicts_to_review():
    candidates = [
        candidate("101", "Rio", 2018),
        candidate("102", "Forte", 2019, drive="4-wheel or all-wheel drive"),
    ]
    joined_rows = [
        joined("101", "Rio", 2018),
        joined("102", "Forte", 2019, "POSSIBLE_ALIAS", "POSSIBLE_EXISTING_TUPLE"),
    ]
    generations = [
        generation("Rio", 2018, "101", "UNRESOLVED_GENERATION"),
        generation("Forte", 2019, "102", "AMBIGUOUS_GENERATION", ["BD", "YD"]),
    ]
    vpic_rows = [
        vpic("Rio", 2018),
        vpic("Forte", 2019, "VPIC_NAME_UNRESOLVED"),
    ]
    groups = [group("Rio", 2018, "101"), group("Forte", 2019, "102")]
    result = router.build_routes(
        candidates, joined_rows, generations, vpic_rows, groups,
        approved_makes=["Kia"], expected_models=2,
    )
    assert len(result["models"]) == 2
    assert len(result["manual_models"]) == 1
    assert result["new_model_year_pairs"] == 2
    by_model = {row["model"]: row for row in result["models"]}
    assert by_model["Rio"]["route"] == "AUTOMATED_SOURCE_RESEARCH"
    assert by_model["Rio"]["manual_exceptions"] == []
    assert by_model["Rio"]["automated_research"][0]["code"] == "GENERATION_UNMAPPED"
    forte = by_model["Forte"]
    assert forte["route"] == "MANUAL_EXCEPTION_REVIEW"
    assert {issue["code"] for issue in forte["manual_exceptions"]} == {
        "MODEL_ALIAS_REVIEW", "VPIC_MODEL_NAME_UNRESOLVED",
        "GENERATION_AMBIGUOUS", "DRIVETRAIN_SOURCE_AMBIGUOUS",
    }
    assert forte["publication_eligible"] is False
    assert forte["manual_exceptions"][0]["epa_vehicle_ids"] == ["102"]
    group_routes = {row["model"]: row for row in result["powertrain_routes"]}
    assert group_routes["Rio"]["years"][0]["route"] == "AUTOMATED_BULK_CANDIDATE"
    assert group_routes["Forte"]["years"][0]["route"] == "MANUAL_EXCEPTION_REVIEW"
    assert all(row["publication_eligible"] is False for row in result["powertrain_routes"])


def test_identity_conflict_is_never_mistaken_for_ordinary_bulk_candidate():
    result = router.build_routes(
        [candidate("201", "Sportage", 2020)],
        [joined("201", "Sportage", 2020, "CONFLICT", "DRIVETRAIN")],
        [generation("Sportage", 2020, "201", "UNRESOLVED_GENERATION")],
        [vpic("Sportage", 2020)],
        [group("Sportage", 2020, "201")],
        approved_makes=["Kia"], expected_models=1,
    )
    assert result["models"][0]["manual_exceptions"][0]["code"] == (
        "CATALOG_IDENTITY_CONFLICT"
    )


def test_missing_powertrain_group_or_model_year_crosscheck_fails_closed():
    args = (
        [candidate("301", "Soul", 2021)],
        [joined("301", "Soul", 2021)],
        [generation("Soul", 2021, "301", "UNRESOLVED_GENERATION")],
        [vpic("Soul", 2021)],
    )
    with pytest.raises(ValueError, match="POWERTRAIN_GROUP_EPA_ID_COVERAGE_MISMATCH"):
        router.build_routes(*args, [], approved_makes=["Kia"], expected_models=1)
    with pytest.raises(ValueError, match="VPIC_MODEL_YEAR_COVERAGE_MISMATCH"):
        router.build_routes(
            args[0], args[1], args[2], [], [group("Soul", 2021, "301")],
            approved_makes=["Kia"], expected_models=1,
        )


def test_source_transmission_labels_do_not_claim_factory_gearbox_family():
    assert router.transmission_source_status("Automatic (S8)") == "EPA_AUTOMATIC_CODE"
    assert router.transmission_source_status("Automatic (AM-S7)") == "EPA_AUTOMATIC_CODE"
    assert router.transmission_source_status("Automatic (variable gear ratios)") == (
        "EPA_VARIABLE_RATIO_LABEL"
    )
    assert router.transmission_source_status("mystery unit") == "UNMAPPED"
    assert router.drivetrain_source_status("4-wheel or all-wheel drive") == "AMBIGUOUS"

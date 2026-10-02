"""No AI assertion becomes evidence or fills an absent factory field."""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from compare_ai_catalog_drafts import compare, observations  # noqa: E402


def draft(**changes):
    values = dict(
        make="Toyota",
        model="Prius",
        market="US",
        model_years=[2013],
        generation="XW30",
        body="HATCHBACK",
        displacement_l=1.8,
        powertrain="HEV",
        fuel_type="GASOLINE",
        aspiration="NATURALLY_ASPIRATED",
        transmission_type="ECVT",
        drivetrain="FWD",
        engine_oil_approval="unproven claim",
    )
    values.update(changes)
    return dict(
        id="synthetic",
        provenance="AI_DRAFT",
        publication_eligible=False,
        fields={
            k: {"value": v, "verification_status": "UNVERIFIED", "source": None}
            for k, v in values.items()
        },
    )


def source(**changes):
    value = dict(
        id="source-row",
        make="Toyota",
        model="Prius",
        market="US",
        model_year=2013,
        generation="XW30",
        facts=dict(
            body="HATCHBACK",
            engine_displacement=1.8,
            powertrain="HEV",
            fuel="GASOLINE",
            aspiration="NATURALLY_ASPIRATED",
            transmission_family="ECVT",
            drivetrain="FWD",
        ),
    )
    value["facts"].update(changes)
    return value


def test_matching_core_does_not_confirm_oil_or_modify_source():
    d, s = draft(), source()
    old = copy.deepcopy(s)
    result = compare([d], [s])["draft_annual_results"][0]
    assert result["status"] == "MATCHED_SOURCE_TUPLE"
    assert result["fields"]["engine_oil_approval"]["status"] == "INSUFFICIENT_DATA"
    assert not result["publication_from_draft"] and s == old


def test_bad_transmission_is_conflict_and_cannot_join():
    result = compare([draft(transmission_type="AT")], [source()])
    row = result["draft_annual_results"][0]
    assert row["status"] == "CONTRADICTION"
    assert row["fields"]["transmission_type"]["source_value"] == "ECVT"
    assert result["source_discovered_observation_ids"] == ["source-row"]


def test_missing_row_and_body_mismatch_do_not_prove_nonexistence():
    result = compare([draft(model_years=[2014]), draft(body="SEDAN", drivetrain="AWD")], [source()])
    assert all(x["status"] == "INSUFFICIENT_DATA" for x in result["draft_annual_results"])
    assert result["source_discovered_observation_ids"] == ["source-row"]


def test_ev_fields_remain_separate_and_unproven_battery_is_not_copied():
    d = draft(
        powertrain="BEV",
        displacement_l=None,
        fuel_type="ELECTRICITY",
        aspiration=None,
        transmission_type="SINGLE_SPEED",
        battery_capacity_kwh=75,
    )
    s = source(
        powertrain="BEV",
        engine_displacement=None,
        fuel="ELECTRICITY",
        aspiration=None,
        transmission_family="SINGLE_SPEED",
    )
    r = compare([d], [s])["draft_annual_results"][0]
    assert r["fields"]["battery_capacity_kwh"]["status"] == "INSUFFICIENT_DATA"
    assert r["fields"]["transmission_type"]["status"] == "CONFIRMED"


def test_draft_is_not_observation_and_cannot_self_approve():
    with pytest.raises(ValueError, match="INDEPENDENT_SOURCE"):
        observations({"provenance": "AI_DRAFT"})
    d = draft()
    d["fields"]["make"]["verification_status"] = "CONFIRMED"
    with pytest.raises(ValueError, match="SELF_VERIFY"):
        compare([d], [source()])


def test_manual_spelling_is_comparator_only_and_cvt_stays_distinct():
    d = draft(transmission_type="MT")
    before = copy.deepcopy(d)
    row = compare([d], [source(transmission_family="MANUAL")])["draft_annual_results"][0]
    assert row["fields"]["transmission_type"]["status"] == "CONFIRMED"
    assert row["fields"]["transmission_type"]["draft_value"] == "MT"
    assert d == before
    conflict = compare([d], [source(transmission_family="CVT")])["draft_annual_results"][0]
    assert conflict["status"] == "CONTRADICTION"


def small_manifest(clearance=127, raw_inches=5):
    return {
        "batch_id": "synthetic-reviewed",
        "documents": {"factory": {"url": "https://example.org/factory.pdf"}},
        "families": [
            {
                "id": "family",
                "make": "Toyota",
                "model": "Prius",
                "market": "US",
                "generation": "XW30",
                "annual_documents": {"2013": ["factory"]},
                "facts": {
                    "ground_clearance": {"value": clearance, "unit": "mm"},
                    "ground_clearance_in": {"value": raw_inches, "unit": "in"},
                },
                "groups": [
                    {
                        "id": "group",
                        "year_from": 2013,
                        "year_to": 2013,
                        "factory_combinations": [{"drivetrain": "FWD"}],
                        "facts": {"body": "HATCHBACK"},
                        "configuration": "scoped test tuple",
                        "locator": "independent factory annual table",
                    }
                ],
            }
        ],
    }


def test_last_manifest_wins_with_original_source_value_history():
    from compare_ai_catalog_drafts import merge_observations

    rows = merge_observations(
        [("first", small_manifest()), ("correction", small_manifest(152.4, 6))]
    )
    assert len(rows) == 1
    assert rows[0]["facts"]["ground_clearance"] == 152.4
    assert rows[0]["superseded_observations"][0]["facts"]["ground_clearance"] == 127
    assert rows[0]["manifest_path"] == "correction"
    field = rows[0]["field_observations"]["ground_clearance"]
    assert field["source_value"] == 6 and field["source_unit"] == "in"
    assert field["normalized_value"] == 152.4 and field["normalized_unit"] == "mm"


def test_recorded_normalization_does_not_leak_from_other_group():
    m = small_manifest()
    del m["families"][0]["facts"]["ground_clearance_in"]
    m["source_unit_normalizations"] = [
        {
            "family": "family",
            "group": "other",
            "field": "ground_clearance",
            "value": 127,
            "unit": "mm",
            "raw_value": 99,
            "raw_unit": "in",
            "conversion": "must not apply",
        }
    ]
    f = observations(m)[0]["field_observations"]["ground_clearance"]
    assert f["source_value"] is None and "conversion" not in f
    assert f["normalized_value"] == 127 and f["normalized_unit"] == "mm"
    m["source_unit_normalizations"][0].update(
        group="group", raw_value=5, conversion="1 in = 25.4 mm"
    )
    f = observations(m)[0]["field_observations"]["ground_clearance"]
    assert f["source_value"] == 5 and f["source_unit"] == "in"


def test_label_adjudication_is_exact_scoped_and_keeps_original_conflict():
    d, s = draft(body="LIFTBACK"), source()
    rule = dict(
        draft_id="synthetic",
        model_year=2013,
        field="body",
        draft_value="LIFTBACK",
        source_value="HATCHBACK",
        source_observation_ids=["source-row"],
        decision="ACCEPT_SCOPED_SOURCE_LABEL",
        references=[{"url": "https://example.org/factory.pdf"}],
        reason="Scoped factory body description; no global alias.",
    )
    result = compare([d], [s], [rule])["draft_annual_results"][0]
    assert result["status"] == "MATCHED_SOURCE_TUPLE_WITH_ADJUDICATION"
    assert result["fields"]["body"]["unadjudicated_status"] == "CONTRADICTION"
    assert not result["publication_from_draft"]
    other = {**s, "id": "other-row"}
    assert compare([d], [other], [rule])["draft_annual_results"][0]["status"] == "CONTRADICTION"
    conflict = compare([draft(body="LIFTBACK", transmission_type="AT")], [s], [rule])
    assert conflict["draft_annual_results"][0]["status"] == "CONTRADICTION"


def test_fuel_conversion_uses_recorded_mpg_not_reverse_calculation():
    m = small_manifest()
    facts = m["families"][0]["facts"]
    facts.update(
        fuel_combined={"value": 9.047, "unit": "L/100km"},
        epa_combined_mpg={"value": 26, "unit": "US mpg"},
    )
    f = observations(m)[0]["field_observations"]["fuel_combined"]
    assert f["source_value"] == 26 and f["source_unit"] == "US mpg"
    assert f["normalized_value"] == 9.047
    del facts["epa_combined_mpg"]
    f = observations(m)[0]["field_observations"]["fuel_combined"]
    assert f["source_value"] is None and f["source_unit"] is None
    assert f["normalized_value"] == 9.047


def test_correction_cannot_reuse_tuple_id_for_other_model():
    from compare_ai_catalog_drafts import merge_observations

    changed = small_manifest()
    changed["families"][0]["model"] = "Corolla"
    with pytest.raises(ValueError, match="CORRECTION_TUPLE_SCOPE_MISMATCH"):
        merge_observations([("first", small_manifest()), ("wrong-model", changed)])


def fact_correction():
    return {
        "source_id": "synthetic-reviewed",
        "parser": "manifest-json-v1",
        "selection_basis": "Synthetic source-backed same-key correction test",
        "records": [
            {
                "external_key": "family-group-FWD-2013",
                "make": "Toyota",
                "model": "Prius",
                "original_market": "US",
                "model_year": 2013,
                "configuration": "Synthetic corrected tuple, not a real vehicle assertion",
                "source_url": "https://example.org/factory.pdf",
                "facts": {
                    "drivetrain": {
                        "value": "4WD",
                        "status": "CONFIRMED",
                        "locator": "Synthetic scoped annual source table",
                        "documentary_source": {
                            "registry_id": "synthetic-reviewed",
                            "document_id": "synthetic-factory",
                            "sha256": "a" * 64,
                            "url": "https://example.org/factory.pdf",
                            "locator": "Synthetic scoped annual source table",
                            "make": "Toyota",
                            "model": "Prius",
                            "market": "US",
                            "model_year": 2013,
                        },
                    }
                },
            }
        ],
    }


def test_same_key_fact_correction_keeps_count_id_original_history_and_draft_conflict():
    from compare_ai_catalog_drafts import apply_fact_corrections, equal

    rows = observations(small_manifest())
    original = copy.deepcopy(rows)
    corrected, conflicts = apply_fact_corrections(rows, [("reviewed.json", fact_correction())])
    assert len(corrected) == len(rows) == 1 and rows == original
    assert corrected[0]["id"] == "family:group:FWD:2013"
    assert corrected[0]["facts"]["drivetrain"] == "4WD"
    assert corrected[0]["superseded_observations"][0]["facts"]["drivetrain"] == "FWD"
    old_context = corrected[0]["superseded_observations"][0]["field_observations"]["body"]
    assert old_context["applicability"]["drivetrain"] == "FWD"
    assert all(
        f["applicability"]["drivetrain"] == "4WD"
        for f in corrected[0]["field_observations"].values()
    )
    assert conflicts[0]["old_value"] == "FWD" and conflicts[0]["corrected_value"] == "4WD"
    assert not conflicts[0]["new_configuration"] and not equal("drivetrain", "AWD", "4WD")
    unchanged, repeated = apply_fact_corrections(corrected, [("reviewed.json", fact_correction())])
    assert unchanged == corrected and not repeated


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("new_key", "EXISTING_UNAMBIGUOUS_SOURCE_TUPLE_REQUIRED"),
        ("duplicate_key", "DUPLICATE_FACT_CORRECTION_KEY"),
        ("different_model", "FACT_CORRECTION_SCOPE_MISMATCH"),
        ("unconfirmed", "FACT_CORRECTION_REQUIRES_CONFIRMED_DOCUMENT"),
        ("wrong_year", "FACT_CORRECTION_DOCUMENT_SCOPE_MISMATCH"),
    ],
)
def test_same_key_fact_correction_rejects_unreviewed_or_unrelated_records(mutation, error):
    from compare_ai_catalog_drafts import apply_fact_corrections

    correction = fact_correction()
    record = correction["records"][0]
    if mutation == "new_key":
        record["external_key"] = "absent-source-key"
    elif mutation == "duplicate_key":
        correction["records"].append(copy.deepcopy(record))
    elif mutation == "different_model":
        record["model"] = "Corolla"
    elif mutation == "unconfirmed":
        record["facts"]["drivetrain"]["status"] = "ESTIMATE"
    elif mutation == "wrong_year":
        record["facts"]["drivetrain"]["documentary_source"]["model_year"] = 2014
    with pytest.raises(ValueError, match=error):
        apply_fact_corrections(observations(small_manifest()), [("invalid.json", correction)])

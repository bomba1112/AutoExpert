"""Generation drafts retain exact source scopes and unresolved years."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "build_us_generation_hypotheses",
    ROOT / "scripts/build_us_generation_hypotheses.py",
)
generation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generation)


def candidate(epa_id, year, model="Camry", epa_model="Camry Sedan", vclass="Midsize Cars"):
    return {
        "epa_vehicle_id": str(epa_id),
        "make": "Toyota",
        "model": model,
        "epa_model": epa_model,
        "model_year": year,
        "epa_fields": {"VClass": vclass},
    }


def join(row, classification="CANDIDATE_NEW"):
    return {
        "epa_vehicle_id": row["epa_vehicle_id"],
        "make": row["make"],
        "model": row["model"],
        "model_year": row["model_year"],
        "classification": classification,
    }


def test_verified_exact_year_reference_does_not_extrapolate_to_neighboring_years():
    candidates = [candidate(1, 2019), candidate(2, 2020), candidate(3, 2021)]
    published = generation.index_published(
        [
            {
                "make": "Toyota",
                "model": "Camry",
                "model_year": 2019,
                "market": "US",
                "generation": "XV70",
                "variant_id": "published-1",
                "body": "SEDAN",
            }
        ]
    )
    years = generation.candidate_years(
        candidates, [join(row) for row in candidates], published, {}
    )
    assert [row["generation_hypothesis"] for row in years] == ["XV70", None, None]
    assert years[0]["generation_resolution"].startswith("EXACT_YEAR_VERIFIED")
    segments = generation.segment_years(years)
    assert [(item["year_start"], item["year_end"], item["generation"]) for item in segments] == [
        (2019, 2019, "XV70"),
        (2020, 2021, None),
    ]
    assert all(item["status"] == "AI_GENERATION_DRAFT" for item in segments)
    assert all(not item["publication_eligible"] for item in segments)


def test_competing_generation_labels_remain_ambiguous():
    source = candidate(4, 2019)
    key = generation.model_year_key("Toyota", "Camry", 2019)
    verified = generation.index_published(
        [
            {
                "make": "Toyota",
                "model": "Camry",
                "model_year": 2019,
                "market": "US",
                "generation": "XV70",
                "variant_id": "published-2",
            }
        ]
    )
    draft = {
        key: [
            {
                "label": "XV50",
                "origin": "PRIOR_AI_DRAFT",
                "source_ref": "prior-ai-1",
                "body": "SEDAN",
            }
        ]
    }
    result = generation.candidate_years([source], [join(source)], verified, draft)[0]
    assert result["generation_hypothesis"] is None
    assert result["generation_resolution"] == "AMBIGUOUS_GENERATION"
    assert {item["label"] for item in result["generation_candidates"]} == {"XV50", "XV70"}


def test_epa_body_alias_is_candidate_only_and_alias_join_stays_unresolved():
    source = candidate(5, 2020, epa_model="Camry Coupe", vclass="Small Cars")
    result = generation.candidate_years(
        [source], [join(source, "POSSIBLE_ALIAS")], {}, {}
    )[0]
    assert result["generation_resolution"] == "UNRESOLVED_GENERATION"
    assert result["body_aliases_candidate"] == [
        {"alias": "COUPE", "basis": "EPA_RAW_MODEL_STRING", "status": "CANDIDATE_ONLY"}
    ]
    assert result["join_classifications"] == {"POSSIBLE_ALIAS": 1}


def test_previous_ai_queue_respects_only_listed_years():
    queue = {
        "queue": [
            {
                "queue_id": "q1",
                "make": "Toyota",
                "model": "Camry",
                "market": "US",
                "generation_candidate": "XV70",
                "target_model_years": [2018, 2019],
            }
        ]
    }
    indexed = generation.index_prior_drafts(queue, [])
    assert set(key[2] for key in indexed) == {2018, 2019}
    assert generation.model_year_key("Toyota", "Camry", 2020) not in indexed

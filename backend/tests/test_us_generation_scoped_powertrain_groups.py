"""EPA groups split at draft generation boundaries without losing source rows."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "generation_scoped_powertrain_groups",
    ROOT / "scripts/group_us_candidate_powertrains_by_generation.py",
)
groups = importlib.util.module_from_spec(spec)
spec.loader.exec_module(groups)


def test_boundary_and_gap_split_without_verification():
    source = {
        "make": "Audi",
        "model": "A3",
        "model_years": [2015, 2016, 2018, 2019],
        "epa_vehicle_ids_by_year": {
            "2015": ["1", "2"],
            "2016": ["3"],
            "2018": ["4"],
            "2019": ["5"],
        },
        "epa_row_count": 5,
        "model_year_start": 2015,
        "model_year_end": 2019,
        "normalized_powertrain_key": "same",
    }
    mapping = {
        ("Audi", "A3", 2015): ("8V", "PRIOR_AI_HYPOTHESIS_UNVERIFIED"),
        ("Audi", "A3", 2016): ("8V", "PRIOR_AI_HYPOTHESIS_UNVERIFIED"),
        ("Audi", "A3", 2018): ("8V", "PRIOR_AI_HYPOTHESIS_UNVERIFIED"),
        ("Audi", "A3", 2019): ("8Y", "PRIOR_AI_HYPOTHESIS_UNVERIFIED"),
    }
    result = groups.split_group(source, mapping)
    assert [x["model_years"] for x in result] == [[2015, 2016], [2018], [2019]]
    assert [x["generation_candidate"] for x in result] == ["8V", "8V", "8Y"]
    assert sum(x["epa_row_count"] for x in result) == 5
    assert all(x["publication_eligible"] is False for x in result)


def test_generation_year_mapping_rejects_overlaps(tmp_path):
    path = tmp_path / "generations.jsonl"
    path.write_text(
        '{"make":"Audi","model":"A3","observed_model_years":[2015],'
        '"generation":"8V","generation_resolution":"PRIOR_AI_HYPOTHESIS_UNVERIFIED"}\n'
        '{"make":"Audi","model":"A3","observed_model_years":[2015],'
        '"generation":"8Y","generation_resolution":"AMBIGUOUS_GENERATION"}\n',
        encoding="utf-8",
    )
    try:
        groups.source_years(path)
    except ValueError as exc:
        assert "DUPLICATE_GENERATION_YEAR" in str(exc)
    else:
        raise AssertionError("overlapping generation hypotheses must fail")

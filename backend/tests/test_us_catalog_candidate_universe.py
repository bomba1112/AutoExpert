"""The EPA universe is a source-preserving candidate index, not publication."""

import csv
import importlib.util
import io
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "build_us_catalog_candidate_universe",
    ROOT / "scripts/build_us_catalog_candidate_universe.py",
)
universe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(universe)


def source_rows(records):
    columns = sorted(universe.REQUIRED_COLUMNS | {"atvType", "fuelType2", "tCharger"})
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows(records)
    buffer.seek(0)
    return csv.DictReader(buffer)


def policy():
    return json.loads(universe.POLICY.read_text(encoding="utf-8"))


def row(epa_id, make, model, year, *, drive="Front-Wheel Drive", trany="Automatic 6-spd"):
    return {
        "id": str(epa_id),
        "make": make,
        "model": model,
        "baseModel": model,
        "year": str(year),
        "displ": "2.0",
        "cylinders": "4",
        "trany": trany,
        "drive": drive,
        "fuelType1": "Regular Gasoline",
        "eng_dscr": "SIDI",
        "evMotor": "",
        "VClass": "Midsize Cars",
        "tCharger": "T",
    }


def test_full_approved_make_scope_and_lower_year_boundaries_preserve_2027():
    source = source_rows(
        [
            row(1, "BMW", "3 Series", 1999),
            row(2, "BMW", "3 Series", 2000),
            row(3, "Toyota", "Camry", 2004),
            row(4, "Toyota", "Camry", 2005),
            row(5, "Toyota", "Camry", 2027),
            row(6, "Ford", "Focus", 2020),
        ]
    )
    rows, counts, columns = universe.select_universe(source, policy(), "a" * 64)
    assert [item["epa_vehicle_id"] for item in rows] == ["2", "4", "5"]
    assert counts["below_make_year_boundary"] == 2
    assert counts["other_make_rows"] == 1
    assert len(columns) == len(rows[0]["epa_fields"])
    assert rows[-1]["model_year"] == 2027


def test_missing_core_field_is_flagged_but_does_not_discard_source_row():
    source = source_rows([row(7, "Toyota", "Camry", 2010, drive="", trany="")])
    rows, _, _ = universe.select_universe(source, policy(), "a" * 64)
    assert len(rows) == 1
    assert rows[0]["missing_core_fields"] == ["transmission", "drivetrain"]
    assert rows[0]["epa_fields"]["drive"] == ""


def test_powertrain_grouping_joins_identical_years_but_keeps_drive_distinct():
    source = source_rows(
        [
            row(8, "Toyota", "Camry", 2010),
            row(9, "Toyota", "Camry", 2011),
            row(10, "Toyota", "Camry", 2011, drive="All-Wheel Drive"),
        ]
    )
    rows, _, _ = universe.select_universe(source, policy(), "a" * 64)
    counts = universe.denominator(rows, policy()["primary_makes"])
    assert counts["epa_rows_after_filter"] == 3
    assert counts["model_year_pairs"] == 2
    assert counts["normalized_powertrain_combinations"] == 2
    assert counts["model_year_powertrain_combinations"] == 3
    assert rows[0]["normalized_powertrain_key"] == rows[1]["normalized_powertrain_key"]
    assert rows[1]["normalized_powertrain_key"] != rows[2]["normalized_powertrain_key"]


def test_contiguous_groups_keep_missing_model_year_gap():
    source = source_rows(
        [
            row(11, "Toyota", "Camry", 2010),
            row(12, "Toyota", "Camry", 2011),
            row(13, "Toyota", "Camry", 2013),
        ]
    )
    rows, _, _ = universe.select_universe(source, policy(), "a" * 64)
    groups = universe.contiguous_powertrain_groups(rows, policy()["primary_makes"])
    assert [(group["model_year_start"], group["model_year_end"]) for group in groups] == [
        (2010, 2011),
        (2013, 2013),
    ]
    assert groups[0]["epa_vehicle_ids_by_year"] == {"2010": ["11"], "2011": ["12"]}
    assert all(group["generation"] is None for group in groups)


def test_schema_change_fails_closed():
    with pytest.raises(ValueError, match="EPA_SCHEMA_CHANGED"):
        universe.select_universe(
            csv.DictReader(io.StringIO("id,make,model,year\n1,Toyota,Camry,2020\n")),
            policy(),
            "a" * 64,
        )

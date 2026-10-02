"""EPA master matching retains source rows without inventing factory variants."""

import csv
import importlib.util
import io
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "epa_bulk_candidates", ROOT / "scripts/epa_bulk_candidates.py"
)
epa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(epa)


def fixtures():
    policy = {
        "primary_makes": ["Land Rover", "Mitsubishi", "Infiniti", "Toyota", "Tesla"],
        "first_wave_model_order": {
            "Land Rover": [
                "Range Rover",
                "Range Rover Sport",
                "Range Rover Evoque",
                "Discovery Sport",
            ],
            "Mitsubishi": ["Outlander", "Outlander Sport"],
            "Infiniti": ["FX"],
            "Toyota": ["Camry"],
            "Tesla": ["Model 3"],
        },
        "allowed_markets": ["US"],
        "minimum_model_year": 2000,
    }
    aliases = json.loads((ROOT / "scripts/epa_master_aliases.json").read_text(encoding="utf-8"))
    return policy, aliases


def csv_rows(rows):
    columns = [
        "id",
        "make",
        "model",
        "baseModel",
        "year",
        "trany",
        "drive",
        "fuelType1",
        "comb08",
        "engId",
        "combE",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


@pytest.mark.parametrize(
    ("make", "model", "base", "expected"),
    [
        ("Land Rover", "Range Rover Sport", "Range Rover", "Range Rover Sport"),
        ("Land Rover", "Range Rover Evoque", "Range Rover", "Range Rover Evoque"),
        ("Land Rover", "Range Rover LWB", "Range Rover", "Range Rover"),
        ("Land Rover", "Discovery Sport", "Discovery", "Discovery Sport"),
        ("Land Rover", "Range Rover Velar", "Range Rover", None),
        ("Mitsubishi", "Outlander Sport 2WD", "Outlander", "Outlander Sport"),
        ("Mitsubishi", "Outlander 4WD", "Outlander", "Outlander"),
        ("Infiniti", "FX37 AWD", "FX37", "FX"),
        ("Toyota", "Camry Solara", "Camry", None),
    ],
)
def test_family_collisions_use_reviewed_scope_without_cross_assignment(make, model, base, expected):
    policy, aliases = fixtures()
    row = {"make": make, "model": model, "baseModel": base}
    matched = epa.match_master(row, epa.scopes(policy), aliases)
    assert (matched[0] if matched else None) == expected


def test_bulk_extract_preserves_source_tuple_and_cycle_without_certifying_trim():
    policy, aliases = fixtures()
    text = csv_rows(
        [
            {
                "id": "12",
                "make": "Tesla",
                "model": "Model 3",
                "baseModel": "Model 3",
                "year": "2020",
                "trany": "Automatic (A1)",
                "drive": "All-Wheel Drive",
                "fuelType1": "Electricity",
                "comb08": "0",
                "engId": "EPA-only-7",
                "combE": "26",
            },
            {
                "id": "13",
                "make": "Mitsubishi",
                "model": "Outlander Sport 2WD",
                "baseModel": "Outlander",
                "year": "2016",
                "trany": "Automatic (AV-S6)",
                "drive": "Front-Wheel Drive",
                "fuelType1": "Regular Gasoline",
                "comb08": "28",
            },
            {
                "id": "14",
                "make": "Mitsubishi",
                "model": "Outlander Sport 2WD",
                "baseModel": "Outlander",
                "year": "2027",
                "trany": "Manual 5-spd",
                "drive": "Front-Wheel Drive",
                "fuelType1": "Regular Gasoline",
                "comb08": "28",
            },
        ]
    )
    rows, meta = epa.select_candidates(text, policy, aliases, "a" * 64, 2026)
    assert [row["epa_vehicle_id"] for row in rows] == ["13", "12"]
    assert rows[0]["raw_fields"]["trany"] == "Automatic (AV-S6)"
    assert rows[0]["source"]["dataset_sha256"] == "a" * 64
    assert rows[1]["raw_fields"]["epa_engine_index"] == "EPA-only-7"
    assert "engId" not in rows[1]["raw_fields"]
    assert epa.SOURCE_FIELD_UNITS["combE"] == "kWh/100mi_EPA"
    assert "factory_trim" not in rows[0] and "seats" not in rows[0]
    assert meta["counts"]["outside_year_scope"] == 1


def test_schema_drift_fails_closed():
    policy, aliases = fixtures()
    with pytest.raises(ValueError, match="EPA_SCHEMA_CHANGED"):
        epa.select_candidates(
            "id,make,model,year\n1,Tesla,Model 3,2020\n", policy, aliases, "a" * 64, 2026
        )

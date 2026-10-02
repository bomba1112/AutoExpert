"""Standalone EPA index preserves source tuples and supports scoped queries."""

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "index_us_catalog_candidates_sqlite",
    ROOT / "scripts/index_us_catalog_candidates_sqlite.py",
)
indexer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(indexer)


def candidate(epa_id, make, model, year, powertrain):
    fields = {
        "id": str(epa_id),
        "make": make,
        "model": model,
        "year": str(year),
        "displ": "2.0",
        "cylinders": "4",
        "fuelType1": "Regular Gasoline",
        "trany": "Automatic 6-spd",
        "drive": "Front-Wheel Drive",
        "evMotor": "",
        "VClass": "Midsize Cars",
    }
    return {
        "epa_vehicle_id": str(epa_id),
        "make": make,
        "model": model,
        "epa_model": model,
        "model_year": year,
        "normalized_powertrain_key": powertrain,
        "missing_core_fields": [],
        "normalized_powertrain": {"displ": "2", "trany": "automatic 6-spd"},
        "epa_fields": fields,
        "source": {
            "dataset_sha256": "a" * 64,
            "row_locator": f"vehicles.csv:id={epa_id}",
        },
    }


def source_bytes(rows):
    return b"".join(indexer.canonical_json(row).encode() + b"\n" for row in rows)


def test_standalone_index_queries_all_required_keys_and_preserves_epa_fields(tmp_path):
    rows = [
        candidate(1, "Toyota", "Camry", 2018, "pt-1"),
        candidate(2, "Toyota", "Camry", 2019, "pt-1"),
        candidate(3, "BMW", "3 Series", 2020, "pt-2"),
    ]
    source = source_bytes(rows)
    out = tmp_path / "candidate-index.sqlite"
    summary = indexer.build_index(
        source,
        out,
        expected_sha256=indexer.digest(source),
        expected_rows=3,
        expected_brands=2,
        expected_columns=set(rows[0]["epa_fields"]),
        epa_source_sha256="a" * 64,
    )
    assert summary["candidate_rows"] == 3
    assert summary["production_database_modified"] is False
    with sqlite3.connect(out) as db:
        match = db.execute(
            """SELECT epa_vehicle_id, epa_fields_json FROM candidate_rows
            WHERE make=? AND model=? AND model_year=?""",
            ("Toyota", "Camry", 2018),
        ).fetchone()
        assert match[0] == "1"
        assert json.loads(match[1]) == rows[0]["epa_fields"]
        assert db.execute(
            "SELECT COUNT(*) FROM candidate_rows WHERE normalized_powertrain_key=?",
            ("pt-1",),
        ).fetchone()[0] == 2
        assert db.execute(
            "SELECT model FROM candidate_rows WHERE epa_vehicle_id=?", ("3",)
        ).fetchone()[0] == "3 Series"
        indexes = {entry[1] for entry in db.execute("PRAGMA index_list(candidate_rows)")}
        assert {
            "idx_candidate_make_model_year",
            "idx_candidate_model",
            "idx_candidate_year",
            "idx_candidate_powertrain",
        } <= indexes


def test_index_rejects_source_hash_mismatch_without_creating_output(tmp_path):
    source = source_bytes([candidate(4, "Toyota", "Camry", 2018, "pt-1")])
    out = tmp_path / "candidate-index.sqlite"
    with pytest.raises(ValueError, match="CANDIDATE_JSONL_SHA_MISMATCH"):
        indexer.build_index(
            source,
            out,
            expected_sha256="0" * 64,
            expected_rows=1,
            expected_brands=1,
            expected_columns=set(json.loads(source)["epa_fields"]),
            epa_source_sha256="a" * 64,
        )
    assert not out.exists()

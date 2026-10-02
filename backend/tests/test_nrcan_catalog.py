"""Adapter tests use deliberately synthetic rows in isolated memory."""

import csv
import io

import pytest
from app.schemas.knowledge import ImportManifest
from app.services.nrcan_catalog import nrcan_record, parse_nrcan


def row(**kw):
    r = {
        "Model year": "2026",
        "Make": "Example",
        "Model": "Model AWD",
        "Vehicle class": "Compact",
        "Transmission": "AV7",
        "Engine size (L)": "2.0",
        "Cylinders": "4",
        "Fuel type": "X",
        "Combined (L/100 km)": "5.5",
    }
    r.update(kw)
    return r


def test_source_tuple_no_generation_or_physical_cvt_gears():
    r = nrcan_record(
        row(),
        kind="CONVENTIONAL",
        source_url="https://example.test/source",
        line=2,
        family={"make": "Example", "model": "Model"},
    )
    assert r.generation is None and r.original_market == "CA"
    assert "gears" not in r.facts and "trim" not in r.facts
    assert r.facts["drivetrain"].value == "AWD"
    assert r.facts["powertrain"].value == "COMBUSTION_UNSPECIFIED"
    assert r.facts["fuel_combined"].value == "5.5" and r.facts["fuel_combined"].labels == {}


def test_blended_phev_does_not_lose_gasoline_component():
    r = row(
        **{
            "Fuel type 1": "B/X",
            "Fuel type 2": "X",
            "Combined Le/100 km": "2.7 ([23.2 kWh + 0.1 L]/100 km)",
        }
    )
    p = nrcan_record(
        r,
        kind="PHEV",
        source_url="https://example.test/source",
        line=2,
        family={"make": "Example", "model": "Model"},
    )
    assert p.facts["electricity_combined"].value == "23.2"
    assert p.facts["electric_mode_fuel"].value == "0.1"


def test_schema_drift_and_duplicate_identity_stop_batch():
    m = ImportManifest(
        source_id="test",
        parser="nrcan-csv-v1",
        dataset_kind="CONVENTIONAL",
        family_mappings=[{"make": "Example", "model": "Model"}],
        selection_basis="Synthetic adapter fixture",
    )
    with pytest.raises(ValueError, match="NRCAN_SCHEMA_CHANGED"):
        parse_nrcan("unexpected,column\na,b\n", m, "https://example.test/source")
    s = io.StringIO()
    writer = csv.DictWriter(s, fieldnames=list(row()))
    writer.writeheader()
    writer.writerow(row())
    writer.writerow(row(**{"Combined (L/100 km)": "8.0"}))
    with pytest.raises(ValueError, match="NRCAN_DUPLICATE_IDENTITY_CONFLICT"):
        parse_nrcan(s.getvalue(), m, "https://example.test/source")


def test_longest_reviewed_model_boundary_keeps_distinct_families():
    m = ImportManifest(
        source_id="test",
        parser="nrcan-csv-v1",
        dataset_kind="CONVENTIONAL",
        family_mappings=[
            {"make": "Example", "model": "Model"},
            {"make": "Example", "model": "Model Cross"},
        ],
        selection_basis="Synthetic distinct-family regression",
    )
    s = io.StringIO()
    writer = csv.DictWriter(s, fieldnames=list(row()))
    writer.writeheader()
    writer.writerow(row())
    writer.writerow(row(**{"Model": "Model Cross AWD"}))
    records = parse_nrcan(s.getvalue(), m, "https://example.test/source")
    assert {r["model"] for r in records} == {"Model", "Model Cross"}
    assert len({r["external_key"] for r in records}) == 2

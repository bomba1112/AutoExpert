"""Owner scope changes visibility, never historical facts or identity readiness."""

import copy
import sys
from pathlib import Path

import pytest
from app.services.catalog_scope import in_active_scope, minimum_year, scope_policy
from app.services.market_priority import base_catalog_batch


@pytest.mark.parametrize(
    "make,year,market,expected",
    [
        ("Mercedes-Benz", 2000, "US", True),
        ("BMW", 2000, "US", True),
        ("BMW", 1999, "US", False),
        ("Toyota", 2004, "US", False),
        ("Toyota", 2005, "US", True),
        ("Honda", 2005, "CA", False),
        ("Skoda", 2020, "US", False),
        ("Unknown", 2020, "US", False),
        ("Range Rover", 2005, "US", True),
        ("Tesla", 2005, "US", True),
    ],
)
def test_boundaries_are_scope_only_not_proof_of_existence(make, year, market, expected):
    assert in_active_scope(make, market, year) is expected
    assert minimum_year("Unknown") is None


def test_generation_start_before_boundary_does_not_remove_in_scope_years():
    from app.services.catalog_scope import catalog_in_active_scope

    record = {
        "make": "Toyota",
        "original_market": "US",
        "model_year": 2005,
        "production_from": 2002,
        "generation_code": "XV30",
    }
    previous = copy.deepcopy(record)
    assert catalog_in_active_scope(record)
    assert record == previous


def test_group_below_boundary_cannot_hide_in_family():
    import json

    root = Path(__file__).resolve().parents[2]
    m = json.loads((root / "data/manifests/us-bulk-data-08.json").read_text())
    f = next(f for f in m["families"] if f["make"] == "Toyota")
    f["groups"][0]["year_from"] = 2004
    with pytest.raises(ValueError, match="GROUP_OUTSIDE_ACTIVE"):
        base_catalog_batch(scope_policy(), m)


def test_single_writer_excludes_second_and_releases(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from catalog_writer_lock import catalog_writer_lock

    with catalog_writer_lock(tmp_path / "writer.lock"), pytest.raises(
        RuntimeError, match="ALREADY_RUNNING"
    ), catalog_writer_lock(tmp_path / "writer.lock"):
        pass
    with catalog_writer_lock(tmp_path / "writer.lock"):
        pass

"""EPA CORE admission is separate from the factory identity gate."""

from copy import deepcopy

from app.services.catalog_verification import (
    base_catalog_ready,
    source_confirmed_core_ready,
)


def _fact(value):
    return {
        "value": value,
        "status": "CONFIRMED",
        "locator": "EPA vehicle 123: source field",
        "source_id": "epa",
    }


def _core():
    return {
        "make": "Honda",
        "model": "Accord",
        "model_year": 2020,
        "original_market": "US",
        "source_registry_id": "epa",
        "source_url": "https://www.fueleconomy.gov/ws/rest/vehicle/123",
        "facts": {
            "powertrain": _fact("ICE"),
            "fuel": _fact("GASOLINE"),
            "engine_displacement": _fact("1.5"),
            "transmission_description": _fact("Automatic (AV-S7)"),
            "transmission_family": _fact("VARIABLE_UNSPECIFIED"),
            "drivetrain": _fact("FWD"),
        },
    }


def test_core_admits_source_backed_annual_vehicle_without_factory_identity():
    row = _core()
    assert source_confirmed_core_ready(row)
    assert not base_catalog_ready(row)
    assert "generation" not in row and "body" not in row["facts"] and "seats" not in row["facts"]
    for broad_family in ("AUTOMATIC_UNSPECIFIED", "VARIABLE_UNSPECIFIED", "AMT_UNSPECIFIED"):
        row["facts"]["transmission_family"]["value"] = broad_family
        assert source_confirmed_core_ready(row)


def test_core_requires_source_provenance_and_exact_drive_but_not_optional_identity():
    for change in ("no_source", "no_locator", "no_displacement", "ambiguous_drive", "other_market"):
        row = deepcopy(_core())
        if change == "no_source":
            row["source_registry_id"] = "ai-draft"
        elif change == "no_locator":
            row["facts"]["transmission_description"].pop("locator")
        elif change == "no_displacement":
            row["facts"].pop("engine_displacement")
        elif change == "ambiguous_drive":
            row["facts"]["drivetrain"]["value"] = "4-Wheel or All-Wheel Drive"
        else:
            row["original_market"] = "CA"
        assert not source_confirmed_core_ready(row), change


def test_electric_core_uses_source_powertrain_without_displacement():
    row = _core()
    row["facts"]["powertrain"] = _fact("BEV")
    row["facts"].pop("engine_displacement")
    row["facts"].pop("fuel")
    assert source_confirmed_core_ready(row)
    row["facts"]["powertrain"] = _fact("FCEV")
    assert source_confirmed_core_ready(row)

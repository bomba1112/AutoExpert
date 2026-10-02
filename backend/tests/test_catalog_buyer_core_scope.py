"""Buyer-level separation between source-confirmed CORE and factory-scoped rows."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from app.services import catalog_buyer as buyer


@pytest.mark.parametrize(
    ("source_family", "requested", "expected"),
    [
        ("AUTOMATIC_UNSPECIFIED", "AUTOMATIC_UNSPECIFIED", "MATCH"),
        ("VARIABLE_UNSPECIFIED", "AUTOMATIC_UNSPECIFIED", "MATCH"),
        ("AMT_UNSPECIFIED", "AUTOMATIC_UNSPECIFIED", "MATCH"),
        ("AUTOMATIC_UNSPECIFIED", "AT", "UNKNOWN"),
        ("AUTOMATIC_UNSPECIFIED", "CVT", "UNKNOWN"),
        ("AUTOMATIC_UNSPECIFIED", "DCT", "UNKNOWN"),
        ("VARIABLE_UNSPECIFIED", "CVT", "UNKNOWN"),
        ("AMT_UNSPECIFIED", "DCT", "UNKNOWN"),
        ("VARIABLE_UNSPECIFIED", "AT", "CONFLICT"),
        ("MANUAL", "AUTOMATIC_UNSPECIFIED", "CONFLICT"),
    ],
)
def test_source_unspecified_transmission_never_claims_exact_construction(
    source_family, requested, expected
):
    assert buyer._transmission_fit(source_family, requested) == expected


def test_core_without_generation_body_or_seats_has_clean_consumer_card():
    catalog = {
        "make": "Test make",
        "model": "Test model",
        "model_year": 2020,
        "original_market": "US",
        "generation": "Generation unverified",
        "generation_code": "UNRESOLVED",
        "configuration": "Generation unverified · 2.0 · Automatic (S6) · Front-Wheel Drive",
        "source_registry_id": "epa",
        "source_url": "https://www.fueleconomy.gov/ws/rest/vehicle/1",
        "revision_id": "revision-1",
        "publication_scope": "COMMERCIAL",
        "facts": {
            "powertrain": {"value": "ICE", "status": "CONFIRMED"},
            "engine_displacement": {"value": "2.0", "status": "CONFIRMED", "unit": "L"},
            "transmission_description": {"value": "Automatic (S6)", "status": "CONFIRMED"},
            "transmission_family": {
                "value": "AUTOMATIC_UNSPECIFIED",
                "status": "CONFIRMED",
            },
            "drivetrain": {"value": "FWD", "status": "CONFIRMED"},
            "body": {"value": "UNKNOWN", "status": "INSUFFICIENT_DATA"},
        },
    }
    with (
        patch.object(buyer, "source_confirmed_core_ready", return_value=True),
        patch.object(buyer, "base_catalog_ready", return_value=False),
        patch.object(buyer, "us_catalog_ready", return_value=False),
        patch.object(buyer, "identity_verified", return_value=False),
        patch.object(buyer, "catalog_in_active_scope", return_value=True),
    ):
        assert buyer.active_us_rows([(SimpleNamespace(id="one"), catalog)])
        assert not buyer.active_us_base_rows([(SimpleNamespace(id="one"), catalog)])
        item = buyer.card(None, SimpleNamespace(id="one"), catalog, assets=[])

    assert item["source_confirmed_core"] is True
    assert item["verified_scoped"] is False
    assert item["us_catalog_ready"] is False
    assert item["generation"] is None and item["generation_code"] is None
    assert "body" not in item["facts"]
    assert "Generation unverified" not in item["configuration"]
    assert "(S6)" in item["configuration"]
    profile_keys = {row["key"] for row in buyer.vehicle_profile(catalog, "ru")["summary"]}
    assert "generation" not in profile_keys

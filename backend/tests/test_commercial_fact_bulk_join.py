"""Safety boundaries for dry-run joins from the existing research universe."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_commercial_fact_overlay_batch import (  # noqa: E402
    _mechanical_key,
    factory_claims,
    publisher_host,
)


def factory_variant(
    *, url="https://www.kiamedia.com/us/en/models/forte/2018/specifications", year=2018
):
    values = {
        "powertrain": "ICE",
        "fuel": "GASOLINE",
        "engine_displacement": "2.0",
        "engine_description": "2.0L MPI inline-4",
        "transmission_description": "6-speed automatic",
        "transmission_family": "AT",
        "drivetrain": "FWD",
    }
    facts = {}
    for name, value in values.items():
        facts[name] = {
            "status": "CONFIRMED",
            "value": value,
            "source_id": "source-record-1",
            "documentary_source": {
                "registry_id": "factory-kia-us",
                "document_id": "factory-doc-1",
                "url": url,
                "make": "Kia",
                "model": "Forte",
                "market": "US",
                "model_year_from": year,
                "model_year_to": year,
            },
        }
    return {
        "id": "variant-1",
        "catalog_key": "factory-kia-us:forte-2018-2l-6at-fwd",
        "catalog": {
            "make": "Kia",
            "model": "Forte",
            "model_year": 2018,
            "original_market": "US",
            "source_registry_id": "factory-kia-us",
            "source_url": url,
            "facts": facts,
        },
    }


def test_exact_official_annual_source_emits_only_fact_claims():
    claims, reasons = factory_claims(factory_variant())
    assert not reasons
    assert {"make", "model", "model_year", "original_market", "drivetrain"} <= {
        claim["fact_name"] for claim in claims
    }
    assert all(claim["reuse_status"] == "COMMERCIAL_OK" for claim in claims)
    assert all(claim["evidence_scope"]["source_record_id"] == "source-record-1" for claim in claims)
    assert all(claim["evidence_scope"]["extraction_scope"] == "ISOLATED_FACT" for claim in claims)
    assert all("LX/S" not in claim["locator"] for claim in claims)


def test_third_party_mirror_and_year_mismatch_never_auto_promote():
    mirror = factory_variant(url="https://www.auto-brochures.com/Kia_Forte_2018.pdf")
    claims, reasons = factory_claims(mirror)
    assert "NO_DIRECT_MANUFACTURER_IDENTITY_ANCHOR" in reasons
    assert all(claim["reuse_status"] == "NEEDS_REVIEW" for claim in claims)

    wrong_year = factory_variant(year=2017)
    claims, reasons = factory_claims(wrong_year)
    assert "NO_DIRECT_MANUFACTURER_IDENTITY_ANCHOR" in reasons
    assert all(claim["reuse_status"] == "NEEDS_REVIEW" for claim in claims)


def test_epa_host_is_not_a_manufacturer_host_even_for_factory_registry():
    assert not publisher_host(
        "factory-kia-us", "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
    )
    assert not publisher_host(
        "factory-kia-us", "https://kiamedia.com.evil.example/us/en/models/forte/2018/specifications"
    )


def test_coarse_epa_factory_tuple_is_qa_only_not_exact_gearbox_construction():
    factory = factory_variant()["catalog"]
    epa = factory_variant()["catalog"] | {
        "source_registry_id": "epa",
        "facts": {
            **factory["facts"],
            "transmission_description": {"status": "CONFIRMED", "value": "Automatic 6-spd"},
            "transmission_family": {"status": "CONFIRMED", "value": "AUTOMATIC_UNSPECIFIED"},
        },
    }
    assert _mechanical_key(factory) == _mechanical_key(epa)
    # The only effect of this equivalence in the bulk script is an EPA QA
    # status.  factory_claims emits from the factory row, never the EPA row.
    claims, _ = factory_claims(factory_variant())
    assert all(claim["source_id"] == "factory-kia-us" for claim in claims)

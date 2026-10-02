from __future__ import annotations

from decimal import Decimal

from app.market_engine import MarketEngine
from app.models.enums import EvidenceStatus
from app.schemas.market import MarketListingInput, MarketVehicle


def _vehicle() -> MarketVehicle:
    return MarketVehicle(
        country="AZ",
        city="Baku",
        make="Example",
        model="Sedan",
        generation="G2",
        year=2022,
        engine="2.0 petrol",
        displacement_l=Decimal("2.0"),
        transmission="automatic",
        drivetrain="FWD",
        mileage_km=80_000,
        selected_price=Decimal("23000"),
        currency="AZN",
    )


def _listing(index: int, price: int, **changes: object) -> MarketListingInput:
    value: dict[str, object] = {
        "id": f"listing-{index}",
        "country": "AZ",
        "city": "Baku",
        "make": "Example",
        "model": "Sedan",
        "generation": "G2",
        "year": 2022 + index % 2,
        "engine": "2.0 petrol",
        "displacement_l": Decimal("2.0"),
        "transmission": "automatic",
        "drivetrain": "FWD",
        "mileage_km": 70_000 + index * 2_000,
        "price": Decimal(price),
        "currency": "AZN",
        "observed_at": "2026-09-01T00:00:00+00:00",
    }
    value.update(changes)
    return MarketListingInput.model_validate(value)


def test_market_statistics_remove_outlier_and_calculate_deviation() -> None:
    listings = [
        _listing(index, price)
        for index, price in enumerate([20_000, 21_000, 22_000, 23_000, 24_000, 25_000, 120_000])
    ]
    listings.append(_listing(99, 23_000, model="Unrelated"))

    result = MarketEngine().analyze(_vehicle(), listings)

    assert result.status == EvidenceStatus.ESTIMATE
    assert result.sample_count == 8
    assert result.comparable_count == 7
    assert result.used_count == 6
    assert result.excluded_outlier_count == 1
    assert result.median == Decimal("22500.00")
    assert result.absolute_deviation == Decimal("500.00")
    assert result.percentage_deviation == Decimal("2.22")
    assert "listing-6" not in result.matched_listing_ids


def test_market_requires_three_real_comparables() -> None:
    result = MarketEngine().analyze(_vehicle(), [_listing(1, 20_000), _listing(2, 21_000)])
    assert result.status == EvidenceStatus.INSUFFICIENT_DATA
    assert result.median is None
    assert result.comparable_count == 2


def test_generation_mismatch_is_not_a_comparable() -> None:
    score = MarketEngine().similarity(_vehicle(), _listing(1, 20_000, generation="G1"))
    assert score == 0


def test_unicode_vehicle_names_are_not_normalized_to_empty_strings() -> None:
    vehicle = _vehicle().model_copy(update={"make": "Марка-А", "model": "Модель-1"})
    matching = _listing(1, 20_000, make="Марка А", model="Модель 1")
    unrelated = _listing(2, 20_000, make="Другая", model="Машина")
    assert MarketEngine().similarity(vehicle, matching) > 0.8
    assert MarketEngine().similarity(vehicle, unrelated) == 0

from __future__ import annotations

from decimal import Decimal

from app.models.enums import EvidenceStatus
from app.pricing import OwnershipCostEngine
from app.schemas.ownership import ConsumptionRange, OwnershipCostInput, PlannedCost


def test_ownership_calculation_is_deterministic_and_exposes_assumptions() -> None:
    value = OwnershipCostInput(
        monthly_mileage_km=1500,
        city_share=Decimal("0.6"),
        consumption=ConsumptionRange(
            city_low=Decimal("10"),
            city_high=Decimal("12"),
            highway_low=Decimal("6"),
            highway_high=Decimal("8"),
        ),
        fuel_price_per_liter=Decimal("1.20"),
        currency="AZN",
        planned_costs=[PlannedCost(name="service", low=100, high=150, assumption="annual service")],
        starting_service_costs=[
            PlannedCost(name="start", low=200, high=300, assumption="post-purchase service")
        ],
        fuel_price_source_date="2026-09-01",
    )
    result = OwnershipCostEngine().calculate(value)

    assert result.status == EvidenceStatus.ESTIMATE
    assert result.monthly_fuel.low == Decimal("151.20")
    assert result.monthly_fuel.high == Decimal("187.20")
    assert result.yearly_fuel.low == Decimal("1814.40")
    assert result.first_year_total.low == Decimal("2114.40")
    assert result.first_year_total.high == Decimal("2696.40")
    assert any("2026-09-01" in assumption for assumption in result.assumptions)


def test_missing_fuel_inputs_return_insufficient_data_without_invention() -> None:
    result = OwnershipCostEngine().calculate(
        OwnershipCostInput(
            monthly_mileage_km=1000,
            city_share=Decimal("0.5"),
            consumption=None,
            fuel_price_per_liter=None,
            currency="AZN",
        )
    )
    assert result.status == EvidenceStatus.INSUFFICIENT_DATA
    assert result.monthly_fuel is None

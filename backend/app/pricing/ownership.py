from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.models.enums import EvidenceStatus
from app.schemas.common import MoneyRange
from app.schemas.ownership import OwnershipCostInput, OwnershipCostResult, PlannedCost

_CENT = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


class OwnershipCostEngine:
    def calculate_verified(self, db, variant, catalog, scenario, *, production_safe=False):
        """Calendar and source-priced extension; the legacy report contract stays intact."""
        from app.services.ownership_cost import calculate

        return calculate(db, variant, catalog, scenario, production_safe=production_safe)

    def calculate(self, value: OwnershipCostInput) -> OwnershipCostResult:
        planned_low, planned_high = self._sum_costs(value.planned_costs)
        planned = MoneyRange(
            low=_money(planned_low), high=_money(planned_high), currency=value.currency
        )
        assumptions = [item.assumption for item in value.planned_costs]
        assumptions.extend(item.assumption for item in value.starting_service_costs)
        if value.consumption is None or value.fuel_price_per_liter is None:
            return OwnershipCostResult(
                status=EvidenceStatus.INSUFFICIENT_DATA,
                planned_maintenance=planned,
                assumptions=assumptions,
                notes=["Fuel cost requires both a consumption range and a dated local fuel price."],
            )

        city_share = value.city_share
        highway_share = Decimal(1) - city_share
        low_l_100 = (
            value.consumption.city_low * city_share + value.consumption.highway_low * highway_share
        )
        high_l_100 = (
            value.consumption.city_high * city_share
            + value.consumption.highway_high * highway_share
        )
        monthly_liters_low = Decimal(value.monthly_mileage_km) / 100 * low_l_100
        monthly_liters_high = Decimal(value.monthly_mileage_km) / 100 * high_l_100
        monthly = MoneyRange(
            low=_money(monthly_liters_low * value.fuel_price_per_liter),
            high=_money(monthly_liters_high * value.fuel_price_per_liter),
            currency=value.currency,
        )
        yearly = MoneyRange(
            low=_money(monthly.low * 12),
            high=_money(monthly.high * 12),
            currency=value.currency,
        )
        starting_low, starting_high = self._sum_costs(value.starting_service_costs)
        first_year = MoneyRange(
            low=_money(yearly.low + planned.low + starting_low),
            high=_money(yearly.high + planned.high + starting_high),
            currency=value.currency,
        )
        assumptions.extend(
            [
                f"Monthly distance: {value.monthly_mileage_km} km.",
                (
                    f"City share: {int(city_share * 100)}%; "
                    f"highway share: {int(highway_share * 100)}%."
                ),
                "Fuel consumption is a range, not a promised real-world result.",
                f"Fuel price source date: {value.fuel_price_source_date or 'not supplied'}.",
            ]
        )
        return OwnershipCostResult(
            status=EvidenceStatus.ESTIMATE,
            monthly_fuel=monthly,
            yearly_fuel=yearly,
            planned_maintenance=planned,
            first_year_total=first_year,
            assumptions=assumptions,
            notes=["Probable repairs are excluded unless explicitly listed as planned work."],
        )

    @staticmethod
    def _sum_costs(costs: list[PlannedCost]) -> tuple[Decimal, Decimal]:
        return (
            sum((item.low for item in costs), start=Decimal(0)),
            sum((item.high for item in costs), start=Decimal(0)),
        )

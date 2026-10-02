"""Fixed unit conversions for the US technical database (one module, exact factors).

The database stores metric values (mm, L, kg, km, kW, N·m, kPa, L/100 km); the
original value and unit stay in the evidence. Factors are exact definitions where one
exists (inch, pound, US gallon, US quart, mile), otherwise the standard published value.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

MM_PER_IN = Decimal("25.4")
L_PER_US_GAL = Decimal("3.785411784")
L_PER_US_QT = Decimal("0.946352946")
KG_PER_LB = Decimal("0.45359237")
KM_PER_MI = Decimal("1.609344")
L_PER_CU_FT = Decimal("28.316846592")
KW_PER_HP = Decimal("0.745699872")  # mechanical horsepower (SAE net figures)
NM_PER_LB_FT = Decimal("1.3558179483")
KPA_PER_PSI = Decimal("6.894757293")
L100KM_MPG_US = Decimal("235.2145833")  # L/100 km = constant / US mpg

FACTORS = {
    ("in", "mm"): MM_PER_IN,
    ("gal", "L"): L_PER_US_GAL,
    ("qt", "L"): L_PER_US_QT,
    ("lb", "kg"): KG_PER_LB,
    ("mi", "km"): KM_PER_MI,
    ("cu_ft", "L"): L_PER_CU_FT,
    ("hp", "kW"): KW_PER_HP,
    ("lb_ft", "N·m"): NM_PER_LB_FT,
    ("psi", "kPa"): KPA_PER_PSI,
}
# Decimal places kept after conversion, per target unit.
PLACES = {"mm": 0, "L": 1, "kg": 0, "km": 0, "kW": 1, "N·m": 0, "kPa": 0, "L/100km": 1}


def _round(value: Decimal, unit: str) -> Decimal:
    exponent = Decimal(1).scaleb(-PLACES.get(unit, 2))
    return value.quantize(exponent, rounding=ROUND_HALF_UP)


def convert(value, source_unit: str, target_unit: str) -> Decimal:
    """Convert with a fixed factor and round to the target unit's storage precision."""
    number = Decimal(str(value))
    if source_unit == target_unit:
        return _round(number, target_unit)
    if (source_unit, target_unit) == ("mpg", "L/100km"):
        if number <= 0:
            raise ValueError("MPG_MUST_BE_POSITIVE")
        return _round(L100KM_MPG_US / number, target_unit)
    factor = FACTORS.get((source_unit, target_unit))
    if factor is None:
        raise ValueError(f"NO_FIXED_FACTOR:{source_unit}->{target_unit}")
    return _round(number * factor, target_unit)

"""Units by language (product phase, stage 1).

The database stores metric values. English (US / Canada) shows US units with the metric value in
brackets: miles, quarts, gallons, psi, inches, pounds, mpg, °F; Russian and Azerbaijani show the
metric value as stored. Every conversion goes through app.services.tech_units (one module, exact
factors); this module only chooses the display unit and formats.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.services.tech_units import FACTORS, L100KM_MPG_US

# keys whose litres are a fuel tank (gallons); other litres are fluids (quarts)
GALLON_KEYS = {"fuel_tank_l", "fuel_tank", "fuel_tank_gal"}
US_UNIT = {"mm": ("in", 1), "kg": ("lb", 0), "km": ("mi", 0), "kPa": ("psi", 0), "m": ("ft", 1),
           "L/100km": ("mpg", 0), "N·m": ("lb-ft", 0), "kW": ("hp", 0)}
SOURCE_OF = {"in": "in", "lb": "lb", "mi": "mi", "psi": "psi", "ft": "ft", "lb-ft": "lb_ft", "hp": "hp", "qt": "qt", "gal": "gal"}
METRIC_PLACES = {"mm": 0, "kg": 0, "km": 0, "kPa": 0, "m": 1, "L": 1, "L/100km": 1, "N·m": 0, "kW": 0}


def _q(value: Decimal, places: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def to_us(value, unit: str, key: str = "") -> tuple[Decimal, str] | None:
    """(value, US unit) of a metric value, or None when the unit has no US display."""
    number = Decimal(str(value))
    if unit == "L":
        target, places = ("gal", 1) if key in GALLON_KEYS else ("qt", 1)
    elif unit == "°C":
        return _q(number * 9 / 5 + 32, 0), "°F"
    elif unit in US_UNIT:
        target, places = US_UNIT[unit]
    else:
        return None
    if unit == "L/100km":
        return (_q(L100KM_MPG_US / number, places), "mpg") if number > 0 else None
    factor = FACTORS[(SOURCE_OF[target], unit)]
    return _q(number / factor, places), target


def fmt(value) -> str:
    d = Decimal(str(value))
    d = d.normalize() if d == d.to_integral() else d
    return f"{d:,f}" if d == d.to_integral() else f"{d:,}"


def show(value, unit: str, language: str, key: str = "") -> str | None:
    """'185.1 in (4,702 mm)' in English; None when the language keeps the metric value."""
    if language != "en" or unit is None:
        return None
    try:
        us = to_us(value, unit, key)
    except (ArithmeticError, ValueError, KeyError):
        return None
    if us is None:
        return None
    metric = _q(Decimal(str(value)), METRIC_PLACES.get(unit, 1))
    return f"{fmt(us[0])} {us[1]} ({fmt(metric)} {unit})"


def distance(km, miles_original=None, language: str = "ru") -> str:
    """A maintenance distance: miles as printed (else converted) with km, in English."""
    if language != "en":
        return f"{fmt(km)} km"
    miles = Decimal(str(miles_original)) if miles_original else to_us(km, "km")[0]
    return f"{fmt(miles)} mi ({fmt(km)} km)"

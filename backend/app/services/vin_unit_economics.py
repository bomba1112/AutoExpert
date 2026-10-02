"""Fail-closed unit economics for one VIN-history report.

This calculation is independent of the legacy mock product prices. A missing
commercial quote is never interpreted as a zero-cost provider request.
Commercial display/resale rights must be checked separately before sale.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class EconomicsStatus(StrEnum):
    SUITABLE = "SUITABLE"
    UNSUITABLE = "UNSUITABLE"
    NEEDS_COMMERCIAL_QUOTE = "NEEDS_COMMERCIAL_QUOTE"
    NEEDS_FX_SNAPSHOT = "NEEDS_FX_SNAPSHOT"
    NEEDS_RETAIL_PRICE = "NEEDS_RETAIL_PRICE"


@dataclass(frozen=True)
class EconomicAssessment:
    status: EconomicsStatus
    sellable: bool
    provider_cost_azn: Decimal | None
    payment_fee_azn: Decimal | None
    tax_fee_azn: Decimal | None
    retry_cost_azn: Decimal
    total_cost_azn: Decimal | None
    gross_margin_azn: Decimal | None
    gross_margin_pct: Decimal | None
    minimum_margin_azn: Decimal


def _amount(value: Decimal | int | float | str, label: str, *, positive: bool = False) -> Decimal:
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0 or (positive and amount == 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{label} must be a finite {qualifier} amount")
    return amount


def evaluate(
    *,
    provider_cost_usd: Decimal | int | float | str | None = None,
    provider_cost_azn: Decimal | int | float | str | None = None,
    retail_price_azn: Decimal | int | float | str | None,
    fx_rate_azn_per_usd: Decimal | int | float | str | None = None,
    payment_fee_azn: Decimal | int | float | str = Decimal("0"),
    payment_fee_rate: Decimal | int | float | str = Decimal("0"),
    tax_fee_azn: Decimal | int | float | str = Decimal("0"),
    tax_fee_rate: Decimal | int | float | str = Decimal("0"),
    retry_cost_azn: Decimal | int | float | str = Decimal("0"),
    minimum_margin_azn: Decimal | int | float | str,
) -> EconomicAssessment:
    """Assess one quote. FX is AZN per USD from an explicit dated snapshot.

    ``sellable`` expresses the configured margin rule only; caller must also
    enforce provider authorization, product coverage, and payment availability.
    ``gross_margin_pct`` is a fraction (e.g. ``Decimal('0.2')`` means 20%).
    """

    if provider_cost_usd is not None and provider_cost_azn is not None:
        raise ValueError("Specify provider cost in exactly one currency")

    fixed_payment = _amount(payment_fee_azn, "payment_fee_azn")
    payment_rate = _amount(payment_fee_rate, "payment_fee_rate")
    fixed_tax = _amount(tax_fee_azn, "tax_fee_azn")
    tax_rate = _amount(tax_fee_rate, "tax_fee_rate")
    retry = _amount(retry_cost_azn, "retry_cost_azn")
    minimum = _amount(minimum_margin_azn, "minimum_margin_azn")
    if payment_rate > 1 or tax_rate > 1:
        raise ValueError("Fee rates must be fractions between 0 and 1")

    def unavailable(status: EconomicsStatus) -> EconomicAssessment:
        return EconomicAssessment(
            status=status,
            sellable=False,
            provider_cost_azn=None,
            payment_fee_azn=None,
            tax_fee_azn=None,
            retry_cost_azn=retry,
            total_cost_azn=None,
            gross_margin_azn=None,
            gross_margin_pct=None,
            minimum_margin_azn=minimum,
        )

    if provider_cost_usd is None and provider_cost_azn is None:
        return unavailable(EconomicsStatus.NEEDS_COMMERCIAL_QUOTE)
    if retail_price_azn is None:
        return unavailable(EconomicsStatus.NEEDS_RETAIL_PRICE)

    retail = _amount(retail_price_azn, "retail_price_azn", positive=True)
    if provider_cost_usd is not None:
        if fx_rate_azn_per_usd is None:
            return unavailable(EconomicsStatus.NEEDS_FX_SNAPSHOT)
        fx = _amount(fx_rate_azn_per_usd, "fx_rate_azn_per_usd", positive=True)
        provider = _amount(provider_cost_usd, "provider_cost_usd") * fx
    else:
        provider = _amount(provider_cost_azn, "provider_cost_azn")

    payment = fixed_payment + retail * payment_rate
    tax = fixed_tax + retail * tax_rate
    total = provider + payment + tax + retry
    margin = retail - total
    sellable = margin >= minimum
    return EconomicAssessment(
        status=EconomicsStatus.SUITABLE if sellable else EconomicsStatus.UNSUITABLE,
        sellable=sellable,
        provider_cost_azn=provider,
        payment_fee_azn=payment,
        tax_fee_azn=tax,
        retry_cost_azn=retry,
        total_cost_azn=total,
        gross_margin_azn=margin,
        gross_margin_pct=margin / retail,
        minimum_margin_azn=minimum,
    )

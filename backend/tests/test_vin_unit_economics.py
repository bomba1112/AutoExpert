from decimal import Decimal

import pytest
from app.services.vin_unit_economics import EconomicsStatus, evaluate


def test_unknown_provider_quote_never_becomes_zero_cost() -> None:
    result = evaluate(
        retail_price_azn="15", fx_rate_azn_per_usd="1.70", minimum_margin_azn="8.50"
    )
    assert result.status is EconomicsStatus.NEEDS_COMMERCIAL_QUOTE
    assert not result.sellable
    assert result.provider_cost_azn is None
    assert result.gross_margin_azn is None


def test_usd_quote_requires_explicit_fx_snapshot() -> None:
    result = evaluate(provider_cost_usd="2", retail_price_azn="15", minimum_margin_azn="8.50")
    assert result.status is EconomicsStatus.NEEDS_FX_SNAPSHOT
    assert not result.sellable
    assert result.gross_margin_azn is None


def test_hypothetical_ten_dollar_provider_is_loss_making_at_15_azn() -> None:
    result = evaluate(
        provider_cost_usd="10",
        retail_price_azn="15",
        fx_rate_azn_per_usd="1.70",
        minimum_margin_azn="8.50",
    )
    assert result.provider_cost_azn == Decimal("17.00")
    assert result.gross_margin_azn == Decimal("-2.00")
    assert result.gross_margin_pct == Decimal("-2.00") / Decimal("15")
    assert result.status is EconomicsStatus.UNSUITABLE
    assert not result.sellable


def test_payment_tax_and_retry_cost_are_all_deducted() -> None:
    result = evaluate(
        provider_cost_usd="2.00",
        retail_price_azn="15.00",
        fx_rate_azn_per_usd="1.70",
        payment_fee_azn="0.30",
        payment_fee_rate="0.02",
        tax_fee_azn="0.50",
        tax_fee_rate="0.01",
        retry_cost_azn="0.35",
        minimum_margin_azn="10.00",
    )
    assert result.payment_fee_azn == Decimal("0.60")
    assert result.tax_fee_azn == Decimal("0.65")
    assert result.total_cost_azn == Decimal("5.00")
    assert result.gross_margin_azn == Decimal("10.00")
    assert result.gross_margin_pct == Decimal("10") / Decimal("15")
    assert result.status is EconomicsStatus.SUITABLE
    assert result.sellable


def test_azn_quote_needs_no_fx_but_insufficient_margin_blocks() -> None:
    result = evaluate(
        provider_cost_azn="7.50", retail_price_azn="15", minimum_margin_azn="8.50"
    )
    assert result.provider_cost_azn == Decimal("7.50")
    assert result.gross_margin_azn == Decimal("7.50")
    assert result.status is EconomicsStatus.UNSUITABLE


def test_ambiguous_cost_currency_and_negative_inputs_are_rejected() -> None:
    with pytest.raises(ValueError, match="exactly one currency"):
        evaluate(
            provider_cost_usd="1",
            provider_cost_azn="1",
            retail_price_azn="15",
            minimum_margin_azn="8.50",
        )
    with pytest.raises(ValueError, match="retry_cost_azn"):
        evaluate(
            provider_cost_azn="1",
            retail_price_azn="15",
            retry_cost_azn="-1",
            minimum_margin_azn="8.50",
        )
    with pytest.raises(ValueError, match="Fee rates"):
        evaluate(
            provider_cost_azn="1",
            retail_price_azn="15",
            payment_fee_rate="1.1",
            minimum_margin_azn="8.50",
        )

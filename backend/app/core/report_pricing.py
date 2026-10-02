from __future__ import annotations

from decimal import Decimal

from app.core.config import get_settings


def configured_report_price(country: str) -> tuple[Decimal | None, str | None]:
    settings = get_settings()
    if country == "AZ":
        return Decimal(str(settings.full_report_price_az_azn)), "AZN"
    return None, None

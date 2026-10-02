from __future__ import annotations

from decimal import Decimal

from app.core.config import get_settings


def configured_vin_price(country: str = "AZ") -> tuple[Decimal | None, str | None]:
    if country != "AZ":
        return None, None
    settings = get_settings()
    return Decimal(str(settings.vin_check_1_price_az_azn)), "AZN"


def configured_product_prices(country: str = "AZ") -> dict[str, Decimal] | None:
    if country != "AZ":
        return None
    settings = get_settings()
    return {
        "MODEL_DOSSIER": Decimal(str(settings.model_dossier_price_az_azn)),
        "VIN_CHECK_1": Decimal(str(settings.vin_check_1_price_az_azn)),
        "VIN_CHECK_3": Decimal(str(settings.vin_check_3_price_az_azn)),
    }

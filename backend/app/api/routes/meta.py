from fastapi import APIRouter

from app.core.config import get_settings
from app.pricing.vin import configured_product_prices
from app.providers.vin import FORD_EXAMPLE_VIN
from app.services.ai_mechanic import enabled as ai_mechanic_enabled
from app.services.catalog_preview import enabled as preview_us_configurations_enabled
from app.services.chat_access import configured_chat_access_policy
from app.services.club import enabled as club_enabled
from app.services.entitlements import enabled as subscription_enabled
from app.services.garage import enabled as garage_enabled
from app.services.listing_opinion import enabled as expert_opinion_enabled
from app.services.us_tech_facts import enabled as us_tech_facts_enabled

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/client-config")
def client_config() -> dict:
    settings = get_settings()
    chat_policy = configured_chat_access_policy()
    qa_mode = settings.environment in {"development", "test"} and settings.demo_mode
    config = {
        "version": "0.8.1",
        "buyer_api_version": 1,
        "catalog_api_version": 1,
        "buyer_languages": ["az", "ru"],
        "concept_products": settings.concept_products if qa_mode else {"active": False},
        "languages": ["az", "ru", "en"],
        "countries": ["AZ", "RU"],
        "prices": {
            "AZ": {
                "full_report": str(settings.full_report_price_az_azn),
                "comparison": str(settings.compare_report_price_az_azn),
                "model_dossier": str(configured_product_prices("AZ")["MODEL_DOSSIER"]),
                "vin_check_1": str(configured_product_prices("AZ")["VIN_CHECK_1"]),
                "vin_check_3": str(configured_product_prices("AZ")["VIN_CHECK_3"]),
                "currency": "AZN",
            },
            "RU": None,
        },
        # A production deployment must never advertise the local fixtures,
        # even if an old environment accidentally leaves demo_mode enabled.
        "qa_mode": qa_mode,
        "demo_mode": qa_mode,
        "vin_demo": {
            "sample_vin": FORD_EXAMPLE_VIN,
            "make": "Ford",
            "model": "Fusion",
            "year": 2019,
            "history_origin": "DEMO",
        }
        if qa_mode
        else None,
        "developer": {
            "enabled": settings.developer_mode and qa_mode,
            "simulate_user_paywall_default": (
                settings.developer_simulate_user_paywall_default and qa_mode
            ),
            "diagnostics_visible": settings.developer_mode and qa_mode,
        },
        "chat": {
            "access_mode": chat_policy.mode,
            "demo_unlimited": settings.chat_demo_unlimited and qa_mode,
            "question_limit": settings.chat_question_limit,
        },
    }
    # Stage C preview: advertised only while the flag is on, so production answers as before.
    if garage_enabled(settings):
        config["garage_v1"] = {"enabled": True}
    if garage_enabled(settings) and ai_mechanic_enabled(settings):
        limit = settings.ai_mechanic_daily_limit
        config["ai_mechanic_v1"] = {"enabled": True, "daily_limit": limit}
    if subscription_enabled(settings):
        config["subscription_v1"] = {"enabled": True}
    if club_enabled(settings):
        config["owners_club_v1"] = {"enabled": True}
    if us_tech_facts_enabled(settings):
        config["us_tech_facts"] = {"enabled": True}
    if expert_opinion_enabled(settings):
        config["expert_opinion_v1"] = {"enabled": True}
    if preview_us_configurations_enabled(settings):
        config["us_configurations_preview"] = {"enabled": True, "years": [2021, 2026]}
    return config

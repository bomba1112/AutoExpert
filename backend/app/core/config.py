from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AUTOEXPERT_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Auto Expert API"
    environment: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./autoexpert.db"
    secret_key: str = "development-only-change-this-secret-key"
    access_token_minutes: int = 60
    admin_email: str = "admin@example.invalid"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8080",
            "https://appassets.autoexpert.local",
        ]
    )
    llm_provider: str = "deterministic"
    payment_provider: str = "mock"
    full_report_price_az_azn: float = 2.99
    compare_report_price_az_azn: float = 6.99
    model_dossier_price_az_azn: float = 2.99
    vin_check_1_price_az_azn: float = 5.00
    vin_check_3_price_az_azn: float = 11.99
    vin_history_minimum_margin_azn: Decimal = Field(default=Decimal("8.50"), ge=0)
    chat_access_mode: Literal[
        "INCLUDED_WITH_UNLOCKED_DOSSIER",
        "LIMITED_QUESTIONS",
        "PREMIUM_UNLIMITED",
        "SUBSCRIPTION",
    ] = "INCLUDED_WITH_UNLOCKED_DOSSIER"
    chat_question_limit: int = Field(default=10, ge=1, le=1000)
    chat_demo_unlimited: bool = True
    demo_mode: bool = True
    # Seeding demo rows when the preview starts is a QA opt-in; the working database
    # stays free of demo data unless AUTOEXPERT_SEED_DEMO_ON_START=true is set.
    seed_demo_on_start: bool = False
    developer_mode: bool = True
    developer_simulate_user_paywall_default: bool = False
    knowledge_data_dir: str = ".localdata"
    knowledge_worker_enabled: bool = False
    knowledge_import_max_records: int = Field(default=10000, ge=1, le=100000)
    knowledge_import_max_bytes: int = 32 * 1024 * 1024
    # US technical facts in the configuration card (next-stage prompt, stage C). Unset: on in
    # development/test (preview), off in production; AUTOEXPERT_SHOW_US_TECH_FACTS overrides.
    show_us_tech_facts: bool | None = None
    # Chinese configuration catalogue card (CN catalogue integration). Unset: on in
    # development/test (preview), off in production; AUTOEXPERT_SHOW_CN_CATALOG overrides.
    show_cn_catalog: bool | None = None
    # US configurations 2021-2026 prepared for publication, shown in the preview catalogue only
    # (owner decision 2026-10-03). Unset: on in development/test; never in production, whatever
    # the value (app/services/catalog_preview.enabled).
    preview_us_configurations: bool | None = None
    turbo_az_authorized_connector_enabled: bool = False
    turbo_az_authorized_connector_credentials: str | None = None
    turbo_az_authorized_connector_permission_reference: str | None = None
    concept_products: dict = Field(
        default_factory=lambda: {
            "active": False,
            "currency": "AZN",
            "technical_minor": 700,
            "history_extension_minor": 1000,
            "combined_minor": 1700,
            "economics": "UNVERIFIED",
            "payments": "SANDBOX_ONLY",
        }
    )

    @model_validator(mode="after")
    def production_secrets_must_be_explicit(self) -> Settings:
        if self.environment == "production" and (
            len(self.secret_key) < 32
            or self.secret_key == "development-only-change-this-secret-key"
            or self.secret_key.startswith("replace-with-")
        ):
            raise ValueError("Production requires an explicit random secret key")
        if self.environment == "production" and self.developer_mode:
            raise ValueError("Developer mode must be disabled in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

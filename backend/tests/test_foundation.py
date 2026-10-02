from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.core.config import Settings
from fastapi.testclient import TestClient
from pydantic import ValidationError


def test_health_and_client_config(client: TestClient) -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "database": "ok"}

    config = client.get("/api/v1/meta/client-config")
    assert config.status_code == 200
    assert config.json()["languages"] == ["az", "ru", "en"]
    assert config.json()["prices"]["AZ"]["full_report"] == "2.99"
    assert config.json()["prices"]["AZ"]["model_dossier"] == "2.99"
    assert config.json()["prices"]["AZ"]["vin_check_1"] == "5.0"
    assert config.json()["prices"]["AZ"]["vin_check_3"] == "11.99"
    assert config.json()["prices"]["RU"] is None
    assert config.json()["chat"] == {
        "access_mode": "INCLUDED_WITH_UNLOCKED_DOSSIER",
        "demo_unlimited": True,
        "question_limit": 10,
    }


def test_auth_password_hash_and_login(client: TestClient) -> None:
    value = {
        "email": "owner@example.com",
        "password": "a-secure-demo-password",
        "preferred_language": "az",
        "country_code": "AZ",
    }
    registered = client.post("/api/v1/auth/register", json=value)
    assert registered.status_code == 201
    assert registered.json()["token_type"] == "bearer"
    assert registered.json()["user"]["preferred_language"] == "az"

    duplicate = client.post("/api/v1/auth/register", json=value)
    assert duplicate.status_code == 409

    logged_in = client.post(
        "/api/v1/auth/login",
        json={"email": value["email"], "password": value["password"]},
    )
    assert logged_in.status_code == 200
    assert logged_in.json()["access_token"]

    rejected = client.post(
        "/api/v1/auth/login",
        json={"email": value["email"], "password": "incorrect-password"},
    )
    assert rejected.status_code == 401


def test_localization_catalogs_have_identical_keys() -> None:
    root = Path(__file__).parents[2] / "apps" / "client" / "lib" / "l10n"
    catalogs = {
        language: json.loads((root / f"app_{language}.arb").read_text(encoding="utf-8"))
        for language in ("az", "ru", "en")
    }
    key_sets = [
        {key for key in catalog if not key.startswith("@@")} for catalog in catalogs.values()
    ]
    assert key_sets[0] == key_sets[1] == key_sets[2]
    assert all(catalog.get("@@locale") == language for language, catalog in catalogs.items())


def test_production_rejects_placeholder_secret() -> None:
    with pytest.raises(ValidationError, match="explicit random secret"):
        Settings(environment="production", _env_file=None)

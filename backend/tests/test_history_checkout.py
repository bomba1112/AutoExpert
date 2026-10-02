from __future__ import annotations

from app.api.routes.history_flow import get_history_provider
from app.main import app
from app.models.history_flow import (
    HistoryAsset,
    HistoryEvent,
    ProviderTransaction,
    ReportEntitlement,
    VehicleHistoryReport,
    VinCheckRequest,
)
from app.providers.history_fixture import FIXTURE_VIN, FixtureHistoryProvider
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

BASE = "/api/v1/vin/history/checks"


def session(client: TestClient) -> dict:
    response = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def start(client: TestClient, headers: dict, vin: str = FIXTURE_VIN):
    return client.post(BASE, headers=headers, json={"vin": vin, "language": "ru"})


def scenario(value: str):
    app.dependency_overrides[get_history_provider] = lambda: FixtureHistoryProvider(value)


def test_vin_validation_unsupported_and_no_history(client: TestClient) -> None:
    headers = session(client)
    assert start(client, headers, "3FA6P0HD0KR114796").status_code == 422
    unsupported = start(client, headers, "1M8GDM9AXKP042788")
    assert unsupported.status_code == 201
    assert unsupported.json()["status"] == "FAILED_FINAL"
    assert unsupported.json()["quote"]["sellable"] is False
    scenario("no_history")
    empty = start(client, headers)
    assert empty.status_code == 201
    assert empty.json()["status"] == "PREFLIGHT_COMPLETE"
    assert empty.json()["preview"]["photo_count"] == 0
    assert empty.json()["quote"]["sellable"] is False
    check_id = empty.json()["check_id"]
    assert (
        client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={}).status_code == 409
    )


def test_preflight_unknown_count_and_failure_states(client: TestClient) -> None:
    headers = session(client)
    scenario("unknown_photos")
    preview = start(client, headers)
    assert preview.json()["preview"]["photo_count"] is None
    assert "events" not in preview.text
    assert "mock-photo-1" not in preview.text
    scenario("timeout")
    other_headers = session(client)
    timeout = start(client, other_headers)
    assert timeout.json()["status"] == "FAILED_RETRYABLE"
    assert timeout.json()["quote"]["sellable"] is False
    scenario("history")
    recovered = start(client, other_headers)
    assert recovered.json()["check_id"] == timeout.json()["check_id"]
    assert recovered.json()["status"] == "AWAITING_PAYMENT"
    scenario("rate_limit")
    third_headers = session(client)
    limited = start(client, third_headers)
    assert limited.json()["status"] == "FAILED_RETRYABLE"


def test_mock_checkout_idempotent_entitled_report_and_assets(
    client: TestClient,
    db_session: Session,
) -> None:
    headers = session(client)
    preview = start(client, headers)
    assert preview.status_code == 201, preview.text
    payload = preview.json()
    assert payload["status"] == "AWAITING_PAYMENT"
    assert payload["preview"]["photo_count"] == 1
    assert payload["quote"]["sellable"] is True
    check_id = payload["check_id"]
    locked = client.get(f"{BASE}/{check_id}/report", headers=headers)
    assert locked.status_code == 402
    outsider = session(client)
    assert client.get(f"{BASE}/{check_id}", headers=outsider).status_code == 404
    assert client.get(f"{BASE}/{check_id}/report", headers=outsider).status_code == 404
    assert client.get(f"{BASE}/{check_id}/assets/guess", headers=headers).status_code == 402
    assert start(client, headers).json()["check_id"] == check_id
    paid = client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    assert paid.status_code == 200, paid.text
    assert paid.json()["status"] == "REPORT_READY"
    assert paid.json()["is_unlocked"] is True
    again = client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    assert again.status_code == 200
    callback = client.post(f"{BASE}/{check_id}/provider/mock/callback", headers=headers)
    assert callback.status_code == 200
    assert db_session.scalar(select(func.count()).select_from(ProviderTransaction)) == 2
    assert db_session.scalar(select(func.count()).select_from(ReportEntitlement)) == 1
    assert db_session.scalar(select(func.count()).select_from(VehicleHistoryReport)) == 1
    assert db_session.scalar(select(func.count()).select_from(HistoryEvent)) == 5
    ru_response = client.get(f"{BASE}/{check_id}/report?language=ru", headers=headers)
    az_response = client.get(f"{BASE}/{check_id}/report?language=az", headers=headers)
    assert ru_response.status_code == 200, ru_response.text
    assert az_response.status_code == 200, az_response.text
    ru, az = ru_response.json(), az_response.json()
    assert ru["mileage_anomaly"] is True
    assert ru["odometer_points"][0]["original_unit"] == "mi"
    assert ru["odometer_points"][0]["mileage_km"] == 48280
    assert ru["asset_ids"] and ru["asset_ids"] == az["asset_ids"]
    assert ru["assets"][0]["id"] == ru["asset_ids"][0]
    assert ru["assets"][0]["event_date"] == "2021-02-01"
    assert ru["assets"][0]["source"] == "local_history_fixture"
    assert ru["assets"][0]["photo_type"] == "WHOLESALE_PHOTO"
    assert az["assets"][0]["photo_type"] == "WHOLESALE_PHOTO"
    assert "WHOLESALE_PHOTO" not in str(ru["sections"])
    assert "WHOLESALE_PHOTO" not in str(az["sections"])
    assert {i["event_id"] for s in ru["sections"] for i in s["items"] if i["event_id"]} == {
        i["event_id"] for s in az["sections"] for i in s["items"] if i["event_id"]
    }
    assert "Обнаружена аномалия" in str(ru["sections"])
    assert "Yürüş qeydlərinin" in str(az["sections"])
    assert "30,000 mi" in str(ru["sections"])
    assert "SALVAGE" in str(az["sections"])
    assert "local_history_fixture" in str(ru["sections"])
    assert "2021-03-01" in str(ru["sections"])
    assert "technical" not in {section["key"] for section in ru["sections"]}
    asset_id = ru["asset_ids"][0]
    assert client.get(f"{BASE}/{check_id}/assets/{asset_id}", headers=outsider).status_code == 404
    image = client.get(f"{BASE}/{check_id}/assets/{asset_id}", headers=headers)
    assert image.status_code == 200
    assert image.headers["cache-control"] == "private, no-store"
    assert b"MOCK PHOTO" in image.content
    assert (
        db_session.scalar(select(HistoryAsset).where(HistoryAsset.id == asset_id)).photo_type
        == "WHOLESALE_PHOTO"
    )


def test_after_payment_retry_and_no_second_charge(client: TestClient, db_session: Session) -> None:
    headers = session(client)
    check_id = start(client, headers).json()["check_id"]
    scenario("post_payment_failure")
    first = client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    assert first.status_code == 200
    assert first.json()["status"] == "FAILED_RETRYABLE"
    assert first.json()["is_unlocked"] is True
    assert client.get(f"{BASE}/{check_id}/report", headers=headers).status_code == 409
    repeated = client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    assert repeated.json()["status"] == "FAILED_RETRYABLE"
    assert db_session.scalar(select(func.count()).select_from(ProviderTransaction)) == 2
    scenario("history")
    recovered = client.post(f"{BASE}/{check_id}/retry", headers=headers)
    assert recovered.json()["status"] == "REPORT_READY"
    assert db_session.scalar(select(func.count()).select_from(ProviderTransaction)) == 2


def test_no_accident_is_not_inferred(client: TestClient) -> None:
    headers = session(client)
    scenario("no_accident")
    check_id = start(client, headers).json()["check_id"]
    client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    report = client.get(f"{BASE}/{check_id}/report", headers=headers).json()
    assert "damage" not in [s["key"] for s in report["sections"]]


def test_real_report_projection_does_not_claim_fixture_source(
    client: TestClient,
    db_session: Session,
) -> None:
    """Projection wording is correct if a future authorized real adapter is added."""
    headers = session(client)
    check_id = start(client, headers).json()["check_id"]
    client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    check = db_session.get(VinCheckRequest, check_id)
    check.is_mock = False
    db_session.commit()
    ru = client.get(f"{BASE}/{check_id}/report?language=ru", headers=headers).json()
    az = client.get(f"{BASE}/{check_id}/report?language=az", headers=headers).json()
    assert "Поставщик истории сообщил 5 событий" in str(ru["sections"])
    assert "Tarixçə provayderi 5 hadisə" in str(az["sections"])
    assert "учебного источника" not in str(ru["sections"])
    assert "Nümunə mənbədə" not in str(az["sections"])


def test_failed_mock_payment_can_be_retried_without_duplicate(
    client: TestClient, db_session: Session
) -> None:
    headers = session(client)
    check_id = start(client, headers).json()["check_id"]
    failed = client.post(
        f"{BASE}/{check_id}/payments/mock", headers=headers, json={"simulate_failure": True}
    )
    assert failed.json()["is_unlocked"] is False
    succeeded = client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    assert succeeded.json()["status"] == "REPORT_READY"
    assert db_session.scalar(select(func.count()).select_from(ReportEntitlement)) == 1
    assert db_session.scalar(select(func.count()).select_from(ProviderTransaction)) == 2


def test_unprofitable_or_unknown_provider_cost_never_offers_payment(client: TestClient) -> None:
    class Expensive(FixtureHistoryProvider):
        def quote(self, vin: str, product: str) -> dict:
            quote = super().quote(vin, product)
            quote["provider_cost_usd"] = "10.00"
            return quote

    class MissingQuote(FixtureHistoryProvider):
        def quote(self, vin: str, product: str) -> dict:
            quote = super().quote(vin, product)
            quote.pop("provider_cost_usd")
            return quote

    app.dependency_overrides[get_history_provider] = lambda: Expensive()
    expensive = start(client, session(client)).json()
    assert expensive["status"] == "PREFLIGHT_COMPLETE"
    assert expensive["quote"]["sellable"] is False
    assert expensive["quote"]["reason"] == "UNSUITABLE"

    app.dependency_overrides[get_history_provider] = lambda: MissingQuote()
    missing = start(client, session(client)).json()
    assert missing["quote"]["retail_price_azn"] is None
    assert missing["quote"]["reason"] == "NEEDS_COMMERCIAL_QUOTE"


def test_percentage_payment_fee_in_provider_quote_blocks_checkout(client: TestClient) -> None:
    class HighFee(FixtureHistoryProvider):
        def quote(self, vin: str, product: str) -> dict:
            quote = super().quote(vin, product)
            quote["payment_fee_rate"] = "0.95"
            return quote

    app.dependency_overrides[get_history_provider] = lambda: HighFee()
    blocked = start(client, session(client)).json()
    assert blocked["status"] == "PREFLIGHT_COMPLETE"
    assert blocked["quote"]["sellable"] is False
    assert blocked["quote"]["reason"] == "UNSUITABLE"


def test_production_never_exposes_fixture_or_mock_payment(client: TestClient) -> None:
    from app.core.config import get_settings

    headers = session(client)
    settings = get_settings()
    old = settings.environment
    settings.environment = "production"
    try:
        assert start(client, headers).status_code == 404
    finally:
        settings.environment = old

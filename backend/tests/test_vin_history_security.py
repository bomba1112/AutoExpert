"""Security and recovery regressions for the local VIN-history checkout.

These tests use only an in-memory database and the deterministic fixture provider.
They never contact a paid history or payment endpoint.
"""

from __future__ import annotations

from collections import Counter

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.routes.history_flow import get_history_provider
from app.core.config import get_settings
from app.main import app
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel, VehicleVariant
from app.models.history_flow import (
    CostLedgerEntry,
    HistoryAsset,
    HistoryEvent,
    ProviderTransaction,
    ReportEntitlement,
    VehicleHistoryReport,
)
from app.providers.history_fixture import FIXTURE_VIN, FixtureHistoryProvider, HistoryProviderError


BASE = "/api/v1/vin/history/checks"


def _user(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _start(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(BASE, headers=headers, json={"vin": FIXTURE_VIN, "language": "ru"})
    assert response.status_code == 201, response.text
    return response.json()["check_id"]


def _count(db: Session, entity: type) -> int:
    return db.scalar(select(func.count()).select_from(entity)) or 0


def test_owner_isolation_covers_every_read_and_mutation_even_when_vin_matches(
    client: TestClient, db_session: Session,
) -> None:
    owner, outsider = _user(client), _user(client)
    owner_check = _start(client, owner)
    outsider_check = _start(client, outsider)
    assert owner_check != outsider_check
    assert [row["check_id"] for row in client.get(BASE, headers=outsider).json()] == [outsider_check]

    forbidden_paths = (
        ("get", f"{BASE}/{owner_check}"),
        ("get", f"{BASE}/{owner_check}/report"),
        ("get", f"{BASE}/{owner_check}/assets/guessed-asset-id"),
        ("post", f"{BASE}/{owner_check}/payments/mock"),
        ("post", f"{BASE}/{owner_check}/retry"),
        ("post", f"{BASE}/{owner_check}/provider/mock/callback"),
    )
    for method, path in forbidden_paths:
        response = getattr(client, method)(path, headers=outsider, **({"json": {}} if "payments" in path else {}))
        assert response.status_code == 404, (method, path, response.text)
    assert _count(db_session, ReportEntitlement) == 0

    paid = client.post(f"{BASE}/{owner_check}/payments/mock", headers=owner, json={})
    assert paid.status_code == 200 and paid.json()["status"] == "REPORT_READY", paid.text
    report = client.get(f"{BASE}/{owner_check}/report", headers=owner).json()
    assert len(report["asset_ids"]) == 1
    asset_id = report["asset_ids"][0]
    assert client.get(f"{BASE}/{owner_check}/assets/{asset_id}", headers=outsider).status_code == 404
    assert client.get(f"{BASE}/{outsider_check}/assets/{asset_id}", headers=outsider).status_code == 402
    assert client.get(f"{BASE}/{owner_check}/report", headers=outsider).status_code == 404


class _HostileAssetProvider(FixtureHistoryProvider):
    """Return private source-only values and an asset without display rights."""

    def preflight(self, vin: str) -> dict:
        result = super().preflight(vin)
        result["photo_count"] = None
        result["internal_provider_note"] = "PRIVATE-PREFLIGHT-MARKER"
        return result

    def get_report(self, provider_report_id: str) -> dict:
        result = super().get_report(provider_report_id)
        result["private_raw_token"] = "PRIVATE-RAW-MARKER"
        result["assets"].append({
            "id": "unlicensed-photo", "event_id": "mock-auction-1",
            "photo_type": "WHOLESALE_PHOTO", "media_type": "image/svg+xml",
            "display_rights_confirmed": False,
            "url": "https://provider.example.invalid/private-asset-token",
        })
        result["assets"][0]["url"] = "https://provider.example.invalid/licensed-origin-token"
        return result

    def get_assets(self, provider_report_id: str) -> dict[str, bytes]:
        return {**super().get_assets(provider_report_id), "unlicensed-photo": b"PRIVATE-IMAGE-BYTES"}


def test_pre_entitlement_and_unlicensed_assets_never_expose_private_content(
    client: TestClient, db_session: Session,
) -> None:
    provider = _HostileAssetProvider()
    app.dependency_overrides[get_history_provider] = lambda: provider
    headers = _user(client)
    check_id = _start(client, headers)

    for response in (
        client.get(BASE, headers=headers),
        client.get(f"{BASE}/{check_id}", headers=headers),
    ):
        assert response.status_code == 200, response.text
        payload = response.text
        for secret in ("PRIVATE-PREFLIGHT-MARKER", "PRIVATE-RAW-MARKER", "private-asset-token", "mock-auction-1"):
            assert secret not in payload
    assert client.get(f"{BASE}/{check_id}", headers=headers).json()["preview"]["photo_count"] is None
    assert client.get(f"{BASE}/{check_id}/report", headers=headers).status_code == 402
    assert client.get(f"{BASE}/{check_id}/assets/unlicensed-photo", headers=headers).status_code == 402

    paid = client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    assert paid.status_code == 200 and paid.json()["status"] == "REPORT_READY", paid.text
    report_response = client.get(f"{BASE}/{check_id}/report", headers=headers)
    assert report_response.status_code == 200
    for secret in ("PRIVATE-RAW-MARKER", "private-asset-token", "licensed-origin-token", "PRIVATE-IMAGE-BYTES"):
        assert secret not in report_response.text
    assert len(report_response.json()["asset_ids"]) == 1
    assert client.get(f"{BASE}/{check_id}/assets/unlicensed-photo", headers=headers).status_code == 404
    assert _count(db_session, HistoryAsset) == 1
    assert "PRIVATE-RAW-MARKER" in db_session.scalar(select(ProviderTransaction).where(
        ProviderTransaction.kind == "REPORT")).raw_payload["private_raw_token"]


class _FailOnceProvider(FixtureHistoryProvider):
    def __init__(self) -> None:
        super().__init__()
        self.purchase_keys: list[str] = []

    def purchase_or_fetch(self, vin: str, product: str, idempotency_key: str) -> dict:
        self.purchase_keys.append(idempotency_key)
        if len(self.purchase_keys) == 1:
            raise HistoryProviderError("PROVIDER_TIMEOUT", retryable=True)
        return super().purchase_or_fetch(vin, product, idempotency_key)


def test_payment_retry_and_provider_callback_are_idempotent_across_requests(
    client: TestClient, db_session: Session,
) -> None:
    provider = _FailOnceProvider()
    app.dependency_overrides[get_history_provider] = lambda: provider
    headers = _user(client)
    check_id = _start(client, headers)

    first = client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    assert first.status_code == 200 and first.json()["status"] == "FAILED_RETRYABLE", first.text
    assert first.json()["is_unlocked"] is True
    assert client.get(f"{BASE}/{check_id}/report", headers=headers).status_code == 409
    assert client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={}).json()["status"] == "FAILED_RETRYABLE"
    assert len(provider.purchase_keys) == 1

    recovered = client.post(f"{BASE}/{check_id}/retry", headers=headers)
    assert recovered.status_code == 200 and recovered.json()["status"] == "REPORT_READY", recovered.text
    assert len(provider.purchase_keys) == 2
    assert len(set(provider.purchase_keys)) == 1
    for _ in range(2):
        assert client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={}).json()["status"] == "REPORT_READY"
        assert client.post(f"{BASE}/{check_id}/provider/mock/callback", headers=headers).json()["status"] == "REPORT_READY"
    # A fresh HTTP client/provider instance must recover from durable DB state.
    app.dependency_overrides[get_history_provider] = lambda: FixtureHistoryProvider()
    with TestClient(app) as restarted_client:
        callback = restarted_client.post(f"{BASE}/{check_id}/provider/mock/callback", headers=headers)
        assert callback.status_code == 200 and callback.json()["status"] == "REPORT_READY", callback.text
        assert restarted_client.get(f"{BASE}/{check_id}/report", headers=headers).status_code == 200
    assert len(provider.purchase_keys) == 2
    assert _count(db_session, ProviderTransaction) == 2
    assert _count(db_session, ReportEntitlement) == 1
    assert {row.kind for row in db_session.scalars(select(CostLedgerEntry))} == {
        "MOCK_RETAIL", "MOCK_PROVIDER_COST",
    }
    assert _count(db_session, CostLedgerEntry) == 2
    assert _count(db_session, VehicleHistoryReport) == 1
    assert _count(db_session, HistoryEvent) == 5


def test_failed_mock_payment_can_be_retried_without_creating_a_second_transaction(
    client: TestClient, db_session: Session,
) -> None:
    headers = _user(client)
    check_id = _start(client, headers)
    failed = client.post(f"{BASE}/{check_id}/payments/mock", headers=headers,
                         json={"simulate_failure": True})
    assert failed.status_code == 200 and failed.json()["is_unlocked"] is False, failed.text
    assert _count(db_session, ProviderTransaction) == 1
    assert _count(db_session, ReportEntitlement) == 0

    recovered = client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    assert recovered.status_code == 200 and recovered.json()["status"] == "REPORT_READY", recovered.text
    assert _count(db_session, ProviderTransaction) == 2  # one payment key and one report key
    assert _count(db_session, ReportEntitlement) == 1
    assert len(list(db_session.scalars(select(ProviderTransaction).where(
        ProviderTransaction.kind == "MOCK_PAYMENT")))) == 1
    assert client.get(f"{BASE}/{check_id}/report", headers=headers).status_code == 200


def test_permanent_post_payment_failure_requires_refund_not_a_second_charge(
    client: TestClient, db_session: Session,
) -> None:
    app.dependency_overrides[get_history_provider] = lambda: FixtureHistoryProvider("post_payment_permanent_failure")
    headers = _user(client)
    check_id = _start(client, headers)
    failed = client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={})
    assert failed.status_code == 200 and failed.json()["status"] == "REFUND_REQUIRED", failed.text
    assert client.get(f"{BASE}/{check_id}/report", headers=headers).status_code == 409
    assert client.post(f"{BASE}/{check_id}/retry", headers=headers).status_code == 409
    assert client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={}).json()["status"] == "REFUND_REQUIRED"
    assert {row.kind for row in db_session.scalars(select(CostLedgerEntry))} == {
        "MOCK_RETAIL", "MOCK_PROVIDER_COST",
    }
    assert _count(db_session, CostLedgerEntry) == 2
    assert _count(db_session, ProviderTransaction) == 2
    assert _count(db_session, VehicleHistoryReport) == 0


def test_production_cannot_read_persisted_mock_checks_reports_or_assets(client: TestClient) -> None:
    headers = _user(client)
    check_id = _start(client, headers)
    assert client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={}).json()["status"] == "REPORT_READY"
    asset_id = client.get(f"{BASE}/{check_id}/report", headers=headers).json()["asset_ids"][0]
    settings = get_settings()
    original = settings.environment
    settings.environment = "production"
    try:
        listed = client.get(BASE, headers=headers)
        assert listed.status_code in {200, 404}, listed.text
        if listed.status_code == 200:
            assert listed.json() == []
        for path in (f"{BASE}/{check_id}", f"{BASE}/{check_id}/report",
                     f"{BASE}/{check_id}/assets/{asset_id}"):
            assert client.get(path, headers=headers).status_code == 404, path
    finally:
        settings.environment = original


def test_internal_epa_candidate_stays_out_and_az_ru_share_fact_snapshot(
    client: TestClient, db_session: Session,
) -> None:
    marker = "PRIVATE_EPA_ONLY_CATALOG_VALUE"
    make = VehicleMake(name="Ford", normalized_name="ford")
    model = VehicleModel(make=make, name="Fusion", normalized_name="fusion")
    generation = VehicleGeneration(model=model, name="EPA research generation", code="EPA", start_year=2019)
    db_session.add(VehicleVariant(
        generation=generation, catalog_key="epa:test-history-isolation", market="USA",
        name=marker, year_from=2019, year_to=2019, engine=marker,
        transmission="Automatic 6-spd", drivetrain="FWD", fuel="Gasoline",
        specifications={"research_only": marker},
    ))
    db_session.commit()

    headers = _user(client)
    check_id = _start(client, headers)
    assert client.post(f"{BASE}/{check_id}/payments/mock", headers=headers, json={}).json()["status"] == "REPORT_READY"
    responses = {language: client.get(f"{BASE}/{check_id}/report?language={language}", headers=headers)
                 for language in ("ru", "az")}
    assert all(response.status_code == 200 for response in responses.values())
    assert all(marker not in response.text for response in responses.values())
    ru, az = (responses[language].json() for language in ("ru", "az"))
    for field in ("check_id", "vin", "status", "vehicle_identity", "mileage_anomaly", "odometer_points", "asset_ids"):
        assert ru[field] == az[field], field
    assert [section["key"] for section in ru["sections"]] == [section["key"] for section in az["sections"]]
    for left, right in zip(ru["sections"], az["sections"]):
        assert [(item["event_id"], item["date"]) for item in left["items"]] == [
            (item["event_id"], item["date"]) for item in right["items"]]
    # Each source event appears in the timeline and exactly one semantic section in both locales.
    assert Counter(item["event_id"] for section in ru["sections"] for item in section["items"] if item["event_id"]) == \
        Counter(item["event_id"] for section in az["sections"] for item in section["items"] if item["event_id"])

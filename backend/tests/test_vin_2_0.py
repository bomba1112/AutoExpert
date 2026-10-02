from __future__ import annotations

from app.core.abbreviations import AbbreviationExplainer
from app.core.vin import VINValidationError, validate_vin
from app.db.seed_demo import seed_autoexpert2_demo
from app.models.enums import EntitlementType, EvidenceCategory, EvidenceStatus
from app.models.evidence import KnownIssue, TechnicalEvidence
from app.models.vehicle_knowledge import (
    AutoExpertChatContext,
    VehicleKnowledgeProfile,
    VINCheck,
    VINEntitlement,
)
from app.providers.us_data import DeterministicUSDataFixtureProvider
from app.providers.vin import DEMO_VIN
from app.services.dossier import build_vehicle_dossier
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

VALID_NO_RECORDS_VIN = "1M8GDM9AXKP042788"


def _session(client: TestClient, language: str = "ru") -> str:
    response = client.post("/api/v1/auth/demo", json={"preferred_language": language})
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _precheck(client: TestClient, token: str, *, vin: str = DEMO_VIN, language: str = "ru"):
    return client.post(
        "/api/v1/vin/precheck",
        json={"vin": vin, "language": language},
        headers=_headers(token),
    )


def test_vin_checksum_normalization_and_forbidden_characters() -> None:
    assert validate_vin(f"  {DEMO_VIN.lower()}  ") == DEMO_VIN
    try:
        validate_vin("4T1B11HK7KU000000")
    except VINValidationError as error:
        assert "checksum" in str(error).casefold()
    else:
        raise AssertionError("invalid checksum was accepted")

    for forbidden in ("I", "O", "Q"):
        vin = f"{forbidden}{DEMO_VIN[1:]}"
        try:
            validate_vin(vin)
        except VINValidationError as error:
            assert "I, O, or Q" in str(error)
        else:
            raise AssertionError(f"forbidden character {forbidden} was accepted")


def test_precheck_returns_safe_locked_dto_without_full_history(
    client: TestClient,
    db_session: Session,
) -> None:
    token = _session(client)
    response = _precheck(client, token, vin=DEMO_VIN.lower())
    assert response.status_code == 201, response.text
    teaser = response.json()
    assert teaser["vin"] == DEMO_VIN
    assert teaser["vehicle"]["make"] == "Toyota"
    assert teaser["vehicle"]["generation"] == "XV70"
    assert teaser["found"] is True
    assert teaser["records_count"] == 3
    assert teaser["photos_count"] == 18
    assert teaser["auctions_count"] == 2
    assert teaser["has_salvage_title"] is True
    assert teaser["odometer_risk"] == "high"
    assert teaser["details_locked"] is True
    assert teaser["can_purchase"] is True
    assert teaser["price"] == "5.0"
    assert teaser["currency"] == "AZN"
    assert teaser["is_demo"] is True
    assert teaser["blurred_preview_data_url"].startswith("data:image/svg+xml;base64,")

    serialized = str(teaser).casefold()
    for forbidden in (
        "timeline",
        'auctions": [',
        "damage_details",
        "odometer_records",
        "sale_price",
        "demo-photo-01",
    ):
        assert forbidden not in serialized

    saved = db_session.scalar(select(VINCheck).where(VINCheck.id == teaser["check_id"]))
    assert saved is not None
    assert len(saved.full_history_payload["photos"]) == 18
    assert len(saved.full_history_payload["timeline"]) == 3

    locked = client.get(f"/api/v1/vin/{teaser['check_id']}", headers=_headers(token))
    assert locked.status_code == 402


def test_vehicle_knowledge_profile_catalog_is_demo_marked(client: TestClient) -> None:
    token = _session(client)
    response = client.get("/api/v1/vin/profiles", headers=_headers(token))
    assert response.status_code == 200
    profiles = response.json()
    assert len(profiles) == 1
    profile = profiles[0]
    assert profile["make"] == "Toyota"
    assert profile["model"] == "Camry"
    assert profile["generation"] == "XV70"
    assert profile["engine_code"] == "A25A-FKS"
    assert profile["transmission"] == "8AT"
    assert profile["is_demo"] is True


def test_no_records_never_offers_or_unlocks_paid_report(
    client: TestClient,
    db_session: Session,
) -> None:
    token = _session(client)
    response = _precheck(client, token, vin=VALID_NO_RECORDS_VIN)
    assert response.status_code == 201, response.text
    teaser = response.json()
    assert teaser["records_count"] == 0
    assert teaser["details_locked"] is True
    assert teaser["can_purchase"] is False
    assert teaser["price"] is None
    assert teaser["currency"] is None
    assert "не предлагаем платный VIN-отчёт" in teaser["no_records_message"]
    assert "не является гарантией отсутствия ДТП" in teaser["caution_message"]

    unlock = client.post(
        f"/api/v1/vin/{teaser['check_id']}/payments/mock",
        json={},
        headers=_headers(token),
    )
    assert unlock.status_code == 409
    assert db_session.scalar(select(func.count(VINEntitlement.id))) == 0


def test_mock_payment_creates_entitlement_and_unlocks_snapshots(
    client: TestClient,
    db_session: Session,
) -> None:
    token = _session(client, "ru")
    teaser = _precheck(client, token).json()
    check_id = teaser["check_id"]

    failed = client.post(
        f"/api/v1/vin/{check_id}/payments/mock",
        json={"simulate_failure": True},
        headers=_headers(token),
    )
    assert failed.status_code == 200
    assert failed.json()["is_unlocked"] is False
    assert db_session.scalar(select(func.count(VINEntitlement.id))) == 0

    unlocked = client.post(
        f"/api/v1/vin/{check_id}/payments/mock",
        json={},
        headers=_headers(token),
    )
    assert unlocked.status_code == 200, unlocked.text
    assert unlocked.json()["status"] == "SUCCEEDED"
    assert unlocked.json()["amount"] == "5.0"
    assert unlocked.json()["entitlement_type"] == "VIN_REPORT_UNLOCKED"
    entitlement = db_session.scalar(select(VINEntitlement))
    assert entitlement is not None
    assert entitlement.entitlement_type == EntitlementType.VIN_REPORT_UNLOCKED

    full = client.get(f"/api/v1/vin/{check_id}", headers=_headers(token))
    assert full.status_code == 200, full.text
    body = full.json()
    assert len(body["history"]["photos"]) == 18
    assert len(body["history"]["auctions"]) == 2
    assert len(body["history"]["timeline"]) == 3
    assert len(body["dossier"]["sections"]) == 17
    for collection in ("timeline", "auctions", "photos", "damage_details", "odometer_records"):
        assert all(item["is_demo"] is True for item in body["history"][collection])
    assert all(item["status"] == "ESTIMATE" for item in body["history"]["auctions"])
    assert all(item["status"] == "ESTIMATE" for item in body["history"]["photos"])
    assert all(item["status"] == "ESTIMATE" for item in body["history"]["odometer_records"])
    assert body["dossier"]["vehicle"]["engine_code"] == "A25A-FKS"
    assert body["sources"][0]["url"].startswith("https://example.invalid/")
    assert body["sources"][0]["usage_status"] == "ACTIVE"
    assert body["is_demo"] is True
    context = db_session.scalar(select(AutoExpertChatContext))
    assert context is not None
    assert context.vin_history_snapshot == body["history"]
    assert context.system_constraints["facts_must_come_from_context"] is True

    saved_teaser = client.get(f"/api/v1/vin/{check_id}/precheck", headers=_headers(token)).json()
    assert saved_teaser["details_locked"] is False
    assert saved_teaser["can_purchase"] is False

    idempotent = client.post(
        f"/api/v1/vin/{check_id}/payments/mock",
        json={},
        headers=_headers(token),
    )
    assert idempotent.json()["status"] == "ALREADY_UNLOCKED"
    assert db_session.scalar(select(func.count(VINEntitlement.id))) == 1


def test_vin_report_ownership_is_enforced(client: TestClient) -> None:
    owner = _session(client)
    other = _session(client)
    teaser = _precheck(client, owner).json()
    check_id = teaser["check_id"]
    client.post(
        f"/api/v1/vin/{check_id}/payments/mock",
        json={},
        headers=_headers(owner),
    )
    for method, path in (
        ("get", f"/api/v1/vin/{check_id}/precheck"),
        ("get", f"/api/v1/vin/{check_id}"),
        ("post", f"/api/v1/vin/{check_id}/payments/mock"),
    ):
        if method == "get":
            response = client.get(path, headers=_headers(other))
        else:
            response = client.post(path, json={}, headers=_headers(other))
        assert response.status_code == 404
    assert client.get("/api/v1/vin/checks", headers=_headers(other)).json() == []


def test_abbreviations_are_explained_once_in_all_languages() -> None:
    expected = {
        "ru": "8AT — 8-ступенчатая автоматическая коробка передач",
        "az": "8AT — 8 pilləli avtomatik sürətlər qutusu",
        "en": "8AT — 8-speed automatic transmission",
    }
    for language, first_use in expected.items():
        glossary = AbbreviationExplainer(language)
        assert glossary.render("8AT") == first_use
        assert glossary.render("8AT") == "8AT"
        assert "—" in glossary.render("TSB")
        assert "—" in glossary.render("A25A-FKS")


def test_dossier_preserves_evidence_status_and_allowed_issue_severity(
    db_session: Session,
) -> None:
    profile_id = seed_autoexpert2_demo(db_session)
    db_session.commit()
    profile = db_session.get(VehicleKnowledgeProfile, profile_id)
    engine = db_session.scalar(
        select(TechnicalEvidence).where(
            TechnicalEvidence.vehicle_variant_id == profile.vehicle_variant_id,
            TechnicalEvidence.category == EvidenceCategory.ENGINE,
        )
    )
    engine.status = EvidenceStatus.ESTIMATE
    issue = db_session.scalar(
        select(KnownIssue).where(KnownIssue.vehicle_variant_id == profile.vehicle_variant_id)
    )
    dossier = build_vehicle_dossier(profile, language="ru", known_issues=[issue])
    sections = {item.key: item for item in dossier.sections}
    assert sections["engine"].claims[0].status == EvidenceStatus.ESTIMATE
    assert sections["weak_points"].known_issues[0].status == issue.status
    assert sections["weak_points"].known_issues[0].severity in {
        "CRITICAL",
        "MEDIUM",
        "MINOR",
    }
    general = sections["general_information"].summary
    assert "A25A-FKS —" in general
    assert "8AT —" in general
    assert "VIN —" in general


def test_us_data_provider_fixture_has_four_separate_demo_surfaces() -> None:
    provider = DeterministicUSDataFixtureProvider()
    assert provider.decode_vin(DEMO_VIN)["is_demo"] is True
    assert provider.recalls(DEMO_VIN)[0]["fixture"] == "recall-shell"
    assert provider.complaints(make="Toyota", model="Camry", year=2019)[0]["is_demo"]
    assert provider.manufacturer_communications(make="Toyota", model="Camry", year=2019)[0][
        "is_demo"
    ]

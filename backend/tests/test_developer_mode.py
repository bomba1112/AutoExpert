from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import Settings, get_settings
from app.db.seed_demo import seed_autoexpert2_ford_demo
from app.models.enums import DataOrigin, ResearchJobStatus
from app.models.research import ResearchJob
from app.models.user import User
from app.models.vehicle_knowledge import VehicleKnowledgeProfile, VINCheck, VINEntitlement
from app.providers.vin import FORD_EXAMPLE_VIN, TOYOTA_DEMO_VIN
from app.services.developer_access import SIMULATE_USER_PAYWALL_HEADER
from app.services.dossier import build_vehicle_dossier
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def _token(client: TestClient, language: str = "ru") -> str:
    response = client.post(
        "/api/v1/auth/demo",
        json={"preferred_language": language},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _headers(token: str, *, simulate_paywall: bool = False) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if simulate_paywall:
        headers[SIMULATE_USER_PAYWALL_HEADER] = "true"
    return headers


def _enable_developer_mode() -> None:
    settings = get_settings()
    settings.developer_mode = True
    settings.developer_simulate_user_paywall_default = False


def _ford_precheck(client: TestClient, token: str, *, simulate_paywall: bool = False) -> dict:
    response = client.post(
        "/api/v1/vin/precheck",
        json={"vin": FORD_EXAMPLE_VIN, "language": "ru", "market": "USA"},
        headers=_headers(token, simulate_paywall=simulate_paywall),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_developer_mode_bypasses_paywall_only_for_resource_owner(
    client: TestClient,
    db_session: Session,
) -> None:
    _enable_developer_mode()
    settings = get_settings()
    original_demo_unlimited = settings.chat_demo_unlimited
    original_limit = settings.chat_question_limit
    settings.chat_demo_unlimited = False
    settings.chat_question_limit = 1
    try:
        owner = _token(client)
        other = _token(client)
        teaser = _ford_precheck(client, owner)

        assert teaser["vin"] == FORD_EXAMPLE_VIN
        assert teaser["vehicle"]["make"] == "Ford"
        assert teaser["vehicle"]["model"] == "Fusion"
        assert teaser["vehicle"]["year"] == 2019
        assert teaser["details_locked"] is False
        assert teaser["can_purchase"] is False
        assert teaser["price"] is None
        assert teaser["currency"] is None
        assert teaser["developer_mode"] is True
        assert teaser["simulate_user_paywall"] is False
        assert TOYOTA_DEMO_VIN not in str(teaser)
        assert db_session.scalar(select(func.count(VINEntitlement.id))) == 0

        check_id = teaser["check_id"]
        report = client.get(
            f"/api/v1/vin/{check_id}",
            headers=_headers(owner),
        )
        assert report.status_code == 200, report.text
        body = report.json()
        assert body["vin"] == FORD_EXAMPLE_VIN
        assert body["history"]["vin"] == FORD_EXAMPLE_VIN
        assert body["vehicle"]["make"] == "Ford"
        assert body["entitlement_type"] == "DEVELOPER_BYPASS"
        assert body["developer_mode"] is True
        assert db_session.scalar(select(func.count(VINEntitlement.id))) == 0

        payment = client.post(
            f"/api/v1/vin/{check_id}/payments/mock",
            json={},
            headers=_headers(owner),
        )
        assert payment.status_code == 409
        assert "Simulate User Paywall" in payment.json()["detail"]

        chat = client.post(
            f"/api/v1/vin/{check_id}/chat/session",
            headers=_headers(owner),
        )
        assert chat.status_code == 201, chat.text
        assert chat.json()["policy"]["unlimited"] is True
        assert chat.json()["policy"]["question_limit"] is None

        for question in ("Что проверить?", "Что ещё проверить?"):
            answer = client.post(
                f"/api/v1/chat/sessions/{chat.json()['session_id']}/messages",
                json={"question": question},
                headers=_headers(owner),
            )
            assert answer.status_code == 201, answer.text

        assert (
            client.get(
                f"/api/v1/vin/{check_id}",
                headers=_headers(other),
            ).status_code
            == 404
        )
        assert (
            client.post(
                f"/api/v1/vin/{check_id}/chat/session",
                headers=_headers(other),
            ).status_code
            == 404
        )
    finally:
        settings.chat_demo_unlimited = original_demo_unlimited
        settings.chat_question_limit = original_limit


def test_simulate_user_paywall_restores_locked_entitlement_flow(
    client: TestClient,
    db_session: Session,
) -> None:
    _enable_developer_mode()
    token = _token(client)
    headers = _headers(token, simulate_paywall=True)
    teaser = _ford_precheck(client, token, simulate_paywall=True)
    check_id = teaser["check_id"]

    assert teaser["details_locked"] is True
    assert teaser["can_purchase"] is True
    assert teaser["price"] == "5.0"
    assert teaser["currency"] == "AZN"
    assert teaser["simulate_user_paywall"] is True
    assert client.get(f"/api/v1/vin/{check_id}", headers=headers).status_code == 402
    assert (
        client.post(
            f"/api/v1/vin/{check_id}/chat/session",
            headers=headers,
        ).status_code
        == 402
    )

    unlocked = client.post(
        f"/api/v1/vin/{check_id}/payments/mock",
        json={},
        headers=headers,
    )
    assert unlocked.status_code == 200, unlocked.text
    assert unlocked.json()["entitlement_type"] == "VIN_REPORT_UNLOCKED"
    assert db_session.scalar(select(func.count(VINEntitlement.id))) == 1

    report = client.get(f"/api/v1/vin/{check_id}", headers=headers)
    assert report.status_code == 200, report.text
    assert report.json()["simulate_user_paywall"] is True
    chat = client.post(f"/api/v1/vin/{check_id}/chat/session", headers=headers)
    assert chat.status_code == 201, chat.text
    assert chat.json()["policy"]["unlimited"] is False
    assert chat.json()["policy"]["question_limit"] == 10


def test_ford_profile_demo_precheck_rejects_toyota_fixture_mixing(
    client: TestClient,
    db_session: Session,
) -> None:
    _enable_developer_mode()
    token = _token(client)
    profile = VehicleKnowledgeProfile(
        vehicle_variant_id=None,
        make="Ford",
        model="Fusion",
        generation="UNRESOLVED",
        production_year_start=2019,
        production_year_end=2019,
        market="USA",
        year=2019,
        engine=None,
        engine_code=None,
        transmission=None,
        drivetrain=None,
        body="sedan",
        fuel=None,
        profile_version="developer-review-test",
        freshness_at=datetime.now(UTC),
        dossier_seed={},
        is_demo=False,
        data_origin=DataOrigin.REAL,
    )
    db_session.add(profile)
    db_session.commit()

    mixed = client.post(
        f"/api/v1/vin/profiles/{profile.id}/demo-precheck",
        json={"language": "ru", "vin": TOYOTA_DEMO_VIN},
        headers=_headers(token),
    )
    assert mixed.status_code == 409

    compatible = client.post(
        f"/api/v1/vin/profiles/{profile.id}/demo-precheck",
        json={"language": "ru", "vin": FORD_EXAMPLE_VIN},
        headers=_headers(token),
    )
    assert compatible.status_code == 201, compatible.text
    teaser = compatible.json()
    assert teaser["vin"] == FORD_EXAMPLE_VIN
    assert teaser["vehicle"]["make"] == "Ford"
    assert teaser["details_locked"] is False
    assert TOYOTA_DEMO_VIN not in str(teaser)


def test_developer_client_config_is_safe_and_production_rejects_flag(
    client: TestClient,
) -> None:
    _enable_developer_mode()
    config = client.get("/api/v1/meta/client-config")
    assert config.status_code == 200
    body = config.json()
    assert body["vin_demo"] == {
        "sample_vin": FORD_EXAMPLE_VIN,
        "make": "Ford",
        "model": "Fusion",
        "year": 2019,
        "history_origin": "DEMO",
    }
    assert body["developer"] == {
        "enabled": True,
        "simulate_user_paywall_default": False,
        "diagnostics_visible": True,
    }
    serialized = config.text.casefold()
    for forbidden in (
        "secret_key",
        "api_key",
        "provider_payload",
        "credentials",
        "password_hash",
    ):
        assert forbidden not in serialized

    try:
        Settings(
            environment="production",
            secret_key="a-secure-production-secret-key-at-least-32-characters",
            developer_mode=True,
            _env_file=None,
        )
    except ValidationError as error:
        assert "Developer mode must be disabled" in str(error)
    else:
        raise AssertionError("production accepted DeveloperMode=true")


def test_completed_research_opens_developer_dossier_without_payment_or_demo_history(
    client: TestClient,
    db_session: Session,
) -> None:
    _enable_developer_mode()
    token = _token(client)
    owner = db_session.scalar(select(User).order_by(User.created_at.desc()))
    assert owner is not None
    profile_id = seed_autoexpert2_ford_demo(db_session)
    profile = db_session.get(VehicleKnowledgeProfile, profile_id)
    assert profile is not None
    dossier = build_vehicle_dossier(profile, language="ru", known_issues=[])
    job = ResearchJob(
        user_id=owner.id,
        vehicle_profile_id=profile.id,
        request_key="developer-hotfix-regression",
        status=ResearchJobStatus.COMPLETE,
        language="ru",
        requested_vehicle={
            "identifier": FORD_EXAMPLE_VIN,
            "vin": FORD_EXAMPLE_VIN,
            "identifier_type": "VIN",
            "market": "USA",
        },
        provider_steps=[],
        completed_capabilities=["vehicle_identity"],
        errors=[],
        resolution_snapshot={},
        dossier_snapshot=dossier.model_dump(mode="json"),
        metrics={},
        cache_hit=False,
        is_demo=False,
    )
    db_session.add(job)
    db_session.commit()

    first = client.post(
        f"/api/v1/research/jobs/{job.id}/developer-dossier",
        headers=_headers(token),
    )
    assert first.status_code == 200, first.text
    check_id = first.json()["check_id"]
    assert db_session.scalar(select(func.count(VINEntitlement.id))) == 0

    second = client.post(
        f"/api/v1/research/jobs/{job.id}/developer-dossier",
        headers=_headers(token),
    )
    assert second.status_code == 200, second.text
    assert second.json()["check_id"] == check_id
    assert db_session.scalar(select(func.count(VINCheck.id))) == 1

    report = client.get(f"/api/v1/vin/{check_id}", headers=_headers(token))
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["vin"] == FORD_EXAMPLE_VIN
    assert body["history"]["timeline"] == []
    assert body["history"]["photos"] == []
    assert body["vin_history_origin"] == "REAL"
    assert body["entitlement_type"] == "DEVELOPER_BYPASS"
    assert db_session.scalar(select(func.count(VINEntitlement.id))) == 0

    chat = client.post(
        f"/api/v1/vin/{check_id}/chat/session",
        headers=_headers(token),
    )
    assert chat.status_code == 201, chat.text
    assert chat.json()["policy"]["unlimited"] is True

    simulated = client.post(
        f"/api/v1/research/jobs/{job.id}/developer-dossier",
        headers=_headers(token, simulate_paywall=True),
    )
    assert simulated.status_code == 409
    assert db_session.scalar(select(func.count(VINEntitlement.id))) == 0


def test_developer_dossier_enforces_ownership_and_missing_resources_are_404(
    client: TestClient,
    db_session: Session,
) -> None:
    _enable_developer_mode()
    owner_token = _token(client)
    owner = db_session.scalar(select(User).order_by(User.created_at.desc()))
    assert owner is not None
    other_token = _token(client)

    profile_id = seed_autoexpert2_ford_demo(db_session)
    profile = db_session.get(VehicleKnowledgeProfile, profile_id)
    assert profile is not None
    dossier = build_vehicle_dossier(profile, language="ru", known_issues=[])
    owned_job = ResearchJob(
        user_id=owner.id,
        vehicle_profile_id=profile.id,
        request_key="developer-hotfix-ownership",
        status=ResearchJobStatus.COMPLETE,
        language="ru",
        requested_vehicle={
            "identifier": FORD_EXAMPLE_VIN,
            "vin": FORD_EXAMPLE_VIN,
            "identifier_type": "VIN",
            "market": "USA",
        },
        provider_steps=[],
        completed_capabilities=["vehicle_identity"],
        errors=[],
        resolution_snapshot={},
        dossier_snapshot=dossier.model_dump(mode="json"),
        metrics={},
        cache_hit=False,
        is_demo=False,
    )
    missing_profile_job = ResearchJob(
        user_id=owner.id,
        vehicle_profile_id=None,
        request_key="developer-hotfix-missing-profile",
        status=ResearchJobStatus.COMPLETE,
        language="ru",
        requested_vehicle={
            "make": "Ford",
            "model": "Fusion",
            "year": 2019,
            "market": "USA",
            "identifier_type": "VIN",
        },
        provider_steps=[],
        completed_capabilities=[],
        errors=[],
        resolution_snapshot={},
        dossier_snapshot=dossier.model_dump(mode="json"),
        metrics={},
        cache_hit=False,
        is_demo=False,
    )
    db_session.add_all([owned_job, missing_profile_job])
    db_session.commit()

    forbidden = client.post(
        f"/api/v1/research/jobs/{owned_job.id}/developer-dossier",
        headers=_headers(other_token),
    )
    assert forbidden.status_code == 404
    assert db_session.scalar(select(func.count(VINCheck.id))) == 0

    nonexistent = client.post(
        "/api/v1/research/jobs/00000000-0000-0000-0000-000000000000/developer-dossier",
        headers=_headers(owner_token),
    )
    assert nonexistent.status_code == 404

    missing_profile = client.post(
        f"/api/v1/research/jobs/{missing_profile_job.id}/developer-dossier",
        headers=_headers(owner_token),
    )
    assert missing_profile.status_code == 404
    assert missing_profile.json()["detail"] == "Vehicle profile not found for this research job"
    assert db_session.scalar(select(func.count(VINCheck.id))) == 0

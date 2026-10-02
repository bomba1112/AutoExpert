from __future__ import annotations

import json
from pathlib import Path

from app.db.seed_demo import seed_demo
from app.models.analysis import Payment
from app.models.analytics import AnalyticsEvent
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def _demo_session(client: TestClient, language: str = "ru") -> tuple[str, str]:
    response = client.post(
        "/api/v1/auth/demo",
        json={"preferred_language": language},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body["access_token"], body["user"]["id"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _analysis_payload(variant_id: str, language: str = "ru") -> dict:
    return {
        "vehicle_variant_id": variant_id,
        "vehicle": {
            "country": "AZ",
            "city": "Baku",
            "make": "Demo Motors",
            "model": "Atlas",
            "generation": "D1",
            "year": 2023,
            "engine": "1.8 Demo Petrol",
            "transmission": "6-speed demo automatic",
            "drivetrain": "FWD",
            "mileage_km": 85_000,
            "price": 22_000,
            "currency": "AZN",
        },
        "usage_profile": {
            "monthly_mileage_km": 1500,
            "city_share": 0.7,
            "poor_roads": True,
            "regular_region_trips": True,
            "mountains": True,
            "unpaved_roads": False,
            "passengers": 4,
            "cargo_need": "normal",
            "economy_priority": 5,
            "reliability_priority": 5,
            "comfort_priority": 4,
            "performance_priority": 2,
            "maintenance_cost_priority": 5,
            "resale_priority": 4,
        },
        "report_language": language,
    }


def _create_preview(
    client: TestClient,
    db_session: Session,
    token: str,
    language: str = "ru",
) -> dict:
    variant_id = seed_demo(db_session)
    response = client.post(
        "/api/v1/analyses/preview",
        json=_analysis_payload(variant_id, language),
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_web_preview_assets_and_locales_are_mobile_ready(client: TestClient) -> None:
    root = client.get("/", follow_redirects=False)
    assert root.status_code in {302, 307}
    assert root.headers["location"] == "/preview/"

    page = client.get("/preview/")
    assert page.status_code == 200
    assert 'name="viewport"' in page.text
    assert "width=device-width" in page.text
    assert 'type="module" src="/preview/app-v2.js?v=' in page.text
    assert page.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]

    stylesheet = client.get("/preview/styles.css")
    assert stylesheet.status_code == 200
    assert "min-height: 54px" in stylesheet.text
    assert "overflow-x: hidden" in stylesheet.text

    app_v2 = client.get("/preview/app-v2.js")
    assert app_v2.status_code == 200
    assert "http://localhost" not in app_v2.text

    api_client = client.get("/preview/api.js")
    assert api_client.status_code == 200
    assert "AUTOEXPERT_API_ROOT" in api_client.text
    assert "Auto Expert service is unavailable" in api_client.text
    assert "http://localhost" not in api_client.text
    assert "http://127.0.0.1" not in api_client.text

    android_origin = "https://appassets.autoexpert.local"
    preflight = client.options(
        "/api/v1/meta/client-config",
        headers={
            "Origin": android_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == android_origin

    android_root = Path(__file__).resolve().parents[2] / "apps" / "android_demo"
    android_manifest = (android_root / "AndroidManifest.xml").read_text(encoding="utf-8")
    android_activity = (
        android_root / "src" / "com" / "autoexpert" / "demo" / "MainActivity.java"
    ).read_text(encoding="utf-8")
    android_build = (android_root / "build.sh").read_text(encoding="utf-8")
    assert 'package="com.autoexpert.demo"' in android_manifest
    assert 'android:targetSdkVersion="35"' in android_manifest
    assert "android.permission.INTERNET" in android_manifest
    assert "appassets.autoexpert.local" in android_activity
    assert "AUTOEXPERT_API_ROOT" in android_activity
    assert "http://127.0.0.1:8000/api/v1" in android_build
    assert "AUTOEXPERT_API_BASE_URL" in android_build
    assert "http://127.0.0.1" not in app_v2.text
    assert "api('/vin/precheck'" in app_v2.text
    assert "api('/research/jobs'" in app_v2.text
    assert "api(`/research/jobs/${jobId}/execute`" in app_v2.text
    assert "identifier_type: identifierType" in app_v2.text
    assert "/variant-selection`" in app_v2.text
    assert "provider.vehicle_variants" in app_v2.text
    assert "profiles/real-pilot" not in app_v2.text
    # A sample VIN comes only from the QA-mode API response, never from the
    # static production-served bundle.
    assert "3FA6P0HD0KR114795" not in app_v2.text
    assert "state.meta?.qa_mode === true" in app_v2.text
    assert "state.meta?.vin_demo?.sample_vin" in app_v2.text
    assert "simulateUserPaywall" in app_v2.text
    assert "configureDeveloperAccess" in app_v2.text
    assert "executeResearchContinuation" in app_v2.text
    assert "developer-dossier" not in app_v2.text
    assert "blurred_preview_data_url" in app_v2.text
    assert 'data-action="chat-start"' in app_v2.text
    assert "api(`/chat/sessions/${sessionId}/messages`" in app_v2.text
    assert "http://localhost" not in app_v2.text

    research_flow = client.get("/preview/research-flow.js")
    assert research_flow.status_code == 200
    assert "DEVELOPER_DOSSIER" in research_flow.text
    assert "SIMULATED_PAYWALL" in research_flow.text
    assert "/research/jobs/${jobId}/developer-dossier" in research_flow.text
    assert "/vin/profiles/${profileId}/demo-precheck" in research_flow.text

    locale_payloads = {}
    for language in ("az", "ru", "en"):
        response = client.get(f"/preview/locales/{language}.json")
        assert response.status_code == 200
        locale_payloads[language] = response.json()
        assert locale_payloads[language]["demoData"]
        assert locale_payloads[language]["checkVehicle"]
        assert locale_payloads[language]["questionsRemaining"]
        assert locale_payloads[language]["vinMethod"]
        assert locale_payloads[language]["unlockHistory"]
        assert locale_payloads[language]["testModeNoCharge"]
        assert locale_payloads[language]["askAutoExpert"]
        assert locale_payloads[language]["groundedOnly"]
        assert locale_payloads[language]["researchStageOfficial"]
        assert locale_payloads[language]["researchStageVariants"]
        assert locale_payloads[language]["chooseVariantTitle"]
        assert locale_payloads[language]["identifierType"]
        assert locale_payloads[language]["automaticResearchNotice"]
        assert locale_payloads[language]["serviceUnavailableTitle"]
        assert locale_payloads[language]["reconnect"]
        assert "evidence items" not in json.dumps(locale_payloads[language]).casefold()
    assert set(locale_payloads["az"]) == set(locale_payloads["ru"])
    assert set(locale_payloads["ru"]) == set(locale_payloads["en"])


def test_demo_sessions_are_isolated_and_catalog_is_database_backed(
    client: TestClient,
    db_session: Session,
) -> None:
    variant_id = seed_demo(db_session)
    token_ru, user_ru = _demo_session(client, "ru")
    token_az, user_az = _demo_session(client, "az")
    token_en, user_en = _demo_session(client, "en")
    assert len({token_ru, token_az, token_en}) == 3
    assert len({user_ru, user_az, user_en}) == 3
    assert db_session.scalar(select(func.count(User.id))) == 3

    catalog = client.get("/api/v1/catalog/options")
    assert catalog.status_code == 200
    payload = catalog.json()
    assert payload["countries"] == [
        {"code": "AZ", "currency": "AZN", "cities": ["Baku"], "is_demo": True}
    ]
    assert payload["variants"][0]["id"] == variant_id
    assert payload["variants"][0]["is_demo"] is True


def test_web_analytics_ingress_is_authenticated_and_allowlisted(
    client: TestClient,
    db_session: Session,
) -> None:
    token, user_id = _demo_session(client)
    unauthenticated = client.post(
        "/api/v1/analytics/events",
        json={"event_name": "app_open", "properties": {}},
    )
    assert unauthenticated.status_code == 401

    accepted = client.post(
        "/api/v1/analytics/events",
        json={"event_name": "app_open", "properties": {"client": "web_preview"}},
        headers=_headers(token),
    )
    assert accepted.status_code == 204
    event = db_session.scalar(select(AnalyticsEvent))
    assert event is not None
    assert event.event_name == "app_open"
    assert event.user_id == user_id
    assert event.properties == {"client": "web_preview"}

    rejected = client.post(
        "/api/v1/analytics/events",
        json={"event_name": "invented_event", "properties": {}},
        headers=_headers(token),
    )
    assert rejected.status_code == 422
    assert db_session.scalar(select(func.count(AnalyticsEvent.id))) == 1


def test_complete_phone_flow_persists_and_enforces_report_ownership(
    client: TestClient,
    db_session: Session,
) -> None:
    owner_token, _ = _demo_session(client)
    other_token, _ = _demo_session(client)
    preview = _create_preview(client, db_session, owner_token)
    report_id = preview["report_id"]

    assert preview["price"] == "2.99"
    assert preview["currency"] == "AZN"
    assert preview["country"] == "AZ"
    assert preview["city"] == "Baku"
    assert preview["is_demo"] is True
    assert preview["pipeline_stages"][-1] == "snapshot_saved"
    assert preview["comparable_count"] >= preview["used_comparable_count"] >= 1

    # A URL refresh loads the immutable snapshot instead of regenerating the report.
    saved_once = client.get(f"/api/v1/reports/{report_id}/preview", headers=_headers(owner_token))
    saved_twice = client.get(f"/api/v1/reports/{report_id}/preview", headers=_headers(owner_token))
    assert saved_once.status_code == saved_twice.status_code == 200
    assert saved_once.json() == saved_twice.json() == preview

    locked = client.get(f"/api/v1/reports/{report_id}", headers=_headers(owner_token))
    assert locked.status_code == 200
    assert locked.json()["is_unlocked"] is False
    assert locked.json()["evidence_bundle"] is None
    assert locked.json()["questions_remaining"] == 3

    locked_question = client.post(
        f"/api/v1/reports/{report_id}/questions",
        json={"question": "Что изменится в горах?"},
        headers=_headers(owner_token),
    )
    assert locked_question.status_code == 402

    failed_payment = client.post(
        f"/api/v1/reports/{report_id}/payments/mock",
        json={"simulate_failure": True},
        headers=_headers(owner_token),
    )
    assert failed_payment.status_code == 200
    assert failed_payment.json()["status"] == "FAILED"
    assert failed_payment.json()["is_unlocked"] is False

    paid = client.post(
        f"/api/v1/reports/{report_id}/payments/mock",
        json={"simulate_failure": False},
        headers=_headers(owner_token),
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "SUCCEEDED"
    assert paid.json()["is_unlocked"] is True
    assert paid.json()["amount"] == "2.99"
    assert db_session.scalar(select(func.count(Payment.id))) == 2

    idempotent = client.post(
        f"/api/v1/reports/{report_id}/payments/mock",
        json={"simulate_failure": False},
        headers=_headers(owner_token),
    )
    assert idempotent.status_code == 200
    assert idempotent.json()["status"] == "ALREADY_UNLOCKED"
    assert db_session.scalar(select(func.count(Payment.id))) == 2

    unlocked = client.get(f"/api/v1/reports/{report_id}", headers=_headers(owner_token))
    assert unlocked.status_code == 200
    detail = unlocked.json()
    assert detail["evidence_bundle"] is not None
    assert detail["calculated_data"] is not None
    assert len(detail["generated_sections"]["sections"]) == 15
    assert detail["generated_sections"]["inspection_notice"]

    reports = client.get("/api/v1/reports", headers=_headers(owner_token))
    assert reports.status_code == 200
    assert [item["id"] for item in reports.json()] == [report_id]
    assert reports.json()[0]["is_unlocked"] is True

    for method, path, body in (
        ("get", f"/api/v1/reports/{report_id}", None),
        ("get", f"/api/v1/reports/{report_id}/preview", None),
        ("post", f"/api/v1/reports/{report_id}/payments/mock", {}),
        ("post", f"/api/v1/reports/{report_id}/questions", {"question": "test"}),
    ):
        if method == "get":
            response = client.get(path, headers=_headers(other_token))
        else:
            response = client.post(path, json=body, headers=_headers(other_token))
        assert response.status_code == 404
    assert client.get("/api/v1/reports", headers=_headers(other_token)).json() == []


def test_three_successful_followup_questions_use_saved_report_context(
    client: TestClient,
    db_session: Session,
) -> None:
    token, _ = _demo_session(client, "ru")
    preview = _create_preview(client, db_session, token, "ru")
    report_id = preview["report_id"]
    unlock = client.post(
        f"/api/v1/reports/{report_id}/payments/mock",
        json={},
        headers=_headers(token),
    )
    assert unlock.status_code == 200

    questions = [
        "А если я каждую неделю езжу в горы?",
        "Стоит ли брать по этой цене?",
        "Что проверить при таком пробеге?",
    ]
    remaining = [2, 1, 0]
    answers = []
    for question, expected_remaining in zip(questions, remaining, strict=True):
        response = client.post(
            f"/api/v1/reports/{report_id}/questions",
            json={"question": question},
            headers=_headers(token),
        )
        assert response.status_code == 200, response.text
        assert response.json()["questions_remaining"] == expected_remaining
        answers.append(response.json()["item"]["answer"])

    assert "FWD" in answers[0]
    assert "медиана" in answers[1]
    assert "физичес" in answers[2].casefold()

    exhausted = client.post(
        f"/api/v1/reports/{report_id}/questions",
        json={"question": "Четвёртый вопрос"},
        headers=_headers(token),
    )
    assert exhausted.status_code == 409

    restored = client.get(f"/api/v1/reports/{report_id}", headers=_headers(token))
    assert restored.status_code == 200
    assert restored.json()["questions_remaining"] == 0
    assert [item["question"] for item in restored.json()["questions"]] == questions


def test_locale_files_are_valid_and_have_identical_contract() -> None:
    locale_root = Path(__file__).resolve().parents[2] / "apps" / "web_preview" / "locales"
    payloads = {
        language: json.loads((locale_root / f"{language}.json").read_text(encoding="utf-8"))
        for language in ("az", "ru", "en")
    }
    assert set(payloads["az"]) == set(payloads["ru"]) == set(payloads["en"])
    assert payloads["az"]["languageTitle"] == "Dili seçin"
    assert "язык" in payloads["ru"]["languageTitle"].casefold()
    assert "language" in payloads["en"]["languageTitle"].casefold()

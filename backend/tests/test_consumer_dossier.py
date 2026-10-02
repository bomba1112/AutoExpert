from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from types import SimpleNamespace

import httpx
from app.api.routes.research import get_provider_registry
from app.main import app
from app.models.enums import Sentiment
from app.models.evidence import TechnicalEvidence
from app.providers.official_nhtsa import OfficialHTTPClient
from app.providers.vin import FORD_EXAMPLE_VIN
from app.review_engine.engine import OwnerFeedbackEngine
from app.services.dossier_synthesis import _risk_key, localized_component
from app.services.provider_registry import default_provider_registry
from app.services.research_pipeline import _owner_observations
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

RAW_RECALL_TEXT = (
    "RAW UNIQUE ENGLISH RECALL PARAGRAPH: the hydraulic unit may fail without warning."
)


def test_official_complaints_merge_component_aliases_without_double_counting():
    rows = [
        SimpleNamespace(
            id=str(index),
            material_identity_key=material,
            owner_identity_key=None,
            topic=component,
            component=component,
            sentiment=Sentiment.NEGATIVE,
            summary="Reported issue",
            source_id="official",
            mileage_km=None,
            observed_at=None,
            is_demo=False,
        )
        for index, (material, component) in enumerate(
            [
                ("complaint-1", "ENGINE"),
                ("complaint-1", "ENGINE AND ENGINE COOLING"),
                ("complaint-2", "ENGINE AND ENGINE COOLING"),
                ("complaint-3", "POWER TRAIN"),
            ]
        )
    ]
    aggregation = OwnerFeedbackEngine().aggregate(
        _owner_observations(rows, normalize_components=True)
    )
    assert aggregation.unique_material_count == 3
    assert [(topic.topic, topic.material_mentions) for topic in aggregation.topics] == [
        ("engine", 2),
        ("powertrain", 1),
    ]


def test_recall_risk_does_not_mistake_installation_for_engine_stall():
    assert _risk_key("Improperly installed camera may increase crash risk.") == "risk_crash"
    assert _risk_key("Engine may stall and increase crash risk.") == "risk_stall"
    assert localized_component("BACK OVER PREVENTION:DISPLAY FUNCTION", "ru") == "Обзорность"


def test_researched_dossier_chat_retains_inspection_actions_and_owner_source_separation(
    client: TestClient,
    db_session: Session,
) -> None:
    from app.core.config import get_settings
    from app.models.vehicle_knowledge import AutoExpertChatSession

    get_settings().developer_mode = True
    app.dependency_overrides[get_provider_registry] = lambda: _registry([])
    try:
        token = _token(client)
        headers = {"Authorization": f"Bearer {token}"}
        for language, question, expected in (
            ("ru", "Что проверить перед покупкой?", "антиблокировочной"),
            ("az", "Almazdan əvvəl nəyi yoxlamaq?", "bloklanmasının"),
            ("en", "What to check before purchase?", "anti-lock"),
        ):
            job = _execute(client, token, language)
            access = client.post(
                f"/api/v1/research/jobs/{job['id']}/developer-dossier",
                headers=headers,
            )
            assert access.status_code == 200
            chat = client.post(
                f"/api/v1/vin/{access.json()['check_id']}/chat/session",
                headers=headers,
            )
            assert chat.status_code == 201
            answer = client.post(
                f"/api/v1/chat/sessions/{chat.json()['session_id']}/messages",
                json={"question": question},
                headers=headers,
            )
            assert answer.status_code == 201, answer.text
            assert expected in answer.json()["message"]["content"]
            assert answer.json()["message"]["status"] == "NEEDS_INSPECTION"
            saved = db_session.get(AutoExpertChatSession, chat.json()["session_id"])
            assert saved.context_snapshot["owner_feedback"]["status"] == "INSUFFICIENT_DATA"
    finally:
        app.dependency_overrides.clear()


def _ford_transport(calls: list[str]) -> httpx.MockTransport:
    archive = _ford_communication_archive()

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        path = request.url.path
        if "DecodeVinValues" in path:
            return httpx.Response(
                200,
                json={
                    "Count": 1,
                    "Results": [
                        {
                            "VIN": FORD_EXAMPLE_VIN,
                            "Make": "FORD",
                            "Model": "Fusion",
                            "ModelYear": "2019",
                            "Series": "SE",
                            "Trim": "SE",
                            "EngineModel": "GTDI",
                            "DisplacementL": "1.5",
                            "EngineCylinders": "4",
                            "EngineConfiguration": "In-Line",
                            "EngineHP": "181",
                            "TransmissionSpeeds": "6",
                            "TransmissionStyle": "Automatic",
                            "DriveType": "FWD/Front-Wheel Drive",
                            "BodyClass": "Sedan/Saloon",
                            "FuelTypePrimary": "Gasoline",
                            "VehicleType": "PASSENGER CAR",
                            "PlantCountry": "MEXICO",
                            "ErrorCode": "0",
                            "ErrorText": "0 - VIN decoded clean.",
                        }
                    ],
                },
            )
        if "/SafetyRatings/modelyear/" in path:
            return httpx.Response(200, json={"Count": 0, "Results": []})
        if "recallsByVehicle" in path:
            return httpx.Response(
                200,
                json={
                    "Count": 1,
                    "results": [
                        {
                            "NHTSACampaignNumber": "19V000999",
                            "Manufacturer": "Ford Motor Company",
                            "ReportReceivedDate": "01/01/2019",
                            "Component": "SERVICE BRAKES, HYDRAULIC",
                            "Summary": RAW_RECALL_TEXT,
                            "Consequence": "A loss of braking can increase the risk of a crash.",
                            "Remedy": "Dealers will inspect and replace the affected unit.",
                            "Notes": "Applicability must be checked by VIN.",
                            "Make": "FORD",
                            "Model": "FUSION",
                            "ModelYear": 2019,
                        }
                    ],
                },
            )
        if "complaintsByVehicle" in path:
            return httpx.Response(
                200,
                json={
                    "count": 3,
                    "results": [
                        {
                            "odiNumber": "110001",
                            "dateOfIncident": "01/01/2020",
                            "components": "POWER TRAIN",
                            "summary": "Owner alleged hesitation.",
                            "crash": False,
                            "fire": False,
                            "numberOfInjuries": 0,
                            "numberOfDeaths": 0,
                        },
                        {
                            "odiNumber": "110002",
                            "dateOfIncident": "02/01/2020",
                            "components": "POWER TRAIN",
                            "summary": "Owner alleged delayed response.",
                            "crash": False,
                            "fire": False,
                            "numberOfInjuries": 0,
                            "numberOfDeaths": 0,
                        },
                        {
                            "odiNumber": "110003",
                            "dateOfIncident": "03/01/2020",
                            "components": "SERVICE BRAKES",
                            "summary": "Owner alleged a brake warning.",
                            "crash": False,
                            "fire": False,
                            "numberOfInjuries": 0,
                            "numberOfDeaths": 0,
                        },
                    ],
                },
            )
        if "MFR_COMMS_RECEIVED_" in path and path.endswith(".zip"):
            return httpx.Response(200, content=archive)
        return httpx.Response(404, json={"error": "unexpected fixture URL"})

    return httpx.MockTransport(handler)


def _ford_communication_archive() -> bytes:
    output = io.StringIO()
    fields = [
        "Make",
        "Model",
        "Model Year",
        "NHTSA ID Number",
        "TSB/Document ID",
        "Mfr Communication Date",
        "Communication Type",
        "NHTSA Components",
        "Summary",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    rows = [
        {
            "Make": "FORD",
            "Model": "FUSION",
            "Model Year": "2019",
            "NHTSA ID Number": "101",
            "TSB/Document ID": "SSM-50001",
            "Mfr Communication Date": "05/01/2019",
            "Communication Type": "Technical Service Bulletin",
            "NHTSA Components": "POWER TRAIN",
            "Summary": "Some vehicles may exhibit hesitation during acceleration.",
        },
        {
            "Make": "FORD",
            "Model": "FUSION",
            "Model Year": "2019",
            "NHTSA ID Number": "102",
            "TSB/Document ID": "SSM-50001",
            "Mfr Communication Date": "05/01/2019",
            "Communication Type": "Technical Service Bulletin",
            "NHTSA Components": "POWER TRAIN",
            "Summary": "Some vehicles may exhibit hesitation during acceleration.",
        },
        {
            "Make": "FORD",
            "Model": "FUSION",
            "Model Year": "2019",
            "NHTSA ID Number": "103",
            "TSB/Document ID": "SSM-EMPTY",
            "Mfr Communication Date": "06/01/2019",
            "Communication Type": "Manufacturer Communication",
            "NHTSA Components": "",
            "Summary": "",
        },
    ]
    writer.writerows(rows)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("MFR_COMMS.csv", output.getvalue())
    return payload.getvalue()


def _registry(calls: list[str]):  # noqa: ANN202
    client = httpx.Client(transport=_ford_transport(calls), trust_env=False)
    http = OfficialHTTPClient(client=client, max_attempts=1, min_interval_seconds=0)
    return default_provider_registry(http=http)


def _token(client: TestClient) -> str:
    response = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"})
    assert response.status_code == 201
    return response.json()["access_token"]


def _execute(client: TestClient, token: str, language: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/v1/research/jobs",
        json={
            "vehicle": {
                "identifier": FORD_EXAMPLE_VIN,
                "identifier_type": "VIN",
                "market": "USA",
            },
            "language": language,
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    executed = client.post(
        f"/api/v1/research/jobs/{created.json()['id']}/execute",
        headers=headers,
    )
    assert executed.status_code == 200, executed.text
    return executed.json()


def test_ford_vin_consumer_dossier_synthesizes_provider_records(
    client: TestClient,
    db_session: Session,
) -> None:
    calls: list[str] = []
    app.dependency_overrides[get_provider_registry] = lambda: _registry(calls)
    token = _token(client)
    result = _execute(client, token, "ru")

    assert result["profile"]["make"] == "Ford"
    assert result["profile"]["model"] == "Fusion"
    assert result["profile"]["trim"] == "SE"
    assert result["profile"]["engine_code"] == "GTDI"
    assert "1.5L" in result["profile"]["engine"]
    assert result["profile"]["transmission"] == "6-speed Automatic"
    assert result["profile"]["drivetrain"] == "FWD/Front-Wheel Drive"
    assert result["profile"]["body"] == "Sedan/Saloon"

    sections = {item["key"]: item for item in result["dossier"]["sections"]}
    rendered_sections = str(result["dossier"]["sections"])
    assert RAW_RECALL_TEXT not in rendered_sections
    assert "component not specified" not in rendered_sections
    assert "summary not provided in the bulk record" not in rendered_sections
    assert "Front-Wheel Drive" not in rendered_sections
    assert "Sedan/Saloon" not in rendered_sections

    suspension = sections["suspension"]
    assert suspension["is_empty"] is True
    assert suspension["claims"] == []
    assert suspension["summary"] == "Данные пока не подтверждены."

    recalls = sections["recalls_tsb"]["claims"]
    assert [item["kind"] for item in recalls].count("manufacturer_communication") == 1
    recall = next(item for item in recalls if item["kind"] == "recall")
    assert recall["heading"] == "Отзывная кампания NHTSA 19V000999"
    assert "Тормозная система" in recall["text"]
    assert "риск ДТП" in recall["why_it_matters"]
    assert "этому VIN" in recall["what_to_check"]

    owner = sections["owner_experience"]
    assert "Независимая выборка опыта владельцев пока не подключена" in owner["summary"]
    assert all(item["heading"] == "Жалобы в официальной базе" for item in owner["claims"])
    assert all("вероятность поломки" in item["text"] for item in owner["claims"])
    assert all("%" not in item["text"] for item in owner["claims"])
    assert sections["weak_points"]["known_issues"] == []

    low_information = list(
        db_session.scalars(
            select(TechnicalEvidence).where(
                TechnicalEvidence.title == "Manufacturer Communication SSM-EMPTY"
            )
        )
    )
    assert len(low_information) == 1
    assert low_information[0].conditions["information_quality"] == "LOW"
    assert RAW_RECALL_TEXT in " ".join(db_session.scalars(select(TechnicalEvidence.statement)))
    app.dependency_overrides.clear()


def test_recall_synthesis_is_localized_in_ru_az_en(client: TestClient) -> None:
    calls: list[str] = []
    app.dependency_overrides[get_provider_registry] = lambda: _registry(calls)
    token = _token(client)
    expected = {
        "ru": ("Отзывная кампания", "Тормозная система", "Проверьте применимость"),
        "az": ("geri çağırma kampaniyası", "Əyləc sistemi", "Kampaniyanın məhz"),
        "en": ("recall campaign", "Brake system", "Check whether the campaign"),
    }
    for language, words in expected.items():
        result = _execute(client, token, language)
        section = next(
            item for item in result["dossier"]["sections"] if item["key"] == "recalls_tsb"
        )
        claim = next(item for item in section["claims"] if item["kind"] == "recall")
        rendered = " ".join(
            str(claim.get(key) or "")
            for key in ("heading", "text", "why_it_matters", "what_to_check", "applicability")
        )
        assert all(word in rendered for word in words)
        assert RAW_RECALL_TEXT not in rendered
    app.dependency_overrides.clear()


def test_exact_vin_identity_takes_priority_over_make_model_year_hints(
    client: TestClient,
) -> None:
    calls: list[str] = []
    app.dependency_overrides[get_provider_registry] = lambda: _registry(calls)
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/v1/research/jobs",
        json={
            "vehicle": {
                "identifier": FORD_EXAMPLE_VIN,
                "identifier_type": "VIN",
                "market": "USA",
                "make": "Toyota",
                "model": "Camry",
                "year": 2018,
            },
            "language": "ru",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    executed = client.post(
        f"/api/v1/research/jobs/{created.json()['id']}/execute",
        headers=headers,
    )
    assert executed.status_code == 200, executed.text
    profile = executed.json()["profile"]
    assert (profile["make"], profile["model"], profile["year"]) == (
        "Ford",
        "Fusion",
        2019,
    )
    decode_urls = [url for url in calls if "DecodeVinValues" in url]
    assert len(decode_urls) == 1
    assert "modelyear=" not in decode_urls[0].casefold()
    app.dependency_overrides.clear()


def test_consumer_ui_hides_internal_source_metadata_but_keeps_dev_provenance() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "apps/web_preview/app-v2.js").read_text(encoding="utf-8")
    source_card = script.split("function sourceCard(source)", 1)[1].split(
        "function consumerSourceTitle", 1
    )[0]
    assert "source.source_tier" not in source_card
    assert "source.confidence" not in source_card
    assert "<code>${esc(source.url)}</code>" not in source_card
    assert "consumerSourcePurpose" in source_card
    diagnostics = script.split("function reportDeveloperDiagnostics", 1)[1].split(
        "async function renderReports", 1
    )[0]
    assert "source.source_type" in diagnostics
    assert "source.source_tier" in diagnostics
    assert "source.confidence" in diagnostics
    assert "source.url" in diagnostics
    assert "section.is_empty" in script

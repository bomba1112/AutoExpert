from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from app import models  # noqa: F401
from app.api.routes.research import get_provider_registry
from app.core.vehicle_identifiers import VehicleIdentifierValidator
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import (
    DataOrigin,
    EvidenceStatus,
    ResearchJobStatus,
    VariantResolutionStatus,
    VehicleIdentifierType,
)
from app.models.evidence import KnownIssue, OwnerEvidence, SourceRecord, TechnicalEvidence
from app.models.research import ProviderCacheEntry, ResearchJob
from app.models.vehicle_knowledge import VehicleKnowledgeProfile
from app.providers.official_nhtsa import OfficialHTTPClient
from app.schemas.research import VehicleResearchRequest
from app.services.provider_registry import default_provider_registry
from app.services.provider_router import ProviderRouter
from app.services.real_data_quality import RealDataQualityError
from app.services.research_pipeline import _validate_identity
from app.services.variant_resolver import VehicleVariantResolver
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker


def _official_transport(
    calls: list[str],
    *,
    variants: list[dict] | None = None,
    fail_capability: str | None = None,
) -> httpx.MockTransport:
    communication_zip = _communication_archive()

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        path = request.url.path
        if fail_capability == "owner_complaints" and "complaintsByVehicle" in path:
            return httpx.Response(503, json={"error": "temporarily unavailable"})
        if "DecodeVinValues" in path:
            return httpx.Response(
                200,
                json={
                    "Count": 1,
                    "Results": [
                        {
                            "VIN": "4T1B11HK8KU000000",
                            "Make": "TOYOTA",
                            "Model": "CAMRY",
                            "ModelYear": "2019",
                            "EngineModel": "",
                            "DisplacementL": "",
                            "TransmissionSpeeds": "",
                            "TransmissionStyle": "",
                            "DriveType": "",
                            "BodyClass": "Sedan/Saloon",
                            "FuelTypePrimary": "Gasoline",
                            "VehicleType": "PASSENGER CAR",
                            "ErrorCode": "0",
                            "ErrorText": (
                                "0 - VIN decoded clean. Check Digit (9th position) is correct"
                            ),
                        }
                    ],
                },
            )
        if "GetModelsForMakeYear" in path:
            return httpx.Response(
                200,
                json={
                    "Count": 1,
                    "Results": [
                        {
                            "Make_ID": 448,
                            "Make_Name": "TOYOTA",
                            "Model_ID": 2469,
                            "Model_Name": "Camry",
                        }
                    ],
                },
            )
        if "/SafetyRatings/modelyear/" in path:
            return httpx.Response(
                200,
                json={
                    "Count": len(variants or [1]),
                    "Results": variants
                    or [
                        {
                            "VehicleId": 11934,
                            "VehicleDescription": "2019 Toyota Camry 2.5L 4 DR FWD",
                        }
                    ],
                },
            )
        if "recallsByVehicle" in path:
            return httpx.Response(
                200,
                json={
                    "Count": 1,
                    "results": [
                        {
                            "NHTSACampaignNumber": "20V682000",
                            "Manufacturer": "Toyota Motor Engineering & Manufacturing",
                            "ReportReceivedDate": "11/04/2020",
                            "Component": "FUEL SYSTEM, GASOLINE:DELIVERY:FUEL PUMP",
                            "Summary": "The low-pressure fuel pump may stop operating.",
                            "Consequence": "An engine stall can increase crash risk.",
                            "Remedy": "Dealers replace the fuel pump assembly.",
                            "Notes": "Check applicability by VIN.",
                            "Make": "TOYOTA",
                            "Model": "CAMRY",
                            "ModelYear": "2019",
                        }
                    ],
                },
            )
        if "complaintsByVehicle" in path:
            return httpx.Response(
                200,
                json={
                    "count": 2,
                    "results": [
                        {
                            "odiNumber": 11111111,
                            "dateOfIncident": "01/10/2020",
                            "components": "POWER TRAIN",
                            "summary": "Owner alleged hesitation from a stop.",
                            "crash": False,
                            "fire": False,
                            "numberOfInjuries": 0,
                            "numberOfDeaths": 0,
                        },
                        {
                            "odiNumber": 22222222,
                            "dateOfIncident": "03/12/2021",
                            "components": "SERVICE BRAKES",
                            "summary": "Owner alleged reduced brake assist.",
                            "crash": False,
                            "fire": False,
                            "numberOfInjuries": 0,
                            "numberOfDeaths": 0,
                        },
                    ],
                },
            )
        if "MFR_COMMS_RECEIVED_" in path and path.endswith(".zip"):
            return httpx.Response(200, content=communication_zip)
        return httpx.Response(404, json={"error": "unexpected test URL"})

    return httpx.MockTransport(handler)


def _communication_archive() -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "Make",
            "Model",
            "Model Year",
            "NHTSA ID Number",
            "TSB/Document ID",
            "Mfr Communication Date",
            "Communication Type",
            "NHTSA Components",
            "Summary",
        ],
    )
    writer.writeheader()
    writer.writerow(
        {
            "Make": "TOYOTA",
            "Model": "CAMRY",
            "Model Year": "2019",
            "NHTSA ID Number": "10169403",
            "TSB/Document ID": "T-SB-0152-19",
            "Mfr Communication Date": "11/01/2019",
            "Communication Type": "Technical Service Bulletin",
            "NHTSA Components": "POWER TRAIN",
            "Summary": "Some vehicles may exhibit hesitation from a slow roll.",
        }
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("MFR_COMMS.csv", output.getvalue())
    return buffer.getvalue()


def _registry(
    calls: list[str],
    *,
    variants: list[dict] | None = None,
    fail_capability: str | None = None,
):  # noqa: ANN202
    client = httpx.Client(
        transport=_official_transport(
            calls,
            variants=variants,
            fail_capability=fail_capability,
        ),
        trust_env=False,
    )
    http = OfficialHTTPClient(
        client=client,
        max_attempts=2,
        min_interval_seconds=0,
    )
    return default_provider_registry(http=http, include_depth=False)


def _token(client: TestClient) -> str:
    response = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"})
    assert response.status_code == 201
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _request() -> dict:
    return {
        "vehicle": {
            "make": "Toyota",
            "model": "Camry",
            "year": 2019,
            "market": "USA",
            "engine_hint": "2.5",
        },
        "language": "ru",
    }


def test_automatic_profile_build_and_process_restart_reuse(tmp_path: Path) -> None:
    database_path = tmp_path / "automatic-research.sqlite3"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    calls: list[str] = []
    registry = _registry(calls)

    def override_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_provider_registry] = lambda: registry
    try:
        with session_factory() as before:
            assert before.scalar(select(func.count(VehicleKnowledgeProfile.id))) == 0

        with TestClient(app) as first_process:
            token = _token(first_process)
            created = first_process.post(
                "/api/v1/research/jobs",
                json=_request(),
                headers=_headers(token),
            )
            assert created.status_code == 201, created.text
            executed = first_process.post(
                f"/api/v1/research/jobs/{created.json()['id']}/execute",
                headers=_headers(token),
            )
            assert executed.status_code == 200, executed.text
            first = executed.json()
            assert first["status"] == ResearchJobStatus.COMPLETE
            assert first["cache_hit"] is False
            assert first["profile"]["data_origin"] == DataOrigin.REAL
            assert first["profile"]["make"] == "Toyota"
            assert first["profile"]["model"] == "Camry"
            assert first["profile"]["generation"] == "UNRESOLVED"
            assert first["resolution"]["unresolved_fields"]
            assert len(first["dossier"]["sections"]) == 16
            assert first["metrics"] == {
                "api_requests": 7,
                "sources_created": 5,
                "evidence_created": 6,
                "profile_reused": False,
                "research_time_seconds": first["metrics"]["research_time_seconds"],
            }
            assert len(calls) == 7

        # A new application client represents a backend process restart. The database
        # file and token survive; no provider call is permitted on the second request.
        with TestClient(app) as second_process:
            second_job = second_process.post(
                "/api/v1/research/jobs",
                json=_request(),
                headers=_headers(token),
            )
            second = second_process.post(
                f"/api/v1/research/jobs/{second_job.json()['id']}/execute",
                headers=_headers(token),
            ).json()
            assert second["status"] == ResearchJobStatus.COMPLETE
            assert second["cache_hit"] is True
            assert second["profile_id"] == first["profile_id"]
            assert second["metrics"]["api_requests"] == 0
            assert second["metrics"]["profile_reused"] is True
            assert len(calls) == 7

        with session_factory() as after:
            profile = after.get(VehicleKnowledgeProfile, first["profile_id"])
            assert profile is not None
            assert profile.dossier_seed["build_method"] == "AUTOMATIC_RESEARCH"
            assert profile.dossier_seed["manual_seed_used"] is False
            assert profile.engine_code is None
            assert profile.transmission is None
            assert all(not source.is_demo for source in profile.sources)
            assert all(not evidence.is_demo for evidence in profile.evidence)
            assert after.scalar(select(func.count(SourceRecord.id))) == 5
            assert after.scalar(select(func.count(TechnicalEvidence.id))) == 6
            assert after.scalar(select(func.count(OwnerEvidence.id))) == 2
            assert after.scalar(select(func.count(KnownIssue.id))) == 0
            assert after.scalar(select(func.count(ProviderCacheEntry.id))) == 5
            assert after.scalar(select(func.count(ResearchJob.id))) == 2
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_research_job_is_owner_scoped(client: TestClient) -> None:
    calls: list[str] = []
    app.dependency_overrides[get_provider_registry] = lambda: _registry(calls)
    first = _token(client)
    second = _token(client)
    job = client.post(
        "/api/v1/research/jobs",
        json=_request(),
        headers=_headers(first),
    ).json()
    assert (
        client.get(
            f"/api/v1/research/jobs/{job['id']}",
            headers=_headers(second),
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/research/jobs/{job['id']}/execute",
            headers=_headers(second),
        ).status_code
        == 404
    )


def test_provider_failure_creates_no_profile_or_fabricated_evidence(client: TestClient) -> None:
    def unavailable(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=httpx.Request("GET", "https://offline"))

    http = OfficialHTTPClient(
        client=httpx.Client(transport=httpx.MockTransport(unavailable), trust_env=False),
        max_attempts=2,
        min_interval_seconds=0,
    )
    app.dependency_overrides[get_provider_registry] = lambda: default_provider_registry(http=http)
    token = _token(client)
    job = client.post(
        "/api/v1/research/jobs",
        json=_request(),
        headers=_headers(token),
    ).json()
    response = client.post(
        f"/api/v1/research/jobs/{job['id']}/execute",
        headers=_headers(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == ResearchJobStatus.FAILED
    assert payload["profile"] is None
    assert payload["dossier"] is None
    assert payload["errors"]


def test_registry_exposes_free_cost_and_provider_capabilities(client: TestClient) -> None:
    calls: list[str] = []
    app.dependency_overrides[get_provider_registry] = lambda: _registry(calls)
    token = _token(client)
    response = client.get("/api/v1/research/providers", headers=_headers(token))
    assert response.status_code == 200
    providers = response.json()
    assert {item["id"] for item in providers} == {
        "nhtsa_vpic",
        "nhtsa_safety_ratings_variants",
        "nhtsa_recalls",
        "nhtsa_complaints",
        "nhtsa_manufacturer_communications",
    }
    assert all(item["cost_model"] == "FREE" for item in providers)
    assert all(item["requires_api_key"] is False for item in providers)


def test_router_caches_normalized_capabilities_without_duplicate_requests(
    db_session: Session,
) -> None:
    calls: list[str] = []
    registry = _registry(calls)
    request = VehicleResearchRequest.model_validate(_request()["vehicle"])
    first = ProviderRouter(db_session, registry).fetch(
        request,
        ["vehicle_identity", "recalls", "owner_complaints", "manufacturer_communications"],
    )
    assert len(calls) == 6
    second = ProviderRouter(db_session, registry).fetch(
        request,
        ["vehicle_identity", "recalls", "owner_complaints", "manufacturer_communications"],
    )
    assert len(calls) == 6
    assert all(not item.from_cache for item in first)
    assert all(item.from_cache for item in second)
    assert all(item.api_requests == 0 for item in second)


def test_quality_gate_rejects_contradictory_official_identity() -> None:
    request = VehicleResearchRequest.model_validate(_request()["vehicle"])
    records = [
        {"make": "Toyota", "model": "Camry", "model_year": 2019},
        {"make": "Toyota", "model": "Corolla", "model_year": 2019},
    ]
    try:
        _validate_identity(request, records)
    except RealDataQualityError as error:
        assert "contradictory" in str(error)
    else:
        raise AssertionError("Contradictory identities passed the quality gate")


def test_owner_complaints_remain_allegations_not_confirmed_issues(
    client: TestClient,
) -> None:
    calls: list[str] = []
    app.dependency_overrides[get_provider_registry] = lambda: _registry(calls)
    token = _token(client)
    job = client.post(
        "/api/v1/research/jobs",
        json=_request(),
        headers=_headers(token),
    ).json()
    result = client.post(
        f"/api/v1/research/jobs/{job['id']}/execute",
        headers=_headers(token),
    ).json()
    owner_section = next(
        item for item in result["dossier"]["sections"] if item["key"] == "owner_experience"
    )
    assert all(claim["status"] == EvidenceStatus.ESTIMATE for claim in owner_section["claims"])
    assert "ломается у" not in str(owner_section)
    weak_points = next(
        item for item in result["dossier"]["sections"] if item["key"] == "weak_points"
    )
    assert weak_points["known_issues"] == []


def test_usa_identifier_strategy_accepts_valid_vin_and_rejects_check_digit() -> None:
    valid = VehicleIdentifierValidator().validate(
        "4T1B11HK8KU000000",
        market="USA",
        identifier_type=VehicleIdentifierType.VIN,
    )
    assert valid.check_digit_applied is True
    assert valid.strategy == "NORTH_AMERICA_VIN"
    with pytest.raises(ValueError, match="checksum"):
        VehicleIdentifierValidator().validate(
            "4T1B11HK7KU000000",
            market="USA",
            identifier_type=VehicleIdentifierType.VIN,
        )


def test_korean_vin_is_not_rejected_by_north_american_checksum() -> None:
    result = VehicleIdentifierValidator().validate(
        "KLABA76BDJB723118",
        market="Korea",
        identifier_type=VehicleIdentifierType.VIN,
    )
    assert result.value == "KLABA76BDJB723118"
    assert result.market == "KOREA"
    assert result.check_digit_applied is False


def test_japanese_chassis_and_frame_identifier_types_are_supported() -> None:
    validator = VehicleIdentifierValidator()
    for identifier_type in (
        VehicleIdentifierType.CHASSIS_NUMBER,
        VehicleIdentifierType.FRAME_NUMBER,
    ):
        result = validator.validate(
            "ZN6-0123456",
            market="Japan",
            identifier_type=identifier_type,
        )
        assert result.value == "ZN6-0123456"
        assert result.strategy == "JAPAN_VIN_OR_FRAME"


def test_variant_resolver_returns_resolved_candidate_without_promoting_hint() -> None:
    request = VehicleResearchRequest(
        make="Toyota", model="Camry", year=2019, market="USA", engine_hint="2.5"
    )
    records = [
        {
            "candidate_id": "official:2.5",
            "label": "2019 Toyota Camry 2.5L 4 DR FWD",
            "engine": "2.5L",
            "drivetrain": "FWD",
            "market": "USA",
            "confidence": "HIGH",
            "evidence_ids": ["official:2.5"],
        }
    ]
    result = VehicleVariantResolver().resolve(
        request,
        [{"make": "Toyota", "model": "Camry", "model_year": 2019}],
        records,
    )
    assert result["status"] == VariantResolutionStatus.RESOLVED
    assert result["engine_candidates"] == ["2.5L"]
    assert result["selected_candidate_id"] == "official:2.5"


def test_variant_resolver_returns_ambiguous_and_keeps_unsupported_hint_unconfirmed() -> None:
    request = VehicleResearchRequest(
        make="Toyota", model="Camry", year=2019, market="USA", engine_hint="diesel"
    )
    records = [
        {
            "candidate_id": "official:2.5",
            "label": "Camry 2.5L",
            "engine": "2.5L",
            "market": "USA",
            "confidence": "HIGH",
        },
        {
            "candidate_id": "official:3.5",
            "label": "Camry 3.5L",
            "engine": "3.5L",
            "market": "USA",
            "confidence": "HIGH",
        },
    ]
    result = VehicleVariantResolver().resolve(
        request,
        [{"make": "Toyota", "model": "Camry", "model_year": 2019}],
        records,
    )
    assert result["status"] == VariantResolutionStatus.AMBIGUOUS
    assert set(result["engine_candidates"]) == {"2.5L", "3.5L"}
    assert "diesel" not in result["engine_candidates"]
    assert any("not promoted" in note for note in result["notes"])


def test_ambiguous_selection_resumes_same_job_and_uses_cache(client: TestClient) -> None:
    calls: list[str] = []
    variants = [
        {"VehicleId": 1, "VehicleDescription": "2019 Toyota Camry 2.5L 4 DR FWD"},
        {"VehicleId": 2, "VehicleDescription": "2019 Toyota Camry 3.5L 4 DR FWD"},
        {"VehicleId": 3, "VehicleDescription": "2019 Toyota Camry Hybrid 4 DR FWD"},
    ]
    app.dependency_overrides[get_provider_registry] = lambda: _registry(calls, variants=variants)
    token = _token(client)
    value = _request()
    value["vehicle"]["engine_hint"] = None
    created = client.post("/api/v1/research/jobs", json=value, headers=_headers(token)).json()
    first = client.post(
        f"/api/v1/research/jobs/{created['id']}/execute", headers=_headers(token)
    ).json()
    assert first["status"] == ResearchJobStatus.PARTIAL
    assert first["resolution"]["status"] == VariantResolutionStatus.AMBIGUOUS
    assert first["resolution"]["needs_user_selection"] is True
    assert first["profile"] is None
    calls_after_first = len(calls)

    candidate_id = first["resolution"]["candidates"][1]["id"]
    selected = client.post(
        f"/api/v1/research/jobs/{created['id']}/variant-selection",
        json={"candidate_id": candidate_id},
        headers=_headers(token),
    )
    assert selected.status_code == 200
    assert selected.json()["id"] == created["id"]
    completed = client.post(
        f"/api/v1/research/jobs/{created['id']}/execute", headers=_headers(token)
    ).json()
    assert completed["status"] == ResearchJobStatus.COMPLETE
    assert completed["resolution"]["selected_candidate_id"] == candidate_id
    assert completed["profile"]["engine"] == "3.5L"
    assert len(calls) == calls_after_first
    assert all(step["from_cache"] for step in completed["provider_steps"])


def test_variant_selection_preserves_job_ownership(client: TestClient) -> None:
    calls: list[str] = []
    variants = [
        {"VehicleId": 1, "VehicleDescription": "Camry 2.5L"},
        {"VehicleId": 2, "VehicleDescription": "Camry 3.5L"},
    ]
    app.dependency_overrides[get_provider_registry] = lambda: _registry(calls, variants=variants)
    owner = _token(client)
    stranger = _token(client)
    value = _request()
    value["vehicle"]["engine_hint"] = None
    job = client.post("/api/v1/research/jobs", json=value, headers=_headers(owner)).json()
    result = client.post(
        f"/api/v1/research/jobs/{job['id']}/execute", headers=_headers(owner)
    ).json()
    candidate = result["resolution"]["candidates"][0]["id"]
    denied = client.post(
        f"/api/v1/research/jobs/{job['id']}/variant-selection",
        json={"candidate_id": candidate},
        headers=_headers(stranger),
    )
    assert denied.status_code == 404


def test_korean_identifier_research_is_partial_without_wrong_market_provider(
    client: TestClient,
) -> None:
    calls: list[str] = []
    app.dependency_overrides[get_provider_registry] = lambda: _registry(calls)
    token = _token(client)
    created = client.post(
        "/api/v1/research/jobs",
        json={
            "vehicle": {
                "identifier": "KLABA76BDJB723118",
                "identifier_type": "VIN",
                "market": "KOREA",
            },
            "language": "ru",
        },
        headers=_headers(token),
    )
    assert created.status_code == 201, created.text
    result = client.post(
        f"/api/v1/research/jobs/{created.json()['id']}/execute",
        headers=_headers(token),
    ).json()
    assert result["status"] == ResearchJobStatus.PARTIAL
    assert result["resolution"]["status"] == VariantResolutionStatus.INSUFFICIENT_DATA
    assert result["profile"] is None
    assert calls == []


def test_partial_provider_failure_keeps_confirmed_profile(client: TestClient) -> None:
    calls: list[str] = []
    app.dependency_overrides[get_provider_registry] = lambda: _registry(
        calls, fail_capability="owner_complaints"
    )
    token = _token(client)
    created = client.post("/api/v1/research/jobs", json=_request(), headers=_headers(token)).json()
    result = client.post(
        f"/api/v1/research/jobs/{created['id']}/execute", headers=_headers(token)
    ).json()
    assert result["status"] == ResearchJobStatus.PARTIAL
    assert result["profile"] is not None
    assert result["dossier"] is not None
    complaint = next(
        step for step in result["provider_steps"] if step["capability"] == "owner_complaints"
    )
    assert complaint["status"] == "FAILED"
    assert complaint["records_count"] == 0


def test_variant_provider_normalizes_and_caches_official_labels(
    db_session: Session,
) -> None:
    calls: list[str] = []
    registry = _registry(calls)
    request = VehicleResearchRequest.model_validate(_request()["vehicle"])
    first = ProviderRouter(db_session, registry).fetch(request, ["vehicle_variants"])[0]
    second = ProviderRouter(db_session, registry).fetch(request, ["vehicle_variants"])[0]
    assert first.http_status == 200
    assert first.records[0]["engine"] == "2.5L"
    assert first.records[0]["drivetrain"] == "FWD"
    assert second.from_cache is True
    assert second.api_requests == 0
    assert len(calls) == 1


def test_usa_vin_only_request_builds_profile_from_decoded_identity(
    client: TestClient,
) -> None:
    calls: list[str] = []
    app.dependency_overrides[get_provider_registry] = lambda: _registry(calls)
    token = _token(client)
    created = client.post(
        "/api/v1/research/jobs",
        json={
            "vehicle": {
                "identifier": "4T1B11HK8KU000000",
                "identifier_type": "VIN",
                "market": "USA",
            },
            "language": "en",
        },
        headers=_headers(token),
    )
    assert created.status_code == 201, created.text
    result = client.post(
        f"/api/v1/research/jobs/{created.json()['id']}/execute",
        headers=_headers(token),
    ).json()
    assert result["status"] == ResearchJobStatus.COMPLETE
    assert result["profile"]["make"] == "Toyota"
    assert result["profile"]["model"] == "Camry"
    assert result["profile"]["year"] == 2019
    assert result["resolution"]["status"] == VariantResolutionStatus.RESOLVED
    assert result["profile"]["engine_code"] is None
    assert result["profile"]["transmission"] is None
    assert result["dossier"] is not None
    assert any("DecodeVinValues" in url for url in calls)

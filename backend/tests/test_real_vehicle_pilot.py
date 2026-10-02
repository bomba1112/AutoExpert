from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from app.db.seed_real_camry import seed_real_camry
from app.models.enums import DataOrigin, EvidenceStatus, SourceTier
from app.models.evidence import KnownIssue, OwnerEvidence
from app.models.vehicle_knowledge import VehicleKnowledgeProfile
from app.providers.us_data import NHTSAUSDataProvider
from app.review_engine.engine import OwnerFeedbackEngine
from app.schemas.reviews import OwnerObservation
from app.schemas.vin import DossierClaim
from app.services.dossier import build_vehicle_dossier
from app.services.real_data_quality import validate_real_profile
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session


def _token(client: TestClient, language: str = "ru") -> str:
    response = client.post("/api/v1/auth/demo", json={"preferred_language": language})
    assert response.status_code == 201
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _real_profile(db: Session) -> VehicleKnowledgeProfile:
    profile_id = seed_real_camry(db)
    profile = db.get(VehicleKnowledgeProfile, profile_id)
    assert profile is not None
    return profile


def _dossier(db: Session, profile: VehicleKnowledgeProfile, language: str = "ru"):
    issues = list(
        db.scalars(
            select(KnownIssue).where(KnownIssue.vehicle_variant_id == profile.vehicle_variant_id)
        )
    )
    owners = list(
        db.scalars(
            select(OwnerEvidence).where(
                OwnerEvidence.vehicle_variant_id == profile.vehicle_variant_id
            )
        )
    )
    observations = [
        OwnerObservation(
            id=item.id,
            material_identity_key=item.material_identity_key,
            owner_identity_key=item.owner_identity_key,
            topic=item.topic,
            component=item.component,
            sentiment=item.sentiment,
            summary=item.summary,
            source_id=item.source_id,
            mileage_km=item.mileage_km,
            is_demo=item.is_demo,
        )
        for item in owners
    ]
    aggregation = OwnerFeedbackEngine().aggregate(observations)
    dossier = build_vehicle_dossier(
        profile,
        language=language,
        known_issues=issues,
        owner_feedback=aggregation,
        owner_source_ids=list(dict.fromkeys(item.source_id for item in owners)),
    )
    return dossier, issues, owners, aggregation


def test_real_profile_contains_no_demo_sources_or_evidence(db_session: Session) -> None:
    profile = _real_profile(db_session)
    assert profile.data_origin == DataOrigin.REAL
    assert profile.is_demo is False
    assert len(profile.sources) == 9
    assert all(item.data_origin == DataOrigin.REAL and not item.is_demo for item in profile.sources)
    assert all(
        item.data_origin == DataOrigin.REAL and not item.is_demo for item in profile.evidence
    )
    assert {item.source_tier for item in profile.sources} == {
        SourceTier.A,
        SourceTier.B,
        SourceTier.C,
    }


def test_confirmed_important_claim_requires_source_and_evidence() -> None:
    with pytest.raises(ValidationError):
        DossierClaim(text="unsupported", status=EvidenceStatus.CONFIRMED)


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class _FakeClient:
    def __init__(self, payload: dict | None = None, *, fail: bool = False) -> None:
        self.payload = payload or {}
        self.fail = fail
        self.calls = 0

    def get(self, url: str) -> _FakeResponse:
        self.calls += 1
        if self.fail:
            raise httpx.ConnectError("offline", request=httpx.Request("GET", url))
        return _FakeResponse(self.payload)


def test_nhtsa_recall_normalization_and_cache() -> None:
    client = _FakeClient(
        {
            "Count": 1,
            "results": [
                {
                    "NHTSACampaignNumber": "20V682000",
                    "Manufacturer": "Toyota Motor Engineering & Manufacturing",
                    "ReportReceivedDate": "04/11/2020",
                    "Component": "FUEL SYSTEM, GASOLINE:DELIVERY:FUEL PUMP",
                    "Summary": "The low-pressure fuel pump may fail.",
                    "Consequence": "The engine can stall.",
                    "Remedy": "Dealers replace the fuel pump assembly.",
                    "Notes": "Verify the VIN.",
                    "Make": "TOYOTA",
                    "Model": "CAMRY",
                    "ModelYear": "2019",
                }
            ],
        }
    )
    provider = NHTSAUSDataProvider(client=client)
    first = provider.recalls_by_vehicle(make="TOYOTA", model="CAMRY", year=2019)
    second = provider.recalls_by_vehicle(make="TOYOTA", model="CAMRY", year=2019)
    assert first.status == EvidenceStatus.CONFIRMED
    assert first.records[0]["campaign_number"] == "20V682000"
    assert first.records[0]["data_origin"] == DataOrigin.REAL
    assert second.from_cache is True
    assert client.calls == 1


def test_nhtsa_failure_returns_insufficient_data_without_fabrication() -> None:
    provider = NHTSAUSDataProvider(client=_FakeClient(fail=True))
    result = provider.complaints(make="TOYOTA", model="CAMRY", year=2019)
    assert result.status == EvidenceStatus.INSUFFICIENT_DATA
    assert result.records == []
    assert "unavailable" in result.error


def test_owner_pilot_deduplicates_and_never_confirms_weak_evidence(
    db_session: Session,
) -> None:
    profile = _real_profile(db_session)
    _, _, owners, aggregation = _dossier(db_session, profile)
    duplicate = OwnerObservation(
        id="mirror",
        material_identity_key=owners[0].material_identity_key,
        owner_identity_key=owners[0].owner_identity_key,
        topic=owners[0].topic,
        component=owners[0].component,
        sentiment=owners[0].sentiment,
        summary=owners[0].summary,
        source_id=owners[0].source_id,
        is_demo=False,
    )
    base = [
        OwnerObservation(
            id=item.id,
            material_identity_key=item.material_identity_key,
            owner_identity_key=item.owner_identity_key,
            topic=item.topic,
            component=item.component,
            sentiment=item.sentiment,
            summary=item.summary,
            source_id=item.source_id,
            is_demo=False,
        )
        for item in owners
    ]
    deduped = OwnerFeedbackEngine().aggregate([*base, duplicate])
    assert aggregation.unique_material_count == 10
    assert deduped.unique_material_count == 10
    assert deduped.duplicate_count == 1
    assert not any(item.is_demo for item in profile.evidence)
    # Owner aggregation is deliberately not a CONFIRMED fact source.
    assert all(item.issue_type == "OWNER_ALLEGATION" for item in owners)


def test_camry_profile_resolution_and_real_dossier_quality(db_session: Session) -> None:
    profile = _real_profile(db_session)
    dossier, issues, owners, _ = _dossier(db_session, profile)
    assert profile.make == "Toyota"
    assert profile.model == "Camry"
    assert profile.generation == "XV70"
    assert profile.engine_code == "A25A-FKS"
    assert profile.variant.transmission_code == "UB80E"
    assert len(dossier.sections) == 16
    assert len(issues) == 4
    assert len(owners) == 10
    quality = validate_real_profile(profile, dossier=dossier)
    assert quality.sources == 9
    assert quality.confirmed_evidence == 18
    assert quality.recalls == 6
    assert quality.manufacturer_communications == 1
    assert quality.dossier_sections_with_real_data == 16
    owner_section = next(item for item in dossier.sections if item.key == "owner_experience")
    assert "изученных материалов" in owner_section.claims[0].text
    assert "ломается у" not in owner_section.model_dump_json()


def test_real_dossier_localizes_abbreviations_in_ru_az_en(db_session: Session) -> None:
    profile = _real_profile(db_session)
    expected = {
        "ru": "8AT — 8-ступенчат",
        "az": "8AT — 8 pilləli",
        "en": "8AT — 8-speed",
    }
    for language, wording in expected.items():
        dossier, _, _, _ = _dossier(db_session, profile, language)
        assert wording in dossier.model_dump_json()


def test_real_model_dossier_is_visibly_separated_from_demo_vin_history(
    client: TestClient,
) -> None:
    token = _token(client)
    profile = client.post("/api/v1/vin/profiles/real-pilot", headers=_headers(token))
    assert profile.status_code == 201, profile.text
    assert profile.json()["data_origin"] == "REAL"
    teaser = client.post(
        f"/api/v1/vin/profiles/{profile.json()['id']}/demo-precheck",
        json={"language": "ru"},
        headers=_headers(token),
    )
    assert teaser.status_code == 201, teaser.text
    assert teaser.json()["is_demo"] is True
    assert teaser.json()["vehicle"]["data_origin"] == "REAL"
    check_id = teaser.json()["check_id"]
    assert client.get(f"/api/v1/vin/{check_id}", headers=_headers(token)).status_code == 402
    unlock = client.post(
        f"/api/v1/vin/{check_id}/payments/mock",
        json={},
        headers=_headers(token),
    )
    assert unlock.status_code == 200
    report = client.get(f"/api/v1/vin/{check_id}", headers=_headers(token)).json()
    assert report["vin_history_origin"] == "DEMO"
    assert report["dossier_origin"] == "REAL"
    assert report["history"]["data_origin"] == "DEMO"
    assert report["dossier"]["vehicle"]["data_origin"] == "REAL"
    assert {item["data_origin"] for item in report["sources"]} == {"DEMO", "REAL"}


def test_grounded_chat_uses_real_camry_source_ids(client: TestClient) -> None:
    token = _token(client, "ru")
    profile = client.post("/api/v1/vin/profiles/real-pilot", headers=_headers(token)).json()
    teaser = client.post(
        f"/api/v1/vin/profiles/{profile['id']}/demo-precheck",
        json={"language": "ru"},
        headers=_headers(token),
    ).json()
    check_id = teaser["check_id"]
    client.post(f"/api/v1/vin/{check_id}/payments/mock", json={}, headers=_headers(token))
    chat = client.post(f"/api/v1/vin/{check_id}/chat/session", headers=_headers(token)).json()
    for question in (
        "Какой здесь двигатель?",
        "Что известно про коробку?",
        "Какие слабые места подтверждены?",
        "Что проверить перед покупкой?",
        "Какие recalls найдены?",
        "Откуда эта информация?",
    ):
        response = client.post(
            f"/api/v1/chat/sessions/{chat['session_id']}/messages",
            json={"question": question},
            headers=_headers(token),
        )
        assert response.status_code == 201, response.text
        message = response.json()["message"]
        assert message["sources"]
        assert any(item["data_origin"] == "REAL" for item in message["sources"])
        assert all(
            not item["url"].startswith("https://example.invalid") for item in message["sources"]
        )


def test_stage3_source_retrieval_and_freshness_dates_are_preserved(db_session: Session) -> None:
    profile = _real_profile(db_session)
    assert all(item.retrieved_at.date().isoformat() == "2026-09-14" for item in profile.sources)
    assert profile.freshness_at.date() == datetime(2026, 9, 14, tzinfo=UTC).date()


def test_real_seed_manifest_matches_quality_report(db_session: Session) -> None:
    profile = _real_profile(db_session)
    dossier, issues, owners, _ = _dossier(db_session, profile)
    quality = validate_real_profile(profile, dossier=dossier)
    manifest_path = (
        Path(__file__).resolve().parents[2] / "data" / "seed" / "real_camry_2019_us_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    counts = manifest["quality_counts"]
    assert manifest["data_origin"] == "REAL"
    assert counts == {
        "real_sources": quality.sources,
        "confirmed_evidence_items": quality.confirmed_evidence,
        "known_issues": len(issues),
        "owner_materials": len(owners),
        "recalls": quality.recalls,
        "manufacturer_communications": quality.manufacturer_communications,
        "dossier_sections_with_real_data": quality.dossier_sections_with_real_data,
        "dossier_sections_total": quality.dossier_sections_total,
    }

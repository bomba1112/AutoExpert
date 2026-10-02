from __future__ import annotations

import pytest
from app.db.seed_demo import seed_demo
from app.models.analysis import Report
from app.models.evidence import OwnerEvidence, TechnicalEvidence
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "a-secure-test-password",
            "preferred_language": "ru",
            "country_code": "AZ",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _payload(variant_id: str) -> dict:
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
            "price": "22000",
            "currency": "AZN",
        },
        "usage_profile": {
            "monthly_mileage_km": 1500,
            "city_share": 0.7,
            "poor_roads": True,
            "regular_region_trips": True,
            "mountains": True,
            "passengers": 4,
            "cargo_need": "normal",
            "economy_priority": 5,
            "reliability_priority": 5,
            "comfort_priority": 4,
            "performance_priority": 2,
            "maintenance_cost_priority": 5,
            "resale_priority": 4,
        },
        "report_language": "ru",
    }


def test_pipeline_persists_immutable_grounded_snapshot_and_demo_flag(
    client: TestClient, db_session: Session
) -> None:
    variant_id = seed_demo(db_session)
    token = _register(client, "first@example.com")
    response = client.post(
        "/api/v1/analyses/preview",
        json=_payload(variant_id),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    preview = response.json()
    assert preview["is_demo"] is True
    assert preview["price"] == "2.99"
    assert preview["local_market_status"] == "ESTIMATE"

    report = db_session.scalar(select(Report).where(Report.id == preview["report_id"]))
    assert report is not None
    assert report.evidence_bundle["vehicle"]["is_demo"] is True
    assert report.evidence_bundle["market_analysis"]["excluded_outlier_count"] == 1
    assert report.evidence_bundle["inspection_notice_status"] == "NEEDS_INSPECTION"
    assert report.generated_sections["inspection_notice"]

    evidence = db_session.scalar(
        select(TechnicalEvidence).where(TechnicalEvidence.vehicle_variant_id == variant_id)
    )
    original_statement = next(
        item["statement"]
        for item in report.evidence_bundle["technical_evidence"]
        if item["id"] == evidence.id
    )
    evidence.statement = "Changed after report creation"
    db_session.commit()
    db_session.refresh(report)
    snapshot_statement = next(
        item["statement"]
        for item in report.evidence_bundle["technical_evidence"]
        if item["id"] == evidence.id
    )
    assert snapshot_statement == original_statement


def test_report_access_is_owner_scoped_and_locked_content_is_hidden(
    client: TestClient, db_session: Session
) -> None:
    variant_id = seed_demo(db_session)
    owner_token = _register(client, "report-owner@example.com")
    other_token = _register(client, "other-owner@example.com")
    response = client.post(
        "/api/v1/analyses/preview",
        json=_payload(variant_id),
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    report_id = response.json()["report_id"]

    forbidden_as_not_found = client.get(
        f"/api/v1/reports/{report_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert forbidden_as_not_found.status_code == 404

    owner_view = client.get(
        f"/api/v1/reports/{report_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_view.status_code == 200
    assert owner_view.json()["evidence_bundle"] is None
    section_keys = {
        section["key"] for section in owner_view.json()["generated_sections"]["sections"]
    }
    assert section_keys <= {"expert_verdict", "vehicle"}


def test_report_language_does_not_change_calculations(
    client: TestClient, db_session: Session
) -> None:
    variant_id = seed_demo(db_session)
    token = _register(client, "language-owner@example.com")
    payload_ru = _payload(variant_id)
    payload_az = _payload(variant_id)
    payload_az["report_language"] = "az"

    headers = {"Authorization": f"Bearer {token}"}
    report_ru_id = client.post("/api/v1/analyses/preview", json=payload_ru, headers=headers).json()[
        "report_id"
    ]
    report_az_id = client.post("/api/v1/analyses/preview", json=payload_az, headers=headers).json()[
        "report_id"
    ]
    reports = {
        report.id: report
        for report in db_session.scalars(
            select(Report).where(Report.id.in_([report_ru_id, report_az_id]))
        )
    }
    assert reports[report_ru_id].calculated_data == reports[report_az_id].calculated_data
    assert (
        reports[report_ru_id].generated_sections["verdict_summary"]
        != reports[report_az_id].generated_sections["verdict_summary"]
    )


def test_owner_evidence_dedupe_key_is_enforced_by_database(db_session: Session) -> None:
    variant_id = seed_demo(db_session)
    existing = db_session.scalar(
        select(OwnerEvidence).where(OwnerEvidence.vehicle_variant_id == variant_id)
    )
    duplicate = OwnerEvidence(
        source_id=existing.source_id,
        vehicle_variant_id=existing.vehicle_variant_id,
        owner_identity_key=existing.owner_identity_key,
        material_identity_key="a-second-import-path",
        dedupe_key=existing.dedupe_key,
        mileage_km=existing.mileage_km,
        component=existing.component,
        topic=existing.topic,
        sentiment=existing.sentiment,
        issue_type=existing.issue_type,
        summary=existing.summary,
        observed_at=existing.observed_at,
        is_demo=True,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

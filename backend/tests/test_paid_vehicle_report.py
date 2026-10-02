from __future__ import annotations

import io
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest
from app.models.enums import Sentiment
from app.providers.knowledge_public import EPAConfigurationProvider, extract_architecture
from app.providers.official_nhtsa import OfficialHTTPClient
from app.review_engine.engine import OwnerFeedbackEngine
from app.schemas.paid_report import VehiclePhotoSet
from app.schemas.research import VehicleResearchRequest
from app.schemas.reviews import OwnerObservation, TopicAggregation
from app.services.knowledge_coverage import applicability, coverage, synthesize_facts
from app.services.owner_experience import aggregate_issues, fuel_layers, owner_sample
from app.services.paid_report import build_paid_report, paid_readiness
from app.services.report_pdf import render_report_pdf
from pydantic import ValidationError
from pypdf import PdfReader

TARGET = {"make": "Ford", "model": "Fusion", "year": 2019, "market": "USA", "displacement": 1.5}


def atom(topic, subtopic, value, *, source="s1", exact=False):
    return {
        "topic": topic,
        "subtopic": subtopic,
        "value": value,
        "status": "CONFIRMED",
        "applicability": TARGET,
        "evidence_ids": [f"{topic}-{subtopic}-{source}"],
        "source_ids": [source],
        "authority": "B",
        "exact_vin": exact,
    }


def sample_profile():
    facts = [
        atom("identity", k, v)
        for k, v in {
            "make": "Ford",
            "model": "Fusion",
            "year": 2019,
            "body": "Sedan/Saloon",
            "drivetrain": "FWD",
            "powertrain_type": "ICE",
        }.items()
    ]
    facts += [
        atom("engine", k, v)
        for k, v in {
            "displacement": 1.5,
            "cylinders": 4,
            "aspiration": "TURBO",
            "injection": "DIRECT_INJECTION",
            "oil": "SAE 5W-20",
            "fuel": "Gasoline",
        }.items()
    ]
    facts += [
        atom("transmission", "type", "AUTOMATIC"),
        atom("transmission", "gears", 6),
        atom("transmission", "fluid", "MERCON LV"),
        atom("suspension", "construction", "MACPHERSON_INTEGRAL_LINK"),
        atom("steering", "construction", "ELECTRIC_POWER_STEERING"),
    ]
    findings, contradictions = synthesize_facts(facts, TARGET)
    from app.services.vehicle_identity import integrity_from_findings

    evidence = [
        SimpleNamespace(id=eid, conditions={}) for f in findings for eid in f["evidence_ids"]
    ]
    return SimpleNamespace(
        make="Ford",
        model="Fusion",
        year=2019,
        market="USA",
        dossier_seed={
            "completed_capabilities": ["recalls"],
            "identity_integrity": integrity_from_findings(TARGET, findings, contradictions),
            "knowledge_depth": {"findings": findings, "contradictions": contradictions},
        },
        evidence=evidence,
        sources=[SimpleNamespace(id="s1")],
    )


def sample_check(language="ru"):
    return SimpleNamespace(
        profile=sample_profile(),
        language=language,
        normalized_vin="3FA6P0HD0KR114795",
        is_demo=False,
        full_history_payload={},
        dossier_snapshot={"sections": []},
    )


def test_material_topic_count_never_exceeds_total_even_with_150_mentions():
    items = [
        OwnerObservation(
            id=str(i),
            material_identity_key=f"post-{i % 100}",
            topic="engine",
            component="engine",
            sentiment=Sentiment.NEGATIVE,
            summary=f"changed text {i}",
        )
        for i in range(150)
    ]
    result = OwnerFeedbackEngine().aggregate(items)
    assert result.unique_material_count == 100
    assert result.topics[0].material_mentions == 100
    assert result.unique_observation_count == 100
    with pytest.raises(ValidationError):
        TopicAggregation(
            topic="engine",
            material_mentions=150,
            sample_size=100,
            mention_share=1,
            show_percentage=True,
            sentiment=Sentiment.NEGATIVE,
        )


def test_factory_document_and_anonymous_complaints_keep_qualified_confidence():
    factory = material(1, "manufacturer", "MANUFACTURER_COMMUNICATION")
    owners = [material(i, "nhtsa", "OFFICIAL_COMPLAINT_DATABASE") for i in (2, 3)]
    for row in owners:
        row["owner_id"] = None
    issue = aggregate_issues([factory, *owners], TARGET)["known_issues"][0]
    assert issue["status"] == "ESTIMATE"
    assert issue["confidence"] == "MEDIUM"
    assert issue["independent_source_count"] == 2


def test_insufficient_fuel_sample_is_not_upgraded_by_unknown_applicability():
    row = atom("fuel_consumption", "owner_reported", {"sample_size": 2})
    row["status"] = "INSUFFICIENT_DATA"
    row["applicability"] = {**TARGET, "engine_code": "UNKNOWN"}
    findings, _ = synthesize_facts([row], TARGET)
    assert findings[0]["status"] == "INSUFFICIENT_DATA"


def test_cvt_with_useful_fluid_information_does_not_require_fixed_gear_count():
    profile = sample_profile()
    facts = profile.dossier_seed["knowledge_depth"]["findings"]
    facts[:] = [f for f in facts if (f["topic"], f["subtopic"]) != ("transmission", "gears")]
    next(f for f in facts if (f["topic"], f["subtopic"]) == ("transmission", "type"))["value"] = (
        "CVT"
    )
    gate = paid_readiness(profile)
    assert gate.checks["transmission"]
    assert gate.missing_requirements == ["vin_history_checked"]


def test_bulletin_document_lookup_is_case_insensitive_and_variant_checked():
    from app.providers.knowledge_public import PublicTechnicalBulletinProvider

    provider = PublicTechnicalBulletinProvider(OfficialHTTPClient())
    request = VehicleResearchRequest(make="FORD", model="FUSION", year=2019)
    assert provider.document(request)
    assert not provider.document(VehicleResearchRequest(make="Ford", model="Focus", year=2019))


def test_phev_only_recall_is_excluded_from_matched_conventional_powertrain():
    from app.services.paid_report import relevant_recalls

    profile = sample_profile()
    profile.dossier_seed["knowledge_depth"]["epa_candidates"] = [{"fuelType2": "", "atvType": ""}]
    profile.evidence += [
        SimpleNamespace(
            id="phev",
            conditions={
                "campaign_number": "example",
                "summary": "certain 2019-2020 Fusion PHEV vehicles.",
            },
        ),
        SimpleNamespace(
            id="camera",
            conditions={"campaign_number": "other", "summary": "Fusion vehicles rearview camera"},
        ),
    ]
    assert [e.id for e in relevant_recalls(profile)] == ["camera"]


def test_incomplete_real_report_cannot_charge_and_diagnostics_are_owner_only(client, db_session):
    from app.core.config import get_settings
    from app.models.enums import DataOrigin
    from app.models.vehicle_knowledge import VINCheck, VINEntitlement
    from sqlalchemy import func, select

    get_settings().developer_mode = True
    token = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    cid = client.post(
        "/api/v1/vin/precheck", json={"vin": "3FA6P0HD0KR114795", "language": "ru"}, headers=headers
    ).json()["check_id"]
    check = db_session.get(VINCheck, cid)
    check.is_demo = False
    check.data_origin = DataOrigin.REAL
    db_session.commit()
    simulated = {**headers, "X-AutoExpert-Simulate-Paywall": "true"}
    response = client.post(f"/api/v1/vin/{cid}/payments/mock", json={}, headers=simulated)
    assert response.status_code == 409
    assert response.json()["detail"] == "NOT_ENOUGH_DATA_FOR_PAID_REPORT"
    assert db_session.scalar(select(func.count(VINEntitlement.id))) == 0
    assert client.get(f"/api/v1/vin/{cid}/report.pdf", headers=simulated).status_code == 402
    diagnostic = client.get(f"/api/v1/vin/{cid}/diagnostics", headers=headers)
    assert diagnostic.status_code == 200
    assert diagnostic.json()["quality_gate"]["state"] == "NOT_ENOUGH_DATA_FOR_PAID_REPORT"
    other = client.post("/api/v1/auth/demo", json={"preferred_language": "en"}).json()[
        "access_token"
    ]
    for route in ("diagnostics", "report.pdf", "photos/any"):
        assert (
            client.get(
                f"/api/v1/vin/{cid}/{route}", headers={"Authorization": f"Bearer {other}"}
            ).status_code
            == 404
        )


def test_real_photo_import_preserves_provenance_and_pdf_embeds_bytes(tmp_path, monkeypatch):
    from app.providers.vin_history import VINHistoryResearch
    from app.services.vin_history_assets import attach_history, photo_bytes
    from PIL import Image

    monkeypatch.setenv("AUTOEXPERT_VIN_ASSETS_DIR", str(tmp_path))
    check = sample_check()
    check.source_snapshot = []
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), color="blue").save(buffer, format="PNG")
    source = dict(
        id="photo-source",
        title="Authorized fixture",
        publisher="Fixture provider",
        url="https://example.com/vehicle",
        source_type="VIN_HISTORY",
        retrieved_at=datetime.now(UTC).isoformat(),
        confidence="HIGH",
        data_origin="REAL",
        is_demo=False,
    )
    research = VINHistoryResearch(
        vin=check.normalized_vin,
        provider_id="fixture",
        sources=[source],
        history=dict(
            vin=check.normalized_vin,
            timeline=[],
            auctions=[],
            photos=[],
            damage_details=[],
            odometer_records=[],
            is_demo=False,
            data_origin="REAL",
        ),
        photo_sets=[
            dict(
                vin=check.normalized_vin,
                source_id=source["id"],
                photos=[
                    dict(
                        id="photo1",
                        vin=check.normalized_vin,
                        source_id=source["id"],
                        source_url=source["url"],
                        asset_url="https://example.com/original.png",
                        retrieved_at=datetime.now(UTC),
                        provenance={"event": "fixture-only"},
                        caption="Fixture photograph",
                    )
                ],
            )
        ],
    )
    attach_history(check, research, {"photo1": buffer.getvalue()})
    report = build_paid_report(check)
    assert report.sections[-2].key == "history"
    photo = report.photo_sets[0].photos[0]
    assert len(photo.asset_sha256) == 64
    pdf = PdfReader(
        io.BytesIO(
            render_report_pdf(report, sources=[source], photo_assets={photo.id: photo_bytes(photo)})
        )
    )
    assert any(list(page.images) for page in pdf.pages)
    research.history.vin = "1HGCM82633A004352"
    with pytest.raises(ValidationError):
        VINHistoryResearch.model_validate(research.model_dump())


def test_unresolved_contradiction_blocks_sale_and_exact_vin_resolves_with_audit():
    a, b = atom("transmission", "gears", 6), atom("transmission", "gears", 8, source="s2")
    findings, conflicts = synthesize_facts([a, b], TARGET)
    assert findings[0]["value"] is None
    assert conflicts[0]["resolution"] == "UNRESOLVED"
    profile = sample_profile()
    profile.dossier_seed["knowledge_depth"]["contradictions"] = conflicts
    assert not paid_readiness(profile).can_purchase
    a["exact_vin"] = True
    findings, conflicts = synthesize_facts([a, b], TARGET)
    assert findings[0]["value"] == 6
    assert conflicts[0]["resolution"] == "EXACT_VIN_AUTHORITY"
    assert len(conflicts[0]["alternatives"]) == 2


@pytest.mark.parametrize(
    "field,wrong", [("displacement", 2.0), ("model", "Focus"), ("market", "JDM"), ("year", 2020)]
)
def test_incompatible_variant_is_rejected(field, wrong):
    assert applicability(TARGET, {**TARGET, field: wrong}) == "MISMATCH"


def test_unknown_variant_cannot_be_promoted_as_exact():
    row = atom("engine", "code", "ABC")
    row["applicability"] = {**TARGET, "engine_code": "ABC"}
    findings, _ = synthesize_facts([row], TARGET)
    assert findings[0]["status"] == "ESTIMATE"
    assert coverage(findings)["engine"]["coverage"] < 0.1


def material(number, publisher="owners-a", evidence_class="FORUM"):
    return {
        "material_id": str(number),
        "owner_id": str(number),
        "topic": "engine",
        "issue_key": "coolant_loss",
        "text": f"different narrative {number}",
        "publisher_group": publisher,
        "evidence_class": evidence_class,
        "applicability": TARGET,
        "evidence_ids": [str(number)],
        "source_ids": [publisher],
    }


def test_single_complaint_and_same_source_reports_never_become_known_issues():
    single = material(1, "nhtsa", "OFFICIAL_COMPLAINT_DATABASE")
    assert not aggregate_issues([single], TARGET)["known_issues"]
    same = aggregate_issues([material(1), material(2)], TARGET)
    assert not same["known_issues"]
    assert same["signals"][0]["strength"] == "WEAK_SIGNAL"


def test_independent_sources_promote_but_reposts_and_same_owner_do_not():
    a, b = material(1), material(2, "owners-b")
    result = aggregate_issues([a, b], TARGET)
    assert result["known_issues"][0]["independent_source_count"] == 2
    b["text"] = a["text"]
    assert not aggregate_issues([a, b], TARGET)["known_issues"]
    b["text"] = "a second account of the same owner's car"
    b["owner_id"] = a["owner_id"]
    assert not aggregate_issues([a, b], TARGET)["known_issues"]


def test_owner_reviews_exclude_official_complaints_and_small_samples_have_no_percentage():
    rows = [material(1), material(2, "nhtsa", "OFFICIAL_COMPLAINT_DATABASE")]
    sample = owner_sample(rows, TARGET)
    assert sample["sample_size"] == 1
    assert not sample["show_share"]


def test_consumption_classes_stay_separate_and_small_owner_sample_has_no_typical_number():
    result = fuel_layers(
        [{"combined": 8.7}], [{"mpg": 22}, {"mpg": 35}], user={"distance_km": 400, "liters": 40}
    )
    assert result["official"][0]["combined"] == 8.7
    assert result["owner_reported"]["combined_l_100km"] is None
    assert result["user_estimate"]["combined_l_100km"] == 10


@pytest.mark.parametrize("language", ["ru", "az", "en"])
def test_consumer_order_no_status_noise_no_model_comparison_and_traced_facts(language):
    report = build_paid_report(sample_check(language))
    assert report.readiness.missing_requirements == ["vin_history_checked"]
    keys = [s.key for s in report.sections]
    assert keys[0] == "vehicle"
    assert keys[-1] == "expert_verdict"
    assert "recommended_version" not in keys
    assert "history" not in keys
    assert not report.photo_sets
    values = " ".join(row.value for section in report.sections for row in section.rows)
    assert "CONFIRMED" not in values and "INSUFFICIENT_DATA" not in values
    assert all(
        row.source_ids and row.evidence_ids
        for s in report.sections
        for row in s.rows
        if row.key != "vin"
    )


@pytest.mark.parametrize("topic", ["engine", "transmission", "suspension"])
def test_missing_critical_content_denies_paid_readiness(topic):
    profile = sample_profile()
    depth = profile.dossier_seed["knowledge_depth"]
    depth["findings"] = [f for f in depth["findings"] if f["topic"] != topic]
    gate = paid_readiness(profile)
    assert gate.state == "NOT_ENOUGH_DATA_FOR_PAID_REPORT"
    assert not gate.can_purchase


def test_fabricated_provenance_denies_readiness():
    profile = sample_profile()
    profile.dossier_seed["knowledge_depth"]["findings"][0]["source_ids"] = ["missing"]
    assert not paid_readiness(profile).can_purchase


@pytest.mark.parametrize(
    "make,model,displacement",
    [("Ford", "Fusion", "1.5"), ("Toyota", "Camry", "2.5"), ("Hyundai", "Sonata", "2.4")],
)
def test_epa_provider_generic_configuration_matching(make, model, displacement):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        if "/menu/model" in request.url.path:
            return httpx.Response(200, json={"menuItem": {"value": model + " FWD"}})
        if "/menu/options" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "menuItem": [
                        {"text": f"Auto (S6), 4 cyl, {displacement} L", "value": "1"},
                        {"text": "Auto (S6), 6 cyl, 3.5 L", "value": "2"},
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "id": "1",
                "make": make,
                "baseModel": model,
                "model": model + " FWD",
                "year": "2019",
                "displ": displacement,
                "cylinders": "4",
                "fuelType1": "Regular Gasoline",
            },
        )

    provider = EPAConfigurationProvider(
        OfficialHTTPClient(
            client=httpx.Client(transport=httpx.MockTransport(handler)), min_interval_seconds=0
        )
    )
    result = provider.fetch_context(
        VehicleResearchRequest(make=make, model=model, year=2019),
        {
            "identity": {
                "displacement_l": displacement,
                "engine_cylinders": "4",
                "fuel_type_primary": "Gasoline",
            }
        },
    )
    assert len(result.records) == 1
    assert len(calls) == 3
    assert not any(url.endswith("/2") for url in calls)


def test_manufacturer_structure_extraction_requires_observed_text():
    assert not extract_architecture("Ford Fusion 2019")
    rows = extract_architecture(
        "Front: independent MacPherson strut; rear: independent integral link"
    )
    assert rows[0][:2] == ("suspension", "construction")


def test_photo_evidence_rejects_different_vin():
    with pytest.raises(ValidationError):
        VehiclePhotoSet(
            vin="3FA6P0HD0KR114795",
            source_id="source",
            photos=[
                {
                    "id": "photo",
                    "vin": "4T1B11HK8KU000000",
                    "source_id": "source",
                    "source_url": "https://example.org/event",
                    "asset_url": "https://example.org/photo.jpg",
                    "retrieved_at": datetime.now(UTC),
                    "provenance": {"provider": "test"},
                    "caption": "test",
                }
            ],
        )


def test_pdf_is_real_document_with_embedded_cyrillic_and_same_report_order():
    report = build_paid_report(sample_check())
    content = render_report_pdf(report, sources=[])
    assert content.startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(content))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert report.vin in text
    assert text.index("Автомобиль") < text.index("Двигатель") < text.index("Экспертный вывод")
    assert "CONFIRMED" not in text
    assert 4 <= len(reader.pages) <= 8

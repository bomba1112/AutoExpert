"""Stage 6.3 regression fixtures are synthetic and never loaded by live providers."""

import io
from datetime import UTC, datetime

import httpx
import pytest
from app.providers.owner_reviews import classify_topics, fingerprint, parse_complaints
from app.providers.public_evidence_http import PublicAccessError, PublicEvidenceHTTP
from app.providers.vin_history_public import AuthorizedHistoryAdapter
from app.schemas.research_evidence import (
    EvidenceProviderMetadata,
    OwnerMaterial,
    ProviderAttempt,
    VinEvent,
    VinHistoryResult,
)
from app.services.history_research import research_history
from app.services.owner_experience import (
    SampleThresholds,
    aggregate_issues,
    deduplicate_materials,
    owner_applicability,
    owner_sample,
)
from app.services.paid_report import build_paid_report, paid_readiness
from app.services.report_evidence_sections import history_status_text, owner_section
from app.services.report_pdf import render_report_pdf
from app.services.vin_events import deduplicate_events
from PIL import Image
from pydantic import ValidationError
from pypdf import PdfReader
from test_paid_vehicle_report import material, sample_check, sample_profile

VIN = "3FA6P0HD0KR114795"
TARGET = {
    "make": "Ford",
    "model": "Fusion",
    "year": 2019,
    "market": "USA",
    "displacement": 1.5,
    "cylinders": 4,
    "transmission": "AUTOMATIC",
    "powertrain": "CONVENTIONAL",
}


def meta(identifier="fixture"):
    return EvidenceProviderMetadata(
        id=identifier,
        name=identifier,
        capabilities=["AUCTION"],
        policy_url="https://example.com/policy",
        commercial_usage_status="ALLOWED",
    )


def source(identifier="s1"):
    return dict(
        id=identifier,
        title="Synthetic test source",
        publisher="Fixture",
        url="https://example.com/lot",
        source_type="VIN_HISTORY",
        source_tier="C",
        retrieved_at=datetime.now(UTC).isoformat(),
        confidence="MEDIUM",
        data_origin="REAL",
        is_demo=False,
    )


def event(**changes):
    value = dict(
        id="raw1",
        vin=VIN,
        event_type="AUCTION",
        event_date="2020-03-04",
        auction="Copart",
        lot_id="123456",
        location="TX",
        odometer=56000,
        odometer_unit="mi",
        source_ids=["s1"],
        provenance=[{"url": "https://example.com/lot", "vin_in_page": VIN}],
    )
    value.update(changes)
    return VinEvent(**value)


def result(state="NO_RECORDS", **kwargs):
    return VinHistoryResult(
        vin=VIN,
        attempt=ProviderAttempt(
            provider=meta(),
            state=state,
            query={"vin": VIN},
            scope="Fixture archive",
            query_completed=state in {"AVAILABLE", "NO_RECORDS"},
            provenance={"response_sha256": "a" * 64},
        ),
        **kwargs,
    )


def history_payload(state="NO_RECORDS"):
    check = sample_check()
    check.source_snapshot = []
    adapter = AuthorizedHistoryAdapter(meta(), lambda vin: result(state))
    research_history(check, [adapter])
    return check.full_history_payload


def test_event_mirrors_merge_provenance_and_optional_values():
    merged, ids = deduplicate_events(
        [
            event(),
            event(
                id="raw2",
                source_ids=["s2"],
                primary_damage="Front end",
                provenance=[{"url": "https://example.org/mirror"}],
            ),
        ]
    )
    assert len(merged) == 1 and ids["raw1"] == ids["raw2"]
    assert merged[0].source_ids == ["s1", "s2"]
    assert len(merged[0].provenance) == 2 and merged[0].sale_price is None


@pytest.mark.parametrize(
    "change", [{"event_date": "2020-05-05"}, {"lot_id": "different"}, {"vin": "4T1B11HK8KU765432"}]
)
def test_relist_or_different_vehicle_is_not_a_mirror(change):
    assert len(deduplicate_events([event(), event(id="second", **change)])[0]) == 2


def test_event_conflicts_remain_visible_without_choosing_an_odometer():
    events, _ = deduplicate_events([event(), event(id="second", odometer=57000)])
    assert events[0].odometer is None
    assert len(events[0].conflicts["odometer"]) == 2


@pytest.mark.parametrize(
    "state", ["PROVIDER_UNAVAILABLE", "AUTH_REQUIRED", "RATE_LIMITED", "ERROR"]
)
def test_failure_is_not_no_records_and_never_ready(state):
    history = history_payload(state)
    assert history["history_research"]["state"] == "PROVIDER_UNAVAILABLE"
    assert not paid_readiness(sample_profile(), history).can_purchase
    assert "не найдена" not in history_status_text(history, "ru")[0]


def test_explicit_completed_zero_result_allows_technically_complete_report():
    history = history_payload()
    assert paid_readiness(sample_profile(), history).can_purchase
    assert (
        history_status_text(history, "ru")[0]
        == "В подключённых источниках история этого VIN не найдена."
    )
    history["history_research"]["attempts"][0]["query"]["vin"] = "4T1B11HK8KU765432"
    assert not paid_readiness(sample_profile(), history).can_purchase


def test_no_records_requires_completed_query_and_contains_no_events():
    with pytest.raises(ValidationError):
        ProviderAttempt(
            provider=meta(),
            state="NO_RECORDS",
            query={"vin": VIN},
            scope="test",
            provenance={"query": VIN},
        )
    with pytest.raises(ValidationError):
        result(events=[event()], sources=[source()])


def test_not_checked_cannot_be_described_as_no_history():
    assert "ещё не проверена" in history_status_text({}, "ru")[0]
    assert not paid_readiness(sample_profile()).can_purchase


def photo_result(**photo_changes):
    photo = dict(
        id="p1",
        vin=VIN,
        source_id="s1",
        source_url="https://example.com/lot",
        asset_url="https://example.com/test.png",
        event_id="raw1",
        order=0,
        retrieved_at=datetime.now(UTC),
        caption="Synthetic test image",
        cache_permission="TEST_FIXTURE",
        provenance={"event_id": "raw1", "vin_in_page": VIN},
    )
    photo.update(photo_changes)
    return result(
        "AVAILABLE",
        events=[event()],
        sources=[source()],
        photo_sets=[dict(vin=VIN, source_id="s1", event_id="raw1", photos=[photo])],
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"vin": "4T1B11HK8KU765432"},
        {"event_id": "wrong"},
        {"provenance": {}},
        {"source_url": "https://other.example/lot"},
    ],
)
def test_photo_exact_vin_event_and_provenance_required(changes):
    with pytest.raises(ValidationError):
        photo_result(**changes)


def test_conditional_pdf_embeds_only_actual_validated_assets(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOEXPERT_VIN_ASSETS_DIR", str(tmp_path))
    out = io.BytesIO()
    Image.new("RGB", (30, 20), color="blue").save(out, format="PNG")
    check = sample_check("en")
    check.source_snapshot = []
    adapter = AuthorizedHistoryAdapter(
        meta(), lambda vin: photo_result(), lambda result: {"p1": out.getvalue()}
    )
    research_history(check, [adapter])
    assert check.records_count == 1 and check.photos_count == 1
    report = build_paid_report(check)
    assert report.photo_sets[0].event_id == report.sections[-2].events[0].id
    with pytest.raises(ValueError):
        render_report_pdf(report, sources=check.source_snapshot)
    pdf = PdfReader(
        io.BytesIO(
            render_report_pdf(
                report, sources=check.source_snapshot, photo_assets={"p1": out.getvalue()}
            )
        )
    )
    assert sum(len(page.images) for page in pdf.pages) == 1
    research_history(check, [AuthorizedHistoryAdapter(meta(), lambda vin: result())])
    report = build_paid_report(check)
    assert not report.photo_sets
    pdf = PdfReader(io.BytesIO(render_report_pdf(report, sources=check.source_snapshot)))
    assert not any(page.images for page in pdf.pages)


def test_invalid_photo_is_provider_error_not_an_endpoint_crash():
    check = sample_check()
    check.source_snapshot = []
    adapter = AuthorizedHistoryAdapter(
        meta(), lambda vin: photo_result(), lambda result: {"p1": b"not an image"}
    )
    research_history(check, [adapter])
    assert check.full_history_payload["history_research"]["attempts"][0]["state"] == "ERROR"
    assert check.photos_count == 0


def test_paid_adapter_cannot_activate_without_spending_authorization():
    with pytest.raises(ValueError):
        AuthorizedHistoryAdapter(
            meta().model_copy(update={"cost_type": "PAYG"}), lambda vin: result()
        )


def test_robots_denial_is_not_bypassed():
    calls = []

    def handle(request):
        calls.append(str(request.url))
        return httpx.Response(200, text="User-agent: *\nDisallow: /private")

    client = PublicEvidenceHTTP(httpx.MockTransport(handle))
    with pytest.raises(PublicAccessError, match="ROBOTS_DISALLOW"):
        client.get("https://example.com/private/vehicle", allowed_hosts={"example.com"})
    assert calls == ["https://example.com/robots.txt"]
    client.close()


@pytest.mark.parametrize(
    "status,state", [(401, "AUTH_REQUIRED"), (403, "PROVIDER_UNAVAILABLE"), (429, "RATE_LIMITED")]
)
def test_http_access_states_no_retry(status, state):
    calls = []

    def handle(request):
        calls.append(str(request.url))
        return (
            httpx.Response(200, text="User-agent: *\nAllow: /")
            if request.url.path == "/robots.txt"
            else httpx.Response(status)
        )

    client = PublicEvidenceHTTP(httpx.MockTransport(handle))
    with pytest.raises(PublicAccessError) as captured:
        client.get("https://example.com/vehicle", allowed_hosts={"example.com"})
    assert captured.value.state == state and len(calls) == 2
    client.close()


def test_owner_dedup_tracking_pagination_repost_and_near_quote():
    first = material(1)
    first["canonical_url"] = "https://www.example.com/thread/#post1"
    copy = {
        **first,
        "material_id": "copy",
        "canonical_url": "https://example.com/thread/page-2/?utm_source=a#post1",
    }
    repost = {**material(3), "repost_of": first["canonical_url"]}
    assert len(deduplicate_materials([first, copy], TARGET)) == 1
    # Explicit repost linkage is retained even if the copied text is edited.
    assert len(deduplicate_materials([first, repost], TARGET)) == 1
    prose = " ".join(f"word{i}" for i in range(100))
    a, b = material(1), material(2, "another-publisher")
    a["content_hash"], a["text_fingerprint"] = fingerprint(prose)
    b["content_hash"], b["text_fingerprint"] = fingerprint(prose + " quoted again")
    assert len(deduplicate_materials([a, b], TARGET)) == 1


@pytest.mark.parametrize(
    "scope",
    [
        {"displacement": 2.0},
        {"powertrain": "HYBRID"},
        {"powertrain": "PHEV"},
        {"transmission": "CVT"},
        {"fuel": "Diesel"},
    ],
)
def test_variant_and_hybrid_isolation(scope):
    row = material(1)
    row["applicability"] = {**TARGET, **scope}
    assert owner_applicability({**TARGET, "fuel": "Gasoline"}, row) != "MATCH"
    assert not owner_sample([row], TARGET)["materials"]


def test_topic_counts_are_unique_per_material_and_not_population_percentages():
    rows = [dict(material(i), topics=["ENGINE"] * 150 + ["COOLING"]) for i in range(6)]
    sample = owner_sample([*rows, *rows], TARGET)
    assert sample["unique_materials"] == 6
    assert sample["topic_mentions"] == {"ENGINE": 6, "COOLING": 6}
    assert not sample["show_share"]


@pytest.mark.parametrize(
    "count,quality",
    [(0, "VERY_SMALL"), (4, "VERY_SMALL"), (5, "SMALL"), (20, "USEFUL"), (50, "STRONG")],
)
def test_sample_quality_thresholds_are_explicit(count, quality):
    sample = owner_sample([material(i) for i in range(count)], TARGET)
    assert sample["sample_quality"] == quality
    assert sample["reliability_conclusion_allowed"] == (count >= 5)
    assert SampleThresholds(2, 4, 6).quality(3) == "SMALL"


def test_official_complaints_never_count_as_owner_materials():
    rows = [
        material(1, "nhtsa", "OFFICIAL_COMPLAINT"),
        material(2, "nhtsa", "OFFICIAL_COMPLAINT_DATABASE"),
    ]
    assert owner_sample(rows, TARGET)["sample_size"] == 0
    with pytest.raises(ValidationError):
        OwnerMaterial(evidence_class="OFFICIAL_COMPLAINT")


def test_known_issue_cross_check_counts_sources_and_does_not_upgrade_one_anecdote():
    factory = material(10, "manufacturer", "MANUFACTURER_COMMUNICATION")
    owner = material(20, "community")
    issue = aggregate_issues([factory, owner], TARGET)["known_issues"][0]
    assert issue["owner_material_count"] == 1 and issue["official_support"]
    assert issue["confidence"] == "MEDIUM" and issue["status"] == "ESTIMATE"
    issue = aggregate_issues([factory, owner, material(30, "independent")], TARGET)["known_issues"][
        0
    ]
    assert issue["owner_material_count"] == 2 and issue["confidence"] == "HIGH"
    assert issue["independent_source_count"] == 3
    assert not aggregate_issues([owner], TARGET)["known_issues"]


@pytest.mark.parametrize(
    "make,model,liters",
    [("Ford", "Fusion", 1.5), ("Toyota", "Camry", 2.5), ("Hyundai", "Sonata", 2.4)],
)
def test_one_parser_handles_three_brands_without_inheriting_engine(make, model, liters):
    target = {**TARGET, "make": make, "model": model, "displacement": liters}
    html = f"""<div class="complaint" id="p0"><div class="cheader"><a class="pnum" name="1">1</a>
        <div class="pdate">Jun 01 <span>2023</span></div><h3 class="ptitle">{model} {liters}L</h3>
        <ul><li>Automatic transmission</li><li>64,000 miles</li></ul></div>
        <div class="comments"><div>
        I experienced a transmission failure and needed a replacement.</div>
        <p class="userinfo"><strong>Test author</strong>
        <span>Test city, US</span></p></div></div>"""
    rows, excluded = parse_complaints(html, "https://example.com/lot", target, datetime.now(UTC))
    assert len(rows) == 1 and not excluded and rows[0].owner_id
    assert owner_sample([rows[0].model_dump(mode="json")], target)["sample_size"] == 1
    rows, _ = parse_complaints(
        html.replace(f"{liters}L", ""), "https://example.com/lot", target, datetime.now(UTC)
    )
    assert owner_sample([rows[0].model_dump(mode="json")], target)["sample_size"] == 0


def test_mirrored_nhtsa_page_is_never_an_owner_review():
    rows, excluded = parse_complaints(
        "About These NHTSA Complaints", "https://example.com", TARGET, datetime.now(UTC)
    )
    assert not rows and excluded[0]["reason"] == "OFFICIAL_COMPLAINT_MIRROR"
    assert "BODY" not in classify_topics("I trusted the car but the transmission failed.")


@pytest.mark.parametrize("language", ["ru", "az", "en"])
def test_localized_no_record_owner_quality_and_pdf(language):
    check = sample_check(language)
    check.full_history_payload = history_payload()
    sample = owner_sample([dict(material(1), topics=["ENGINE"], sentiment="NEGATIVE")], TARGET)
    check.full_history_payload["owner_reliability"] = {"sample": sample}
    report = build_paid_report(check)
    assert report.readiness.can_purchase
    section = owner_section({"sample": sample}, language)
    assert section.title in {"Отзывы владельцев", "Sahiblərin rəyləri", "Owner reviews"}
    assert "VERY_SMALL" not in section.model_dump_json() and not report.photo_sets
    pdf = PdfReader(io.BytesIO(render_report_pdf(report, sources=[])))
    text = " ".join(p.extract_text() for p in pdf.pages)
    assert section.title in text and VIN in text

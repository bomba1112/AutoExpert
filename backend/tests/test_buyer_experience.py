# ruff: noqa: E501
"""Buyer contracts; synthetic fixtures here never feed production research."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.core.config import get_settings
from app.models.enums import ReportStatus
from app.providers import listings
from app.schemas.paid_report import PaidReportSection, ReportRow
from app.schemas.research import VehicleResearchRequest
from app.services.buyer_experience import buyer_projection, persist_report
from app.services.paid_report import build_paid_report
from app.services.research_pipeline import _effective_request
from app.services.variant_resolver import VehicleVariantResolver, epa_candidates
from test_paid_vehicle_report import sample_check


def login(client):
    payload = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"}).json()
    return {"Authorization": "Bearer " + payload["access_token"]}, payload["user"]["id"]


@pytest.mark.parametrize(
    "address", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "fc00::1", "100.64.0.1"]
)
def test_listing_ssrf_blocks_nonpublic_dns(monkeypatch, address):
    monkeypatch.setattr(
        listings.socket, "getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", (address, 443))]
    )
    with pytest.raises(listings.ListingUnavailable, match="UNSAFE_URL"):
        listings.public_address("https://apparently-public.example/car")


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "https://u:p@example.com/car",
        "http://localhost/car",
        "https://example.com:8080/car",
    ],
)
def test_listing_rejects_unsafe_url_shape(url):
    with pytest.raises(listings.ListingUnavailable):
        listings.public_address(url)


def test_turbo_parser_seller_photo_class_currency_no_fake_vin(monkeypatch):
    monkeypatch.setattr(listings, "public_address", lambda url: None)
    html = """<meta property="og:image" content="https://turbo.azstatic.com/uploads/full/car.jpg">
    <div class="product-photos"><img src="https://turbo.azstatic.com/uploads/f660x496/car.jpg"><img src="https://turbo.azstatic.com/uploads/thumbnail/car.jpg"></div>
    <div class="product-properties__i"><span class="product-properties__i-name">Marka</span><span class="product-properties__i-value">Example</span></div>
    <div class="product-properties__i"><span class="product-properties__i-name">Model</span><span class="product-properties__i-value">Car</span></div>
    <div class="product-properties__i"><span class="product-properties__i-name">Buraxılış ili</span><span class="product-properties__i-value">2020</span></div>
    <div class="product-price__i">27 900 ₼</div>"""
    parsed = listings.parse_listing(html, "https://turbo.az/autos/test")
    assert parsed["vin"] is None
    assert parsed["currency"] == "AZN" and parsed["price"] == 27900
    assert parsed["photos"][0]["type"] == "LISTING"
    assert parsed["photos"][0]["pdf_permission"] == "NOT_ESTABLISHED"
    assert len(parsed["photos"]) == 1
    assert parsed["claim_type"] == "SELLER_CLAIM"


def test_shared_schema_org_adapter(monkeypatch):
    monkeypatch.setattr(listings, "public_address", lambda url: None)
    result = listings.parse_listing(
        """<script type="application/ld+json">{"@type":"Car","brand":{"name":"Example"},"model":"Electric","vehicleModelDate":"2024","offers":{"price":31000,"priceCurrency":"EUR"},"user":{"session":"must not persist"}}</script>""",
        "https://dealer.example/car",
    )
    assert result["adapter"] == "schema.org" and result["price"] == 31000
    assert "user" not in result and "session" not in str(result)


def test_robots_block_never_fetches_listing(monkeypatch):
    calls = []
    monkeypatch.setattr(listings, "public_address", lambda url: None)

    def fake(url, **kw):
        calls.append(url)
        return 200, "text/plain", b"User-agent: *\nDisallow: /", url

    monkeypatch.setattr(listings, "fetch_public", fake)
    result = listings.import_listing("https://dealer.example/car")
    assert result["reason"] == "SOURCE_RESTRICTED"
    assert calls == ["https://dealer.example/robots.txt"]


def test_optional_vin_and_hints_survive_identity_lookup():
    request = VehicleResearchRequest(
        make="Example", model="Car", year=2020, powertrain_hint="HEV", engine_hint="1.8"
    )
    identity = {"make": "Example", "model": "Car", "model_year": 2020}
    request = _effective_request(request, identity)
    assert request.vin is None and request.powertrain_hint == "HEV"
    records = [
        {
            "id": "1",
            "model": "Car",
            "displ": 1.8,
            "fuelType1": "Regular Gasoline",
            "atvType": "",
            "trany": "Automatic (variable gear ratios)",
            "drive": "Front-Wheel Drive",
        },
        {
            "id": "2",
            "model": "Car Hybrid",
            "displ": 1.8,
            "fuelType1": "Regular Gasoline",
            "atvType": "Hybrid",
            "trany": "Automatic (variable gear ratios)",
            "drive": "Front-Wheel Drive",
        },
    ]
    result = VehicleVariantResolver().resolve(request, [identity], epa_candidates(records))
    assert result["selected_candidate_id"] == "epa:2"
    assert not result["needs_user_selection"]


def test_unavailable_requested_powertrain_requires_visible_choice():
    request = VehicleResearchRequest(make="Example", model="Car", year=2020, powertrain_hint="BEV")
    result = VehicleVariantResolver().resolve(
        request,
        [{"make": "Example", "model": "Car", "model_year": 2020}],
        epa_candidates(
            [{"id": "1", "model": "Car", "displ": 1.8, "fuelType1": "Regular Gasoline"}]
        ),
    )
    assert result["needs_user_selection"] and result["selected_candidate_id"] is None


@pytest.mark.parametrize("language", ["ru", "az", "en"])
def test_model_projection_no_fake_vin_separate_history_gate_and_verdict_first(language):
    check = sample_check(language)
    check.normalized_vin = ""
    report = buyer_projection(build_paid_report(check), check, None, {})
    assert report.vin == ""
    assert all(row.key != "vin" for row in report.sections[0].rows)
    assert "vin_history_checked" not in report.readiness.checks
    assert report.sections[0].key == "expert_verdict"
    assert not any(section.key == "history" for section in report.sections)


def report_fixture(db, uid, name="First", fuel=4.5):
    check = sample_check()
    check.normalized_vin = ""
    projections = {}
    for lang in ["ru", "az", "en"]:
        check.language = lang
        p = buyer_projection(build_paid_report(check), check, None, {})
        p.title = name
        p.sections[1] = PaidReportSection(
            key="engine",
            title="Engine",
            rows=[
                ReportRow(
                    key="engine.displacement",
                    label="Engine",
                    value=name + " unique value",
                    source_ids=[name],
                )
            ],
        )
        projections[lang] = p.model_dump(mode="json")
    return persist_report(
        db, uid, "ru", {"kind": "MODEL"}, projections, {"sources": [], "official_consumption": fuel}
    )


def test_comparison_2_3_isolation_ownership_paywall_and_storage(client, db_session):
    headers, uid = login(client)
    get_settings().developer_mode = True
    cars = [
        report_fixture(db_session, uid, name, fuel)
        for name, fuel in [("First", 4.5), ("Second", 7.2), ("Third", 6.3)]
    ]
    for count in (2, 3):
        r = client.post(
            "/api/v1/reports/buyer/comparisons",
            headers=headers,
            json={"report_ids": [r.id for r in cars[:count]], "preferences": {"monthly_km": 2000}},
        )
        assert r.status_code == 200, r.text
        value = r.json()
        engine = next(s for s in value["projection"]["sections"] if s["key"] == "engine")
        assert len(engine["rows"]) == count
        for row in engine["rows"]:
            assert row["label"].split(" · ")[0] in row["value"]
        assert value["projection"]["sections"][0]["key"] == "expert_verdict"
        assert "90 L" in value["projection"]["sections"][0]["paragraphs"][0]["text"]
        rid = value["id"]
        assert (
            client.get(
                f"/api/v1/reports/buyer/{rid}",
                headers={**headers, "X-AutoExpert-Simulate-Paywall": "true"},
            ).status_code
            == 402
        )
        other, _ = login(client)
        assert client.get(f"/api/v1/reports/buyer/{rid}", headers=other).status_code == 404
        assert client.get(f"/api/v1/reports/buyer/{rid}/pdf", headers=other).status_code == 404
        pdf = client.get(f"/api/v1/reports/buyer/{rid}/pdf", headers=headers)
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
        assert pdf.headers["cache-control"] == "private, no-store"
    assert all(r.status == ReportStatus.FULL for r in cars)
    duplicate = client.post(
        "/api/v1/reports/buyer/comparisons", headers=headers, json={"report_ids": [cars[0].id] * 2}
    )
    assert duplicate.status_code == 422
    # Existing member access must not unlock a newly created comparison.
    for car in cars:
        car.is_unlocked = True
    db_session.commit()
    restricted = client.post(
        "/api/v1/reports/buyer/comparisons",
        headers={**headers, "X-AutoExpert-Simulate-Paywall": "true"},
        json={"report_ids": [car.id for car in cars[:2]]},
    )
    assert restricted.status_code == 402


def test_blocked_import_saved_with_fallback_and_owned(client, monkeypatch):
    headers, _ = login(client)
    monkeypatch.setattr(
        "app.api.routes.buyer.import_listing",
        lambda url: {
            "source_url": url,
            "status": "UNAVAILABLE",
            "reason": "SOURCE_RESTRICTED",
            "data": {},
        },
    )
    r = client.post(
        "/api/v1/reports/buyer/listings",
        headers=headers,
        json={"url": "https://turbo.az/autos/10506644-toyota-corolla"},
    )
    assert r.status_code == 200 and r.json()["source_url"] == (
        "https://turbo.az/autos/10506644-toyota-corolla"
    )
    rid = r.json()["id"]
    other, _ = login(client)
    assert client.get(f"/api/v1/reports/buyer/listings/{rid}", headers=other).status_code == 404
    fallback = client.post(
        "/api/v1/reports/buyer/listings",
        headers=headers,
        json={"url": r.json()["source_url"], "description": "Seller supplied text"},
    )
    assert fallback.json()["status"] == "USER_PASTED" and fallback.json()["id"] != rid


def test_local_session_renewal_preserves_owner_and_rejects_unsigned(client):
    headers, uid = login(client)
    get_settings().developer_mode = True
    now = datetime.now(UTC)
    token = jwt.encode(
        {"sub": uid, "iat": now - timedelta(hours=2), "exp": now - timedelta(hours=1)},
        get_settings().secret_key,
        algorithm="HS256",
    )
    r = client.post(
        "/api/v1/auth/local-session/renew", headers={"Authorization": "Bearer " + token}
    )
    assert r.status_code == 200 and r.json()["user"]["id"] == uid
    assert (
        client.post(
            "/api/v1/auth/local-session/renew", headers={"Authorization": "Bearer " + token + "x"}
        ).status_code
        == 401
    )
    get_settings().developer_mode = False
    assert client.post("/api/v1/auth/local-session/renew", headers=headers).status_code == 404


def test_client_contract_version(client):
    r = client.get("/api/v1/meta/client-config").json()
    assert r["version"] == "0.8.1" and r["buyer_api_version"] == 1

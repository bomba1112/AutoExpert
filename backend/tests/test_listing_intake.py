"""Single user-provided listing intake, ownership and production-safe matching."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.core.config import get_settings
from app.models.listing_intake import ListingIntakeRequest, ListingSnapshot
from app.providers.history_fixture import FIXTURE_VIN
from app.services import listing_intake as intake
from fastapi.testclient import TestClient
from sqlalchemy import func, select

BASE = "/api/v1/listings/intake"


def auth(client: TestClient) -> dict:
    response = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def record(
    identifier: str,
    make: str,
    model: str,
    year: int,
    engine: str,
    displacement: str,
    transmission: str,
    drive: str,
    fuel="GASOLINE",
):
    facts = {
        "engine_description": engine,
        "engine_displacement": displacement,
        "transmission_description": transmission,
        "drivetrain": drive,
        "fuel": fuel,
    }
    return SimpleNamespace(id=identifier), {
        "make": make,
        "model": model,
        "model_year": year,
        "original_market": "US",
        "facts": {key: {"status": "CONFIRMED", "value": value} for key, value in facts.items()},
    }


@pytest.fixture
def production_rows(monkeypatch):
    rows = [
        record(
            "cruze-2017",
            "Chevrolet",
            "Cruze",
            2017,
            "1.4L turbo gasoline inline-4",
            "1.4",
            "6-speed automatic",
            "FWD",
        ),
        record(
            "a3-18",
            "Audi",
            "A3",
            2015,
            "1.8 TFSI turbo inline-4",
            "1.8",
            "6-speed S tronic dual-clutch",
            "FWD",
        ),
        record(
            "a3-20",
            "Audi",
            "A3",
            2015,
            "2.0 TFSI turbo inline-4",
            "2.0",
            "6-speed S tronic dual-clutch",
            "AWD",
        ),
    ]
    rows[0][1]["facts"]["body"] = {"status": "CONFIRMED", "value": "UNKNOWN"}
    monkeypatch.setattr(intake, "_consumer_rows", lambda db: rows)
    return rows


def post(client, headers, fields, **extra):
    return client.post(
        BASE,
        headers=headers,
        json={
            "input_type": "MANUAL",
            "language": "ru",
            "fields": fields,
            **extra,
        },
    )


def test_url_reference_is_validated_owned_and_never_fetched(client, db_session, monkeypatch):
    def forbidden(_db):
        raise AssertionError("URL-only intake must not query catalog or network")

    monkeypatch.setattr(intake, "_consumer_rows", forbidden)
    headers = auth(client)
    payload = {
        "input_type": "URL_REFERENCE",
        "source_url": "https://www.turbo.az/autos/10506644-toyota-corolla?utm_source=share",
    }
    first = client.post(BASE, headers=headers, json=payload)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["snapshot"]["source_url"] == "https://www.turbo.az/autos/10506644-toyota-corolla"
    assert body["snapshot"]["source_listing_id"] == "10506644"
    assert body["claims"] == [] and body["next_step"] == "PROVIDE_CONTENT"
    assert client.post(BASE, headers=headers, json=payload).json()["id"] == body["id"]
    assert db_session.scalar(select(func.count()).select_from(ListingIntakeRequest)) == 1
    assert client.get(f"{BASE}/{body['id']}", headers=auth(client)).status_code == 404
    assert client.get(f"{BASE}/{body['id']}", headers=headers).json() == body
    in_az = client.post(BASE, headers=headers, json={**payload, "language": "az"}).json()
    assert in_az["id"] == body["id"]
    assert in_az["snapshot"]["language"] == "az"
    assert db_session.scalar(select(func.count()).select_from(ListingIntakeRequest)) == 1


@pytest.mark.parametrize(
    "url",
    [
        "http://turbo.az/autos/10506644-toyota-corolla",
        "https://evil.example/autos/10506644-toyota-corolla",
        "https://turbo.az.evil.example/autos/10506644-toyota-corolla",
        "https://localhost/autos/10506644-toyota-corolla",
        "https://127.0.0.1/autos/10506644-toyota-corolla",
        "https://user:secret@turbo.az/autos/10506644-toyota-corolla",
        "https://turbo.az:443/autos/10506644-toyota-corolla",
        "https://turbo.az/autos/../../127.0.0.1",
        "https://turbo.az/autos/%31%30%35%30%36%36%34%34",
        "https://turbo.az/autos/10506644/redirect",
    ],
)
def test_url_rejects_unsupported_domains_and_ssrf_shapes(client, url):
    response = client.post(
        BASE,
        headers=auth(client),
        json={
            "input_type": "URL_REFERENCE",
            "source_url": url,
        },
    )
    assert response.status_code == 422, response.text


def test_content_type_allowlist_and_byte_limits(client):
    headers = auth(client)
    cases = [
        {
            "input_type": "URL_REFERENCE",
            "source_url": "https://turbo.az/autos/10506644-car",
            "fields": {},
        },
        {"input_type": "TEXT", "text": "A" * 60_001},
        {"input_type": "HTML_SNAPSHOT", "html": "ə" * 128_001},
        {"input_type": "MANUAL", "fields": {"remote_url": "https://127.0.0.1/"}},
        {"input_type": "PDF", "text": "listing"},
    ]
    for payload in cases:
        assert client.post(BASE, headers=headers, json=payload).status_code == 422


def test_authorized_connector_remains_disabled_without_permissions(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "turbo_az_authorized_connector_enabled", False)
    value = intake.ListingIntakeCreate(
        input_type="URL_REFERENCE", source_url="https://turbo.az/autos/10506644-car"
    )
    with pytest.raises(intake.ListingInputError, match="disabled"):
        intake.TurboAzAuthorizedConnector().parse(value)


def test_pasted_text_preserves_seller_claims_and_optional_absence(client, production_rows):
    headers = auth(client)
    pasted = "\n".join(
        [
            "Chevrolet Cruze, 1.4 L, 2017 il",
            "Qiymət: 27 900 AZN",
            "Yürüş: 80 000 km",
            "Yanacaq: Benzin",
            "Sürətlər qutusu: Avtomat",
            "Ötürücü: Ön",
            "Hansı bazar üçün yığılıb: Amerika",
            "Rəsmi diler",
        ]
    )
    response = client.post(
        BASE,
        headers=headers,
        json={
            "input_type": "TEXT",
            "text": pasted,
            "source_url": "https://turbo.az/autos/10506644-chevrolet-cruze",
            "language": "az",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    claims = {c["field_name"]: c for c in body["claims"]}
    assert body["snapshot"]["source_type"] == "TURBO_AZ"
    assert body["match"]["status"] == "EXACT_MATCH"
    assert claims["transmission"]["normalized_value"] == "AUTOMATIC_UNSPECIFIED"
    assert claims["transmission"]["claim_type"] == "SELLER_CLAIM"
    assert claims["market"]["raw_value"] == "Amerika"
    assert claims["market"]["claim_type"] == "SELLER_CLAIM"
    assert claims["seller_type"]["raw_value"] == "Rəsmi diler"
    assert "vin" not in claims and "color" not in claims
    assert claims["price"]["normalized_value"] == 27900
    assert claims["mileage"]["normalized_value"] == 80000


def test_html_snapshot_is_plain_data_with_no_scripts_or_photos(client, db_session, production_rows):
    html = """<html><script>alert('XSS'); location='https://bad.invalid'</script>
    <h1>Audi A3, 2015 il</h1><div class="product-price">24 900 AZN</div>
    <div class="product-properties__i"><span class="product-properties__i-name">Marka</span>
    <span class="product-properties__i-value">Audi</span></div>
    <div class="product-properties__i"><span class="product-properties__i-name">Model</span>
    <span class="product-properties__i-value">A3</span></div>
    <div class="product-properties__i"><span class="product-properties__i-name">Elan nömrəsi</span>
    <span class="product-properties__i-value">10506645</span></div>
    <img src="https://example.invalid/car.jpg"><iframe src="https://bad.invalid"></iframe>
    </html>"""
    response = client.post(
        BASE,
        headers=auth(client),
        json={
            "input_type": "HTML_SNAPSHOT",
            "html": html,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["snapshot"]["source_type"] == "USER_PROVIDED"
    assert body["snapshot"]["source_listing_id"] == "10506645"
    assert body["match"]["status"] == "MULTIPLE_CANDIDATES"
    assert "bad.invalid" not in response.text and "car.jpg" not in response.text
    snapshot = db_session.scalar(select(ListingSnapshot))
    assert "alert" not in snapshot.sanitized_content
    assert "iframe" not in snapshot.sanitized_content


def test_match_statuses_and_no_internal_epa_fields(client, production_rows):
    headers = auth(client)
    exact = post(
        client,
        headers,
        {
            "make": "Chevrolet",
            "model": "Cruze",
            "year": "2017",
            "engine": "1.4 L",
            "fuel": "gasoline",
            "transmission": "automatic",
            "drivetrain": "FWD",
            "market": "Amerika",
        },
    )
    assert exact.status_code == 200, exact.text
    assert exact.json()["match"]["status"] == "EXACT_MATCH"
    assert exact.json()["match"]["candidates"][0]["variant_id"] == "cruze-2017"
    assert exact.json()["match"]["candidates"][0]["body"] is None
    assert "UNKNOWN" not in exact.text
    assert "source_configuration" not in exact.text
    assert "source_registry_id" not in exact.text
    multiple = post(
        client,
        headers,
        {
            "make": "Audi",
            "model": "A3",
            "year": "2015",
            "transmission": "automatic",
        },
    ).json()["match"]
    assert multiple["status"] == "MULTIPLE_CANDIDATES"
    assert len(multiple["candidates"]) == 2
    assert "1.8" in multiple["question"] and "2.0" in multiple["question"]
    az_multiple = client.post(
        BASE,
        headers=headers,
        json={
            "input_type": "MANUAL",
            "language": "az",
            "fields": {"make": "Audi", "model": "A3", "year": "2015", "transmission": "automatic"},
        },
    ).json()["match"]
    assert az_multiple["status"] == "MULTIPLE_CANDIDATES"
    assert "Mühərrikin" in az_multiple["question"]
    conflict = post(
        client,
        headers,
        {
            "make": "Chevrolet",
            "model": "Cruze",
            "year": "2017",
            "engine": "3.5 L",
        },
    ).json()["match"]
    assert conflict["status"] == "CLAIM_CONFLICT"
    assert conflict["conflicts"] == [
        {
            "field_name": "engine",
            "claimed": "3.5 L",
            "catalog_values": ["1.4"],
        }
    ]
    assert (
        post(client, headers, {"make": "Ferrari", "model": "488", "year": "2017"}).json()["match"][
            "status"
        ]
        == "OUT_OF_PRODUCT_SCOPE"
    )
    assert (
        post(client, headers, {"make": "Audi", "model": "A3", "year": "2024"}).json()["match"][
            "status"
        ]
        == "NO_MATCH"
    )


def test_ambiguity_question_and_conflict_values_do_not_echo_english_technical_prose():
    rows = [
        record(
            "one", "Audi", "A3", 2018, "2.0 gasoline inline-4", "2.0",
            "8-speed torque-converter automatic", "Front",
        ),
        record(
            "two", "Audi", "A3", 2018, "2.0 gasoline inline-4", "2.0",
            "7-speed dual-clutch automatic", "Front",
        ),
    ]
    assert intake._question(rows, {}, "ru") == "Какая коробка указана?"
    assert intake._question(rows, {}, "az") == "Hansı sürətlər qutusu göstərilib?"
    assert intake._conflict_display("transmission", "8-speed torque-converter automatic", "ru") == (
        "Автоматическая"
    )
    assert intake._conflict_display("drivetrain", "Front", "az") == "Ön"


def test_vin_claim_can_continue_to_existing_mock_flow(client, production_rows):
    headers = auth(client)
    with_vin = post(
        client,
        headers,
        {
            "make": "Chevrolet",
            "model": "Cruze",
            "year": "2017",
            "vin": FIXTURE_VIN,
        },
    ).json()
    claims = {claim["field_name"]: claim for claim in with_vin["claims"]}
    assert claims["vin"]["normalized_value"] == FIXTURE_VIN
    preview = client.post(
        "/api/v1/vin/history/checks",
        headers=headers,
        json={
            "vin": claims["vin"]["normalized_value"],
            "language": "ru",
        },
    )
    assert preview.status_code == 201, preview.text
    assert "events" not in preview.text
    without_vin = post(client, headers, {"make": "Audi", "model": "A3", "year": "2015"})
    assert "vin" not in {claim["field_name"] for claim in without_vin.json()["claims"]}
    invalid = post(
        client,
        headers,
        {
            "make": "Chevrolet",
            "model": "Cruze",
            "year": "2017",
            "vin": "1HGCM82633A004353",
        },
    ).json()
    vin_claim = next(c for c in invalid["claims"] if c["field_name"] == "vin")
    assert vin_claim["raw_value"] == "1HGCM82633A004353"
    assert vin_claim["normalized_value"] is None


def test_production_safe_projection_is_explicit(monkeypatch):
    calls = []
    safe = record("safe", "Audi", "A3", 2015, "1.8 TFSI", "1.8", "6-speed dual-clutch", "FWD")

    def records(db, *, production_safe=False):
        calls.append(production_safe)
        return (
            [safe]
            if production_safe
            else [
                safe,
                record("internal", "Audi", "A3", 2015, "EPA_INTERNAL_ONLY", "1.8", "A1", "FWD"),
            ]
        )

    monkeypatch.setattr(intake.buyer, "records", records)
    monkeypatch.setattr(intake.buyer, "active_us_rows", lambda rows: rows)
    rows = intake._consumer_rows(None)
    assert calls == [True]
    assert len(rows) == 1 and "EPA_INTERNAL_ONLY" not in str(rows)


def test_legacy_buyer_listing_route_is_reference_only(client, monkeypatch):
    def never_fetch(*args, **kwargs):
        raise AssertionError("Legacy listing route must not fetch an arbitrary URL")

    monkeypatch.setattr("app.providers.listings.fetch_public", never_fetch)
    response = client.post(
        "/api/v1/reports/buyer/listings",
        headers=auth(client),
        json={"url": "https://turbo.az/autos/10506644-toyota-corolla"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "UNAVAILABLE"
    assert response.json()["reason"] == "USER_CONTENT_REQUIRED"
    blocked = client.post(
        "/api/v1/reports/buyer/listings",
        headers=auth(client),
        json={"url": "https://localhost/private"},
    )
    assert blocked.status_code == 422

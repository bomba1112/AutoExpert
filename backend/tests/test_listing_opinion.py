# ruff: noqa: E501, F811
"""The Auto Expert opinion (UI-by-reference prompt, sections 3-4): what was pasted is recognised,
a listing page is fetched once a day at most, the model always equals the listing's and the link's
(the Stinger -> "Kia K5 2023" regression), a model we do not have is never replaced by a similar
one, discrepancies, the checklist, recalls and the next service by the listing's mileage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import get_settings
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel
from app.models.research import ProviderCacheEntry
from app.services import listing_opinion as lo
from tests.test_us_tech_facts import ICE, camry, fact, generation  # noqa: F401

STINGER_URL = "https://turbo.az/autos/10556520-kia-stinger"


def page(make, model, year=2018, engine="2.0 L / 247 a.g. / Benzin", gearbox="Avtomat (AT)", drive="Arxa", km="70 000 km", market="Amerika"):
    rows = {"Marka": make, "Model": model, "Buraxılış ili": str(year), "Mühərrik": engine, "Sürətlər qutusu": gearbox,
            "Ötürücü": drive, "Yürüş": km, "Şəhər": "Bakı", "Hansı bazar üçün yığılıb": market}
    items = "".join(f'<div class="product-properties__i"><span class="product-properties__i-name">{k}</span>'
                    f'<span class="product-properties__i-value">{v}</span></div>' for k, v in rows.items() if v)
    return f'<html><head><meta property="og:title" content="{make} {model}"></head><body>{items}' \
           f'<div class="product-price__i">29 400 ₼</div></body></html>'


def fetcher(html, calls=None):
    from app.providers.listings import parse_listing

    def fetch(url):
        if calls is not None:
            calls.append(url)
        return {"status": "IMPORTED", "data": parse_listing(html, url)}
    return fetch


@pytest.fixture
def kia_k5(db_session):
    """A make with a K5 (the model the bug showed) and no Stinger, as in our database."""
    make = VehicleMake(name="Kia", normalized_name="kia")
    model = VehicleModel(make=make, name="K5", normalized_name="k5")
    gen = VehicleGeneration(model=model, name="DL3", code="DL3", start_year=2021, end_year=2025)
    from app.models.evidence import SourceRecord

    source = SourceRecord(title="EPA", publisher="EPA", url="https://example.test/epa", source_type="OFFICIAL_DATABASE",
                          retrieved_at=datetime(2026, 1, 1, tzinfo=UTC), confidence="HIGH")
    db_session.add_all([make, model, gen, source])
    db_session.flush()
    g = {"make": make, "gen": gen, "source": source, "db": db_session}
    fact(g, "configuration", "kia-k5-us-2023-1.6l", level="CONFIGURATION", config="kia-k5-us-2023-1.6l", years=(2023, 2023),
         extra={"identity": {"powertrain": "ICE", "drivetrain": "FWD", "displacement_l": "1.6", "epa_transmission": "Automatic (S8)"}})
    db_session.commit()
    return g


@pytest.fixture(autouse=True)
def flag():
    settings = get_settings()
    original = settings.expert_opinion_v1, settings.environment
    yield
    settings.expert_opinion_v1, settings.environment = original


# --- what was pasted -------------------------------------------------------------------------------
@pytest.mark.parametrize("value,kind", [
    (STINGER_URL, "LINK"), ("turbo.az/autos/10556520-kia-stinger", "LINK"), ("1HGCM82633A004352", "VIN"),
    ("1hgcm 82633a004352", "VIN"), ("10-AB-123", "PLATE"), ("90 KL 456", "PLATE"), ("Toyota Camry 2020", "TEXT"), ("hello", "UNKNOWN")])
def test_input_is_recognised(value, kind):
    assert lo.classify(value) == kind


def test_the_link_names_the_model():
    assert lo.url_slug(STINGER_URL) == "kia-stinger"
    assert lo.slug_agrees("kia-stinger", "Kia", "Stinger")
    assert not lo.slug_agrees("kia-stinger", "Kia", "K5")
    assert not lo.slug_agrees("kia-k5", "Kia", "Stinger")
    assert lo.slug_agrees("mercedes-benz-e-220", "Mercedes-Benz", "E 220")
    assert lo.slug_agrees("hyundai-sonata", "Hyundai", "Sonata")
    assert not lo.slug_agrees("hyundai-sonata", "Kia", "Sonata")
    assert lo.slug_agrees(None, "Kia", "Stinger")  # a link without the name: the page alone says it


def test_seller_claims_become_codes():
    c = lo.normalize_listing({"make": "Kia", "model": "Stinger", "year": 2018, "engine": "2.0 L / 247 a.g. / Benzin",
                              "transmission": "Avtomat (AT)", "drivetrain": "Arxa", "market_claim": "Amerika", "mileage_km": 70000})
    assert (c["displacement_l"], c["power_hp"], c["fuel"], c["transmission"], c["drivetrain"], c["market"]) == (2.0, 247, "GASOLINE", "AT", "RWD", "US")
    assert lo.normalize_listing({"engine": "1600"})["displacement_l"] == 1.6
    assert lo.normalize_listing({"engine": "247 a.g."})["displacement_l"] is None


# --- the Stinger regression ------------------------------------------------------------------------
def test_stinger_link_never_becomes_another_kia(db_session, kia_k5):
    result = lo.opinion(db_session, query=STINGER_URL, fetch=fetcher(page("Kia", "Stinger")))
    assert result["status"] == "MODEL_NOT_IN_BASE"
    assert "Stinger" in result["message"] and "K5" not in result["message"]
    assert result.get("model") is None and "configuration" not in result


def test_page_and_link_disagree_is_an_error(db_session, kia_k5):
    result = lo.opinion(db_session, query="https://turbo.az/autos/10556520-kia-k5", fetch=fetcher(page("Kia", "Stinger")))
    assert result["status"] == "MODEL_MISMATCH" and "configuration" not in result
    result = lo.opinion(db_session, query=STINGER_URL + "?x", fetch=fetcher(page("Kia", "K5", 2023)))
    assert result["status"] == "MODEL_MISMATCH"


def test_result_model_always_equals_the_listing(db_session, kia_k5, camry):
    for url, html in ((STINGER_URL, page("Kia", "Stinger")), ("https://turbo.az/autos/1234567-kia-k5", page("Kia", "K5", 2023, "1.6 L / 180 a.g. / Benzin")),
                      ("https://turbo.az/autos/7654321-toyota-camry", page("Toyota", "Camry", 2020, "2.5 L / 203 a.g. / Benzin", drive="Ön"))):
        result = lo.opinion(db_session, query=url, fetch=fetcher(html))
        claimed = result.get("claims") or {}
        if result["status"] == "OK":
            assert (result["make"], result["model"]) == (claimed["make"], claimed["model"])
            assert lo.slug_agrees(lo.url_slug(url), result["make"], result["model"])
        else:
            assert result["status"] in ("MODEL_NOT_IN_BASE", "YEAR_NOT_IN_BASE") and result.get("model") is None


def test_no_similar_model_is_substituted(db_session, camry):
    for model in ("Camr", "Camry Solara", "Corolla"):
        assert lo.find_model(db_session, "Toyota", model)[1] is None
    assert lo.find_model(db_session, "toyota", "camry") == ("Toyota", "Camry")
    assert lo.find_model(db_session, "Lada", "Granta") == (None, None)
    assert lo.model_names("BMW", "328i") == ["328i", "3 Series"]
    assert "E-Class" in lo.model_names("Mercedes-Benz", "E 220")


# --- the opinion -----------------------------------------------------------------------------------
def test_listing_opinion(db_session, camry):
    html = page("Toyota", "Camry", 2020, "2.5 L / 203 a.g. / Benzin", drive="Ön", km="87 000 km")
    result = lo.opinion(db_session, query="https://turbo.az/autos/7654321-toyota-camry", fetch=fetcher(html), language="ru")
    assert result["status"] == "OK" and result["configuration"]["key"] == ICE and result["confirmed"]
    assert result["claims"]["mileage_km"] == 87000 and result["seller_label"] == "указано в объявлении"
    assert result["discrepancies"] == []
    titles = [i["title"] for i in result["weak_points"]]
    assert "Disputed issue" not in titles and "V6 only issue" not in titles  # HIDDEN_CONFLICT, another engine
    assert [c["number"] for c in result["campaigns"]] == ["20V682000"]
    assert any("20V682000" in c["text"] for c in result["checklist"] if c["kind"] == "recall")
    assert any("Check by VIN." in c["text"] for c in result["checklist"] if c["kind"] == "issue")
    assert len(result["checklist"]) <= lo.MAX_ISSUES + lo.MAX_RECALLS
    assert not any("rattle" in c["text"] for c in result["checklist"])  # owner reports stay in the weak points
    jobs = [s["job"] for s in result["next_service"]]
    assert "spark_plugs" not in jobs and "engine_oil_and_filter" not in jobs  # hidden; oil needs the owner's interval
    assert all(s["next_km"] > 87000 for s in result["next_service"] if s["next_km"])
    assert result["summary"] and any("VIN" in s for s in result["summary"])
    assert result["source"]["kind"] == "LINK" and not result["vin_check"]


def test_discrepancies_and_market_note(db_session, camry):
    html = page("Toyota", "Camry", 2020, "3.0 L / 300 a.g. / Benzin", drive="Tam", market="Koreya")
    result = lo.opinion(db_session, query="https://turbo.az/autos/7654321-toyota-camry", fetch=fetcher(html), language="en")
    assert result["status"] == "OK"
    fields = {d["field"] for d in result["discrepancies"]}
    assert fields == {"displacement_l", "drivetrain"}
    assert any("Korea" in n for n in result["notes"])


def test_year_and_model_missing_are_said(db_session, camry):
    result = lo.opinion(db_session, manual={"make": "Toyota", "model": "Camry", "year": 2012})
    assert result["status"] == "YEAR_NOT_IN_BASE" and 2020 in result["years"]
    result = lo.opinion(db_session, manual={"make": "Toyota", "model": "Supra", "year": 2020})
    assert result["status"] == "MODEL_NOT_IN_BASE" and "Supra" in result["message"]


def test_manual_and_text_inputs(db_session, camry):
    manual = lo.opinion(db_session, manual={"make": "Toyota", "model": "Camry", "year": 2020, "engine": "2.5", "fuel": "Hibrid"})
    assert manual["status"] == "OK" and manual["configuration"]["key"].endswith("hev-a-av-s6-fwd")
    text = lo.opinion(db_session, query="Toyota Camry 2020")
    assert text["status"] == "OK" and not text["confirmed"] and text["alternatives"]


def test_plate_is_honest(db_session):
    assert lo.opinion(db_session, query="10-AB-123")["status"] == "PLATE_UNAVAILABLE"


def test_unreachable_page_offers_to_paste_text(db_session, camry):
    result = lo.opinion(db_session, query=STINGER_URL, fetch=lambda url: {"status": "UNAVAILABLE", "reason": "SOURCE_RESTRICTED"})
    assert result["status"] == "LISTING_UNAVAILABLE" and result["paste_text"]
    pasted = lo.opinion(db_session, text="Toyota Camry\nMarka: Toyota\nModel: Camry\nBuraxılış ili: 2020\nYürüş: 87 000 km")
    assert pasted["status"] == "OK" and pasted["model"] == "Camry" and pasted["source"]["kind"] == "PASTED_TEXT"


def test_a_page_is_fetched_once_a_day(db_session, camry):
    calls = []
    fetch = fetcher(page("Toyota", "Camry", 2020, "2.5 L / 203 a.g. / Benzin", drive="Ön"), calls)
    url = "https://turbo.az/autos/7654321-toyota-camry"
    assert lo.opinion(db_session, query=url, fetch=fetch)["source"]["cached"] is False
    assert lo.opinion(db_session, query=url, fetch=fetch)["source"]["cached"] is True
    assert calls == [url]
    entry = db_session.query(ProviderCacheEntry).filter_by(provider_id=lo.PROVIDER).one()
    entry.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.flush()
    lo.opinion(db_session, query=url, fetch=fetch)
    assert calls == [url, url]
    failing = []
    lo.fetch_listing(db_session, "https://turbo.az/autos/1111111-kia-rio", lambda u: failing.append(u) or {"status": "UNAVAILABLE"})
    lo.fetch_listing(db_session, "https://turbo.az/autos/1111111-kia-rio", lambda u: failing.append(u) or {"status": "UNAVAILABLE"})
    assert len(failing) == 2  # failures are not kept


def test_browser_headers_and_timeout_reach_the_fetch(monkeypatch):
    from app.providers import listings

    seen = {}
    monkeypatch.setattr(listings, "import_listing", lambda url, **kw: seen.update(kw) or {"status": "UNAVAILABLE"})
    lo.default_fetch(STINGER_URL)
    assert "Mozilla" in seen["headers"]["User-Agent"] and seen["timeout"] == lo.FETCH_TIMEOUT


# --- the API ---------------------------------------------------------------------------------------
def test_api_behind_the_flag(client, camry, monkeypatch):
    token = client.post("/api/v1/auth/demo", json={"preferred_language": "ru"}).json()["access_token"]
    h = {"X-AutoExpert-Token": token}
    assert client.post("/api/v1/expert/opinion", json={"query": "Toyota Camry 2020"}).status_code == 401
    r = client.post("/api/v1/expert/opinion", json={"query": "Toyota Camry 2020", "language": "en"}, headers=h)
    assert r.status_code == 200 and r.json()["status"] == "OK"
    assert client.post("/api/v1/expert/opinion", json={}, headers=h).status_code == 422
    settings = get_settings()
    settings.expert_opinion_v1 = False
    assert client.post("/api/v1/expert/opinion", json={"query": "Toyota Camry 2020"}, headers=h).status_code == 404
    settings.expert_opinion_v1, settings.environment = None, "production"
    assert not lo.enabled()


def test_client_config_advertises_the_flag(client):
    settings = get_settings()
    settings.expert_opinion_v1 = True
    assert client.get("/api/v1/meta/client-config").json()["expert_opinion_v1"] == {"enabled": True}
    settings.expert_opinion_v1 = False
    assert "expert_opinion_v1" not in client.get("/api/v1/meta/client-config").json()

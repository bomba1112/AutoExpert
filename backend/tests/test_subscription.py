# ruff: noqa: E501
"""The subscription model (product phase, stage 6): free rights (one car, the basic schedule,
reading the club), subscription rights (several cars, personal hints and recall alerts, the AI
mechanic, writing in the club, the PDF log), the trial once, the store stub outside production
only, cancellation keeping the paid period, prices per region, and the flag."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import get_settings
from app.models.subscription import Subscription
from app.models.user import User
from app.services import entitlements
from tests.test_club import _generation_room, gen, settings  # noqa: F401
from tests.test_garage import _headers, car  # noqa: F401
from tests.test_us_tech_facts import ICE, generation  # noqa: F401


@pytest.fixture
def paywall():
    s = get_settings()
    original = s.subscription_v1, s.environment
    s.subscription_v1 = True
    yield s
    s.subscription_v1, s.environment = original


def _add_car(client, h):
    return client.post("/api/v1/garage/vehicles?language=en", json={"configuration_key": ICE, "odometer": 1000}, headers=h)


def test_free_rights(car, client, paywall):  # noqa: F811
    h = _headers(client)
    first = _add_car(client, h)
    assert first.status_code == 201
    view = first.json()
    assert view["services"] and view["weak_points"] == [] and "PERSONAL_HINTS" in view["locked"]  # personal hints locked
    second = _add_car(client, h)
    assert second.status_code == 402 and second.json()["detail"] == {"code": "SUBSCRIPTION_REQUIRED", "feature": "GARAGE_MULTIPLE_CARS"}
    vid = view["id"]
    assert client.get(f"/api/v1/garage/vehicles/{vid}/service-log.pdf", headers=h).status_code == 402
    asked = client.post(f"/api/v1/garage/vehicles/{vid}/mechanic", json={"question": "oil?"}, headers=h)
    assert asked.status_code == 402 and asked.json()["detail"]["feature"] == "AI_MECHANIC"
    feed = client.get("/api/v1/garage/feed?language=en", headers=h).json()
    assert not any(f["kind"] == "RECALL" for f in feed)  # recall alerts are a subscription right
    offer = client.get("/api/v1/subscription?language=en", headers=h).json()
    assert offer["tier"] == "FREE" and offer["rights"]["GARAGE_ONE_CAR"] and not offer["rights"]["AI_MECHANIC"]
    assert offer["trial"] == {"days": 7, "available": True}


def test_trial_unlocks_everything_once(car, client, paywall):  # noqa: F811
    h = _headers(client)
    vid = _add_car(client, h).json()["id"]
    started = client.post("/api/v1/subscription/trial?language=ru", headers=h)
    assert started.status_code == 201 and started.json()["tier"] == "SUBSCRIPTION" and started.json()["status"] == "TRIAL"
    assert _add_car(client, h).status_code == 201
    assert client.get(f"/api/v1/garage/vehicles/{vid}/service-log.pdf", headers=h).status_code == 200
    view = client.get(f"/api/v1/garage/vehicles/{vid}?language=en", headers=h).json()
    assert view["locked"] == {} and view["recall_alerts"] is True
    assert client.post("/api/v1/subscription/trial", headers=h).status_code == 409


def test_expired_trial_returns_to_free(car, client, db_session, paywall):  # noqa: F811
    h = _headers(client)
    client.post("/api/v1/subscription/trial", headers=h)
    sub = db_session.query(Subscription).one()
    sub.period_end = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()
    offer = client.get("/api/v1/subscription", headers=h).json()
    assert offer["tier"] == "FREE" and offer["trial"]["available"] is False
    assert db_session.query(Subscription).one().status == "EXPIRED"


def test_store_stub_outside_production_only_and_cancel_keeps_the_period(car, client, paywall):  # noqa: F811
    h = _headers(client)
    bought = client.post("/api/v1/subscription/purchase", json={"store": "APP_STORE"}, headers=h).json()
    assert bought["status"] == "ACTIVE" and bought["store"] == "STUB" and bought["purchase_stub"] is True
    canceled = client.post("/api/v1/subscription/cancel", headers=h).json()
    assert canceled["status"] == "CANCELED" and canceled["tier"] == "SUBSCRIPTION"  # until the period ends
    paywall.environment = "production"  # the same signed-in user; no stub purchase in production
    r = client.post("/api/v1/subscription/purchase", json={"store": "GOOGLE_PLAY"}, headers=h)
    assert r.status_code == 501 and r.json()["detail"] == "STORE_NOT_CONNECTED"


def test_club_writing_is_a_subscription_right(gen, client, paywall):  # noqa: F811
    h = _headers(client)
    room = _generation_room(client, h)
    assert client.get(f"/api/v1/club/rooms/{room}", headers=h).status_code == 200  # reading is free
    r = client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Hello owners"}, headers=h)
    assert r.status_code == 402 and r.json()["detail"]["feature"] == "CLUB_WRITE"
    client.post("/api/v1/subscription/trial", headers=h)
    assert client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Hello owners"}, headers=h).status_code == 201


def test_prices_per_region_from_the_configuration(db_session):
    us = User(email="a@example.com", password_hash="x", country_code="US")
    az = User(email="b@example.com", password_hash="x", country_code="AZ")
    other = User(email="c@example.com", password_hash="x", preferred_language="az")
    assert entitlements.price(entitlements.region_of(us)) == {"currency": "USD", "monthly_minor": 399}
    assert entitlements.price(entitlements.region_of(az)) == {"currency": "AZN", "monthly_minor": 100}
    assert entitlements.region_of(other) == "AZ"
    assert entitlements.price("XX")["currency"] == "USD"
    demo_en = User(email="demo-1@demo.autoexpert.invalid", password_hash="x", country_code="AZ", preferred_language="en")
    assert entitlements.region_of(demo_en) == "US"  # a preview demo session follows its language


def test_flag_off_grants_everything(car, client, db_session):  # noqa: F811
    assert get_settings().subscription_v1 is False  # the test default
    h = _headers(client)
    assert _add_car(client, h).status_code == 201 and _add_car(client, h).status_code == 201
    assert client.get("/api/v1/subscription", headers=h).status_code == 404
    admin = User(email="admin@example.com", password_hash="x", is_admin=True)
    s = get_settings()
    s.subscription_v1 = True
    try:
        assert entitlements.allows(db_session, admin, "AI_MECHANIC")
        assert "subscription_v1" in client.get("/api/v1/meta/client-config").json()
    finally:
        s.subscription_v1 = False

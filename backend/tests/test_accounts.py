# ruff: noqa: E501
"""Account readiness for the owners club (product phase, stage 4): email confirmation, password
reset without address enumeration, single-use expiring tokens, older sessions revoked after a
reset, and the brute-force lock on login."""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime, timedelta

from app.models.account import AuthToken, OutboxMessage
from app.models.user import User
from app.services import accounts

PASSWORD = "correct-horse-battery"


def _register(client, email="owner@example.com"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD, "preferred_language": "en"})
    assert r.status_code == 201, r.text
    return r.json()


def _link_token(db_session, purpose, email="owner@example.com"):
    message = db_session.query(OutboxMessage).filter_by(purpose=purpose, recipient=email).order_by(OutboxMessage.created_at.desc()).first()
    return re.search(r"/(?:verify-email|reset-password)/([\w-]+)", message.body).group(1), message


def test_registration_sends_a_confirmation_and_the_link_confirms(client, db_session):
    data = _register(client)
    assert data["user"]["email_verified_at"] is None
    token, message = _link_token(db_session, "VERIFY_EMAIL")
    assert message.subject == "Confirm your email — Auto Expert" and message.channel == "EMAIL"
    assert token not in {t.token_hash for t in db_session.query(AuthToken)}  # only the hash is stored
    confirmed = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert confirmed.status_code == 200 and confirmed.json()["email_verified_at"]
    assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 400  # single use


def test_password_reset_does_not_reveal_addresses(client, db_session):
    _register(client)
    known = client.post("/api/v1/auth/password-reset/request", json={"email": "owner@example.com"})
    unknown = client.post("/api/v1/auth/password-reset/request", json={"email": "nobody@example.com"})
    assert known.status_code == unknown.status_code == 202 and known.json() == unknown.json()
    assert db_session.query(OutboxMessage).filter_by(purpose="RESET_PASSWORD").count() == 1


def test_password_reset_revokes_older_sessions(client, db_session):
    old_token = _register(client)["access_token"]
    old = {"Authorization": f"Bearer {old_token}"}
    assert client.post("/api/v1/auth/verify-email/resend", headers=old).status_code == 202
    client.post("/api/v1/auth/password-reset/request", json={"email": "owner@example.com"})
    token, _ = _link_token(db_session, "RESET_PASSWORD")
    time.sleep(1.1)  # the new password is set after the old session was issued
    reset = client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "password": "a-brand-new-password"})
    assert reset.status_code == 200
    assert client.post("/api/v1/auth/verify-email/resend", headers=old).status_code == 401
    new = {"Authorization": f"Bearer {reset.json()['access_token']}"}
    assert client.post("/api/v1/auth/verify-email/resend", headers=new).status_code == 202
    assert client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "a-brand-new-password"}).status_code == 200
    assert client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "password": "another-password-1"}).status_code == 400


def test_expired_token_is_refused(db_session):
    user = User(email="late@example.com", password_hash="x")
    db_session.add(user)
    db_session.flush()
    raw = accounts.issue_token(db_session, user, "RESET_PASSWORD")
    db_session.flush()
    token = db_session.query(AuthToken).filter_by(user_id=user.id).one()
    token.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    assert accounts.consume_token(db_session, raw, "RESET_PASSWORD") is None
    assert accounts.consume_token(db_session, raw, "VERIFY_EMAIL") is None


def test_login_is_locked_after_repeated_failures(client):
    _register(client)
    for _ in range(accounts.MAX_PER_EMAIL):
        assert client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "wrong-password"}).status_code == 401
    blocked = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD})
    assert blocked.status_code == 429  # even the right password waits 15 minutes
    assert client.post("/api/v1/auth/login", json={"email": "other@example.com", "password": "x"}).status_code == 401


def test_inactive_account_gets_no_token_and_the_same_answer_as_a_wrong_password(client, db_session):
    _register(client)
    ok = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD})
    assert ok.status_code == 200 and ok.json()["access_token"]  # an active account signs in
    wrong = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "wrong-password"})
    user = db_session.query(User).filter_by(email="owner@example.com").one()
    user.is_active = False
    db_session.commit()
    inactive = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD})
    assert inactive.status_code == 401 and "access_token" not in inactive.json()
    assert inactive.json() == wrong.json()  # nothing tells that the account exists


def test_club_writing_needs_a_confirmed_email(db_session):
    from app.core.config import get_settings

    settings = get_settings()
    original = settings.environment
    try:
        user = User(email="w@example.com", password_hash="x")
        demo = User(email="demo-1@demo.autoexpert.invalid", password_hash="x")
        settings.environment = "production"
        assert not accounts.can_write(user) and not accounts.can_write(demo)
        user.email_verified_at = datetime.now(UTC)
        assert accounts.can_write(user)
        settings.environment = "development"
        assert accounts.can_write(demo)
    finally:
        settings.environment = original


def test_the_app_token_travels_next_to_the_site_basic_auth(client):
    """Closed staging: Authorization carries the site's Basic Auth (the browser attaches it), the
    app's token goes in X-AutoExpert-Token; Authorization: Bearer keeps working."""
    token = _register(client)["access_token"]
    basic = "Basic " + __import__("base64").b64encode(b"site:password").decode()
    path = "/api/v1/auth/verify-email/resend"
    assert client.post(path, headers={"Authorization": basic, "X-AutoExpert-Token": token}).status_code == 202
    assert client.post(path, headers={"X-AutoExpert-Token": f"Bearer {token}"}).status_code == 202
    assert client.post(path, headers={"Authorization": f"Bearer {token}"}).status_code == 202
    only_basic = client.post(path, headers={"Authorization": basic})
    assert only_basic.status_code == 401 and only_basic.headers["www-authenticate"] == "Bearer"
    assert client.post(path, headers={"X-AutoExpert-Token": "not-a-token"}).status_code == 401

# ruff: noqa: E501
"""The owners club (product phase, stage 4): rooms and starter topics from the database (hidden
conflicts never), access rights (confirmed email, bans, moderators only for moderation),
automatic filter and reports, the review queue into OWNER_REPORTS only after a moderator, photos
without metadata, and no personal data in any response."""

from __future__ import annotations

import io
import json

import pytest
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.club import ClubModerationLog, ClubReviewItem
from app.models.evidence import KnownIssue
from app.models.user import User
from app.services import club, us_tech_facts
from tests.test_garage import _headers  # noqa: F401
from tests.test_us_tech_facts import ICE, configuration, generation  # noqa: F401


@pytest.fixture
def settings(tmp_path):
    s = get_settings()
    original = (s.environment, s.owners_club_v1, s.club_review_threshold, s.club_media_dir, s.club_ai_moderation)
    s.club_media_dir = str(tmp_path / "media")
    club._ROOMS_READY.clear()
    yield s
    s.environment, s.owners_club_v1, s.club_review_threshold, s.club_media_dir, s.club_ai_moderation = original
    club._ROOMS_READY.clear()


@pytest.fixture
def gen(generation, db_session, settings):  # noqa: F811
    g = generation
    configuration(g, ICE, "ICE", "A25A-FKS", "Automatic (S8)", ["Camry LE/SE"])

    def issue(title, display, severity="HIGH"):
        db_session.add(KnownIssue(component="engine", title=title, description=title, symptoms=["stall"], severity=severity,
                                  confidence="HIGH", inspection_recommendation="Check by VIN.", status="CONFIRMED",
                                  scope_level="GENERATION", display_level=display, make_id=g["make"].id, generation_id=g["gen"].id,
                                  year_from=2018, year_to=2024, data_origin="REAL", is_demo=False))

    issue("Fuel pump failure", "FACT")
    issue("Water pump leak", "SECONDARY_NOTE", "MEDIUM")
    issue("Infotainment freezes", "OWNER_REPORTS", "LOW")
    issue("Secret conflicting claim", "HIDDEN_CONFLICT")
    db_session.commit()
    us_tech_facts.clear_cache()
    return g


def _admin(client, db_session):
    user = User(email="moderator@example.com", password_hash="x", is_admin=True)
    db_session.add(user)
    db_session.commit()
    return {"Authorization": f"Bearer {create_access_token(user.id, is_admin=True)}"}


def _generation_room(client, h):
    makes = client.get("/api/v1/club/rooms?language=en", headers=h).json()["makes"]
    make_room = client.get(f"/api/v1/club/rooms/{makes[0]['id']}?language=en", headers=h).json()
    return make_room["generations"][0]["id"]


def test_rooms_and_starter_topics_from_the_database(gen, client):
    h = _headers(client)
    makes = client.get("/api/v1/club/rooms?language=en", headers=h).json()["makes"]
    assert [m["title"] for m in makes] == ["Toyota"] and makes[0]["generations"] == 1
    room = client.get(f"/api/v1/club/rooms/{_generation_room(client, h)}?language=en", headers=h).json()
    assert room["title"].startswith("Toyota Camry XV70 (2020")
    titles = {p["title"]: p for p in room["posts"]}
    assert set(titles) == {"Fuel pump failure", "Water pump leak", "Infotainment freezes"}  # the hidden conflict never
    assert titles["Water pump leak"]["mark"] == "per reference sources"
    assert titles["Infotainment freezes"]["mark"] == "owners report"
    assert titles["Fuel pump failure"]["author"] == "Auto Expert · from our database" and "Check by VIN." in titles["Fuel pump failure"]["body"]
    # starters are created once
    again = client.get(f"/api/v1/club/rooms/{room['id']}", headers=h).json()
    assert len(again["posts"]) == 3


def test_room_from_the_garage_car(gen, client):
    h = _headers(client)
    vid = client.post("/api/v1/garage/vehicles", json={"configuration_key": ICE, "odometer": 1000}, headers=h).json()["id"]
    rooms = client.get(f"/api/v1/club/vehicles/{vid}/rooms?language=ru", headers=h).json()
    assert [r["kind"] for r in rooms] == ["GENERATION", "MAKE"]
    assert client.get("/api/v1/club/rooms", headers=h).json()["mine"][0]["vehicle"] == "Toyota Camry 2020"


def test_writing_rights(gen, client, db_session, settings):
    h = _headers(client)
    room = _generation_room(client, h)
    assert client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Hello owners"}, headers=h).status_code == 201  # preview demo
    registered = client.post("/api/v1/auth/register", json={"email": "real@example.com", "password": "long-enough-password"}).json()
    rh = {"Authorization": f"Bearer {registered['access_token']}"}
    r = client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Unconfirmed post"}, headers=rh)
    assert r.status_code == 403 and r.json()["detail"] == "EMAIL_NOT_CONFIRMED"
    settings.environment = "production"
    settings.owners_club_v1 = True  # production with the flag on: demo sessions cannot write either
    assert not club.accounts.can_write(db_session.query(User).filter(User.email.like("demo-%")).first())


def test_personal_data_never_leaks(gen, client, db_session):
    h = _headers(client)
    room = _generation_room(client, h)
    post = client.post(f"/api/v1/club/rooms/{room}/posts?language=en",
                       json={"title": "Selling parts", "body": "Write me at john.doe@mail.com or call +994 50 123 45 67"}, headers=h).json()
    assert "john.doe" not in post["body"] and "123 45 67" not in post["body"] and post["body"].count("[hidden]") == 2
    other = _headers(client)
    payloads = [client.get(f"/api/v1/club/rooms/{room}", headers=other).text, client.get(f"/api/v1/club/posts/{post['id']}", headers=other).text]
    emails = [u.email for u in db_session.query(User)]
    assert not any(e in p for e in emails for p in payloads)
    assert json.loads(payloads[1])["author"].startswith("Владелец #")
    assert client.patch("/api/v1/club/profile", json={"display_name": "Camry fan"}, headers=h).json() == {"display_name": "Camry fan"}
    assert client.get(f"/api/v1/club/posts/{post['id']}", headers=other).json()["author"] == "Camry fan"


def test_autofilter_holds_and_moderator_restores(gen, client, db_session):
    h, other, mod = _headers(client), _headers(client), _admin(client, db_session)
    room = _generation_room(client, h)
    held = client.post(f"/api/v1/club/rooms/{room}/posts?language=ru", json={"title": "Эта сука опять сломалась"}, headers=h).json()
    assert held["status"] == "HELD" and held["held_note"] == "На проверке у модератора"
    assert client.get(f"/api/v1/club/posts/{held['id']}", headers=other).status_code == 404
    assert held["id"] not in {p["id"] for p in client.get(f"/api/v1/club/rooms/{room}", headers=other).json()["posts"]}
    spam = client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Deals", "body": "http://a.x http://b.x https://c.x"}, headers=h).json()
    assert spam["status"] == "HELD"
    assert {(r.actor, r.reason) for r in db_session.query(ClubModerationLog)} >= {("AUTOFILTER", "OBSCENE"), ("AUTOFILTER", "SPAM_LINKS")}
    queue = client.get("/api/v1/club/moderation", headers=mod).json()
    assert {p["id"] for p in queue["posts"]} == {held["id"], spam["id"]}
    assert client.post(f"/api/v1/club/moderation/targets/POST/{held['id']}", json={"action": "RESTORE", "reason": "car, not a person"}, headers=mod).json() == {"status": "VISIBLE"}
    assert client.get(f"/api/v1/club/posts/{held['id']}", headers=other).status_code == 200
    # only moderators moderate
    assert client.get("/api/v1/club/moderation", headers=h).status_code == 403
    assert client.post(f"/api/v1/club/moderation/targets/POST/{spam['id']}", json={"action": "RESTORE"}, headers=h).status_code == 403


def test_reports_hide_after_three_and_ban_blocks_writing(gen, client, db_session):
    h, mod = _headers(client), _admin(client, db_session)
    room = _generation_room(client, h)
    post = client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Annoying text"}, headers=h).json()
    reporters = [_headers(client) for _ in range(3)]
    for rh in reporters[:2]:
        assert client.post("/api/v1/club/reports", json={"target_type": "POST", "target_id": post["id"], "reason": "ABUSE"}, headers=rh).status_code == 201
    client.post("/api/v1/club/reports", json={"target_type": "POST", "target_id": post["id"], "reason": "ABUSE"}, headers=reporters[0])  # once per user
    assert client.get(f"/api/v1/club/posts/{post['id']}", headers=reporters[2]).status_code == 200
    client.post("/api/v1/club/reports", json={"target_type": "POST", "target_id": post["id"], "reason": "SPAM"}, headers=reporters[2])
    assert client.get(f"/api/v1/club/posts/{post['id']}", headers=reporters[2]).status_code == 404  # hidden until a moderator looks
    assert len(client.get("/api/v1/club/moderation", headers=mod).json()["reports"]) == 3
    assert client.post("/api/v1/club/moderation/ban", json={"post_id": post["id"], "reason": "abuse", "days": 7}, headers=mod).status_code == 201
    r = client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Am I banned"}, headers=h)
    assert r.status_code == 403 and r.json()["detail"] == "BANNED"
    log = client.get("/api/v1/club/moderation/log", headers=mod).json()
    assert {e["action"] for e in log} >= {"HIDE", "BAN"}


def test_repeated_owner_reports_go_to_review_and_only_then_to_the_database(gen, client, db_session, settings):
    settings.club_review_threshold = 3
    h, mod = _headers(client), _admin(client, db_session)
    room = _generation_room(client, h)
    post = client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Rear brake squeal at low speed", "body": "Every morning"}, headers=h).json()
    for _ in range(2):
        client.post(f"/api/v1/club/posts/{post['id']}/same", headers=_headers(client))
    item = db_session.query(ClubReviewItem).one()
    assert item.owners == 3 and item.status == "PENDING"
    assert not db_session.query(KnownIssue).filter_by(display_level="OWNER_REPORTS", component="owner_report").count()  # not automatic
    done = client.post(f"/api/v1/club/moderation/review/{item.id}", json={"approve": True, "severity": "LOW"}, headers=mod)
    assert done.status_code == 200, done.text
    done = done.json()
    issue = db_session.get(KnownIssue, done["known_issue_id"])
    assert str(issue.display_level.value if hasattr(issue.display_level, "value") else issue.display_level) == "OWNER_REPORTS"
    assert issue.source_count == 3 and issue.conditions["origin"] == "owners_club"
    us_tech_facts.clear_cache()
    weak = us_tech_facts.build(db_session, ICE, "en")["weak_points"]
    owned = next(w for w in weak if w["title"] == "Rear brake squeal at low speed")
    assert owned["owner_reports"] and owned["note"] == "owners report"


def test_photos_lose_their_metadata(gen, client, db_session):
    from PIL import Image

    h = _headers(client)
    room = _generation_room(client, h)
    post = client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Photo of the leak"}, headers=h).json()
    image = Image.new("RGB", (40, 30), "red")
    exif = Image.Exif()
    exif[0x8825] = {2: (40.0, 22.0, 0.0)}  # GPS
    exif[0x010F] = "PhoneMaker"
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", exif=exif)
    up = client.post(f"/api/v1/club/posts/{post['id']}/photos", files={"file": ("leak.jpg", buffer.getvalue(), "image/jpeg")}, headers=h)
    assert up.status_code == 201, up.text
    stored = client.get(f"/api/v1/club{up.json()['url'].removeprefix('/club')}", headers=h)
    assert stored.status_code == 200 and not Image.open(io.BytesIO(stored.content)).getexif()
    bad = client.post(f"/api/v1/club/posts/{post['id']}/photos", files={"file": ("x.jpg", b"not an image", "image/jpeg")}, headers=h)
    assert bad.status_code == 415
    other = _headers(client)
    assert client.post(f"/api/v1/club/posts/{post['id']}/photos", files={"file": ("y.jpg", buffer.getvalue(), "image/jpeg")}, headers=other).status_code == 403


def test_rate_limit_and_duplicates(gen, client):
    h = _headers(client)
    room = _generation_room(client, h)
    assert client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "First", "body": "same text"}, headers=h).status_code == 201
    assert client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Second", "body": "same text"}, headers=h).status_code == 409
    for i in range(4):
        client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": f"Post {i}", "body": f"text {i}"}, headers=h)
    assert client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Too many", "body": "x"}, headers=h).status_code == 429


def test_comments_and_flag(gen, client, settings):
    h, other = _headers(client), _headers(client)
    room = _generation_room(client, h)
    post = client.post(f"/api/v1/club/rooms/{room}/posts", json={"title": "Oil leak?"}, headers=h).json()
    client.post(f"/api/v1/club/posts/{post['id']}/comments", json={"body": "Check the pan gasket"}, headers=other)
    client.post(f"/api/v1/club/posts/{post['id']}/comments", json={"body": "fuck this car"}, headers=other)
    seen = client.get(f"/api/v1/club/posts/{post['id']}", headers=h).json()
    assert [c["body"] for c in seen["comment_list"]] == ["Check the pan gasket"] and seen["comments"] == 1
    assert "owners_club_v1" in client.get("/api/v1/meta/client-config").json()
    settings.owners_club_v1 = False
    assert client.get("/api/v1/club/rooms", headers=h).status_code == 404
    assert "owners_club_v1" not in client.get("/api/v1/meta/client-config").json()


def test_optional_ai_moderation(monkeypatch, settings):
    import httpx

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    original = settings.anthropic_api_key
    try:
        settings.anthropic_api_key = None
        assert club.ai_moderate("anything") is None  # no key: the AI does not hold texts
        settings.anthropic_api_key = "test-key"
        say = lambda word: httpx.MockTransport(lambda r: httpx.Response(200, json={"content": [{"type": "text", "text": word}]}))  # noqa: E731
        assert club.ai_moderate("buy cheap pills", transport=say("SPAM")) == "SPAM"
        assert club.ai_moderate("my brakes squeal", transport=say("ALLOW")) is None
        failing = httpx.MockTransport(lambda r: httpx.Response(500))
        assert club.ai_moderate("text", transport=failing) is None
    finally:
        settings.anthropic_api_key = original

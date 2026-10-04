# ruff: noqa: E501
"""The AI mechanic (product phase, stage 3): the answer contains no number that is not in the
car's data, an honest refusal without data, HIDDEN_CONFLICT never in the context, the Claude call
through the backend (mocked transport), the data-only mode without a key, the per-user limit, the
log and the ai_mechanic_v1 flag."""

from __future__ import annotations

import json

import httpx
import pytest
from app.core.config import get_settings
from app.models.ai_mechanic import AIMechanicRequest
from app.services import ai_mechanic
from tests.test_garage import _headers, _vehicle, car, user  # noqa: F401
from tests.test_us_tech_facts import ICE, fact, generation  # noqa: F401


@pytest.fixture
def settings():
    s = get_settings()
    original = (s.anthropic_api_key, s.ai_mechanic_v1, s.ai_mechanic_daily_limit, s.environment)
    yield s
    s.anthropic_api_key, s.ai_mechanic_v1, s.ai_mechanic_daily_limit, s.environment = original


@pytest.fixture
def no_key(settings, monkeypatch):
    settings.anthropic_api_key = None
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return settings


@pytest.fixture
def hidden(car, db_session):  # noqa: F811
    fact(car, "fuel_tank_l", 60.6, unit="L")
    fact(car, "fuel_tank_l", 59.8, unit="L", display="HIDDEN_CONFLICT")
    db_session.commit()
    from app.services import us_tech_facts

    us_tech_facts.clear_cache()
    return car


def _fact_id(ctx, needle):
    return next(f["id"] for f in ctx["facts"] if needle in f["text"])


def test_hidden_conflict_never_reaches_the_context(hidden, db_session, user):  # noqa: F811
    v = _vehicle(db_session, user.id)
    ctx = ai_mechanic.context(db_session, v, "ru")
    text = "\n".join(f["text"] for f in ctx["facts"])
    assert "60.6" in text and "59.8" not in text
    assert not any(f["key"] == "spark_plugs" for f in ctx["facts"])  # the hidden maintenance row
    assert "ATF WS" in text and "Recall 20V682000" in text


def test_numbers_must_come_from_the_cited_facts(car, db_session, user):  # noqa: F811
    v = _vehicle(db_session, user.id)
    ctx = ai_mechanic.context(db_session, v, "ru")
    atf = _fact_id(ctx, "ATF WS")
    cap = _fact_id(ctx, "7.3")
    draft = {"answer": [{"text": f"Заливается Toyota Genuine ATF WS, 7,3 л [{atf}, {cap}]", "facts": [atf, cap]},
                        {"text": "Меняйте ATF каждые 60 000 км", "facts": [atf]},          # invented interval
                        {"text": "Объём масла 4,8 л", "facts": []}],                      # no source
             "general": [{"text": "Проверяйте уровень на прогретом двигателе."},
                         {"text": "Обычно меняют раз в 2 года."}],                          # a number in general advice
             "not_in_data": ["Объём масла в руководстве не указан"]}
    answer, rejected = ai_mechanic.check(draft, ctx, "Какую жидкость в коробку?", "ru")
    assert [a["text"] for a in answer["answer"]] == ["Заливается Toyota Genuine ATF WS, 7,3 л"]
    assert answer["answer"][0]["facts"][0]["source"]  # every statement keeps its source
    assert [g["text"] for g in answer["general"]] == ["Проверяйте уровень на прогретом двигателе."]
    assert {r["reason"] for r in rejected} == {"NUMBER_NOT_IN_CITED_FACTS", "NO_FACTS_CITED", "NUMBER_IN_GENERAL_ADVICE"}
    assert next(r for r in rejected if r["reason"] == "NUMBER_NOT_IN_CITED_FACTS")["numbers"] == ["60000"]
    # every number left in the answer is a number of the car's data
    shown = " ".join(a["text"] for a in answer["answer"])
    assert ai_mechanic.numbers(shown) <= set().union(*(ai_mechanic.numbers(f["text"]) for f in ctx["facts"]))


def test_honest_refusal_without_data(car, db_session, user):  # noqa: F811
    v = _vehicle(db_session, user.id)
    ctx = ai_mechanic.context(db_session, v, "en")
    answer, _ = ai_mechanic.check({"answer": [{"text": "Refrigerant R-1234yf, 450 g", "facts": ["F1"]}]}, ctx, "A/C refrigerant?", "en")
    assert answer["answer"] == [] and answer["not_in_data"] == [ai_mechanic.tt("en", "refusal")]
    assert "manual" in answer["not_in_data"][0]


def test_claude_through_the_backend(car, db_session, user, settings):  # noqa: F811
    settings.anthropic_api_key = "test-key"
    v = _vehicle(db_session, user.id)
    ctx = ai_mechanic.context(db_session, v, "az")
    atf = _fact_id(ctx, "ATF WS")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["headers"] = dict(request.headers)
        seen["body"] = json.loads(request.content)
        text = json.dumps({"answer": [{"text": "Toyota Genuine ATF WS istifadə olunur", "facts": [atf]},
                                      {"text": "Həcmi 8 litrdir", "facts": [atf]}],
                           "general": [], "not_in_data": []}, ensure_ascii=False)
        return httpx.Response(200, json={"model": "claude-opus-5-5", "content": [{"type": "text", "text": text}],
                                         "usage": {"input_tokens": 1200, "output_tokens": 80}})

    entry = ai_mechanic.ask(db_session, user, v, "Qutuya hansı maye?", "az", transport=httpx.MockTransport(handler))
    assert seen["headers"]["x-api-key"] == "test-key" and seen["headers"]["anthropic-version"]
    assert seen["body"]["model"] == settings.ai_mechanic_model and "Azerbaijani" in seen["body"]["system"]
    assert "ATF WS" in seen["body"]["messages"][-1]["content"]
    assert entry.mode == "CLAUDE" and entry.status == "OK" and (entry.input_tokens, entry.output_tokens) == (1200, 80)
    assert [a["text"] for a in entry.answer["answer"]] == ["Toyota Genuine ATF WS istifadə olunur"]
    assert entry.rejected[0]["numbers"] == ["8"]  # the invented capacity was removed and logged


def test_model_error_falls_back_to_the_cars_data(car, db_session, user, settings):  # noqa: F811
    settings.anthropic_api_key = "test-key"
    v = _vehicle(db_session, user.id)
    entry = ai_mechanic.ask(db_session, user, v, "Какая жидкость в АКПП?", "ru",
                            transport=httpx.MockTransport(lambda r: httpx.Response(529, json={"error": "overloaded"})))
    assert entry.status == "ERROR" and entry.mode == "DATA_ONLY"
    assert any("ATF WS" in a["text"] for a in entry.answer["answer"])


def test_data_only_mode_without_a_key(car, db_session, user, no_key):  # noqa: F811
    v = _vehicle(db_session, user.id)
    entry = ai_mechanic.ask(db_session, user, v, "Какая жидкость в коробку?", "ru")
    assert entry.mode == "DATA_ONLY" and entry.status == "OK"
    assert any("ATF WS" in a["text"] for a in entry.answer["answer"])
    assert entry.answer["mode_note"] == ai_mechanic.tt("ru", "data_only")
    refused = ai_mechanic.ask(db_session, user, v, "Сколько фреона в кондиционере?", "ru")
    assert refused.status == "REFUSED" and refused.answer["not_in_data"] == [ai_mechanic.tt("ru", "refusal")]


def test_api_limit_log_and_flag(car, client, no_key):  # noqa: F811
    h = _headers(client)
    vid = client.post("/api/v1/garage/vehicles", json={"configuration_key": ICE, "odometer": 87000}, headers=h).json()["id"]
    no_key.ai_mechanic_daily_limit = 2
    for _ in range(2):
        r = client.post(f"/api/v1/garage/vehicles/{vid}/mechanic?language=en", json={"question": "Which transmission fluid?"}, headers=h)
        assert r.status_code == 201, r.text
    limited = client.post(f"/api/v1/garage/vehicles/{vid}/mechanic?language=en", json={"question": "And the oil?"}, headers=h)
    assert limited.status_code == 429 and limited.json()["detail"]["code"] == "AI_MECHANIC_LIMIT"
    hist = client.get(f"/api/v1/garage/vehicles/{vid}/mechanic", headers=h).json()
    assert len(hist["items"]) == 2 and hist["used"] == 2 and hist["connected"] is False
    other = _headers(client)
    assert client.post(f"/api/v1/garage/vehicles/{vid}/mechanic", json={"question": "hi there"}, headers=other).status_code == 404
    assert "ai_mechanic_v1" in client.get("/api/v1/meta/client-config").json()
    no_key.ai_mechanic_v1 = False  # one flag switches it off
    assert client.get(f"/api/v1/garage/vehicles/{vid}/mechanic", headers=h).status_code == 404
    assert "ai_mechanic_v1" not in client.get("/api/v1/meta/client-config").json()
    no_key.ai_mechanic_v1, no_key.environment = None, "production"
    assert not ai_mechanic.enabled(no_key)


def test_the_log_keeps_every_request(car, db_session, user, no_key):  # noqa: F811
    v = _vehicle(db_session, user.id)
    ai_mechanic.ask(db_session, user, v, "oil?", "en")
    assert db_session.query(AIMechanicRequest).filter_by(user_id=user.id).count() == 1
    assert ai_mechanic.used_today(db_session, user.id) == 1

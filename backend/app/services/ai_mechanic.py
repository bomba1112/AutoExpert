# ruff: noqa: E501
"""The AI mechanic of a Garage car (product phase, stage 3), behind the ai_mechanic_v1 flag.

The answer is built only from this car's data: the published rows of its configuration
(us_tech_facts.build — FACT; SECONDARY_NOTE marked; OWNER_REPORTS as "владельцы сообщают";
HIDDEN_CONFLICT never reaches the context), its recalls and known issues, and the owner's own log
and mileage. Every fact gets an id (F1, F2, ...); the model must cite the ids it uses.

The server checks what the model returns before anything is shown:
- a car-specific statement must cite known facts, and every number in it must be a number of the
  cited facts (or of the question): no invented capacity, approval or interval;
- general advice is kept apart and must contain no number at all;
- whatever fails the check is dropped and logged; nothing left -> an honest refusal ("в данных этой
  машины этого нет").

Model: Claude through the backend (the key from the environment, never in code). Without a key the
mechanic answers in DATA_ONLY mode: the car's facts found for the question, no generated text.
Per-user daily limit and a log of every request (ai_mechanic_requests).
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.english import pick
from app.models.ai_mechanic import AIMechanicRequest
from app.models.garage import GarageVehicle
from app.services import garage, us_tech_facts

API_URL = "https://api.anthropic.com/v1/messages"
NUMBER = re.compile(r"(?<![\w.])\d+(?:[   ,.]\d+)*")
CITATION = re.compile(r"\[(?:F\d+(?:\s*,\s*F\d+)*)\]")
T = {
    "refusal": ("В данных этой машины ответа на этот вопрос нет — в руководстве и в нашей базе это не указано.",
                "Bu avtomobilin məlumatlarında bu suala cavab yoxdur — təlimatda və bazamızda göstərilməyib.",
                "This car's data has no answer to that — the manual and our database don't state it."),
    "data_only": ("ИИ-механик не подключён (нет ключа API): показаны данные вашей машины, найденные по вопросу.",
                  "Sİ-mexanik qoşulmayıb (API açarı yoxdur): sualınıza görə tapılan avtomobil məlumatları göstərilir.",
                  "The AI mechanic is not connected (no API key): here is your car's data matching the question."),
    "disclaimer": ("Ответ основан только на данных вашей машины; числа — со ссылкой на источник. Общие советы помечены отдельно.",
                   "Cavab yalnız avtomobilinizin məlumatlarına əsaslanır; rəqəmlər mənbə ilə. Ümumi məsləhətlər ayrıca qeyd olunub.",
                   "Based only on your car's data; every number cites its source. General advice is marked separately."),
    "owner_log": ("журнал владельца", "sahibin jurnalı", "owner's log"),
    "app_calc": ("расчёт Auto Expert по журналу и регламенту", "jurnal və reqlament üzrə Auto Expert hesablaması",
                 "Auto Expert calculation from the log and schedule"),
    "limit": ("Лимит вопросов на сегодня исчерпан", "Bu gün üçün sual limiti bitib", "Today's question limit is reached"),
}
# topic words -> fact keys / jobs, for the DATA_ONLY search (three languages)
TOPICS = [
    (r"масл|oil|yağ", ("engine_oil", "oil")),
    (r"антифриз|охлажд|coolant|antifreeze|soyuducu|antifriz|зим|winter|qış|перегр|overheat", ("coolant", "engine_coolant", "cooling")),
    (r"короб|акпп|atf|transmission|gearbox|ötürmə|qutu|сцеплен|clutch", ("transmission", "dct", "dual_clutch", "clutch")),
    (r"тормоз|brake|əyləc", ("brake",)),
    (r"свеч|spark|şam", ("spark",)),
    (r"шин|колес|давлен|tire|tyre|wheel|pressure|təkər|şin", ("tire", "wheel")),
    (r"бензин|топлив|октан|fuel|gas|octane|yanacaq|benzin", ("fuel", "octane")),
    (r"ремень|грм|belt|kəmər|цеп|chain|zəncir", ("timing", "belt", "chain")),
    (r"фильтр|filter|filtr", ("filter",)),
    (r"аккумул|батар|battery|akkumul", ("battery",)),
    (r"отзыв|recall|кампан|campaign|kampaniya", ("@recalls",)),
    (r"пробл|слаб|ломает|issue|problem|weak|zəif|problem|лампа|light|lamp|lampa|горит|стук|noise|səs", ("@issues",)),
    (r"то\b|обслуж|регламент|maintenance|service|xidmət|reqlament|когда|when|nə vaxt", ("@maintenance",)),
]


def enabled(settings=None) -> bool:
    settings = settings or get_settings()
    if settings.ai_mechanic_v1 is not None:
        return bool(settings.ai_mechanic_v1)
    return settings.environment != "production"


def api_key(settings=None) -> str | None:
    settings = settings or get_settings()
    return settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY") or None


def tt(language: str, key: str) -> str:
    return pick(language, *T[key])


# --- the context -------------------------------------------------------------------------------
def _source_text(source: dict | None) -> str | None:
    if not source:
        return None
    return " · ".join(str(x) for x in (source.get("title"), source.get("publisher"), source.get("locator")) if x) or None


def context(db, vehicle: GarageVehicle, language: str) -> dict:
    """The facts of this car, each with an id, its text, kind, key and source."""
    data = us_tech_facts.build(db, vehicle.configuration_key, language) if vehicle.configuration_key else None
    view = garage.overview(db, vehicle, language)
    labels = (data or {}).get("labels") or {}
    facts: list[dict] = []

    def add(kind, key, text, source=None, note=None):
        facts.append({"id": f"F{len(facts) + 1}", "kind": kind, "key": key, "text": text,
                      "source": source, "note": note})

    for category in (data or {}).get("categories") or []:
        for row in category["rows"]:
            for v in row["values"]:
                text = f"{category['title']} — {row['label']}: {v['value']}" + (f" ({v['qualifier']})" if v.get("qualifier") else "")
                add("fact", row["key"], text, _source_text(v.get("source")), labels.get("secondary") if v.get("secondary") else None)
    for m in (data or {}).get("maintenance") or []:
        parts = [m["job"], m.get("action"), m.get("occurrence"), m.get("interval"), m.get("max_interval") and f"≤ {m['max_interval']}",
                 m.get("system"), m.get("service"), m.get("condition_detail")]
        severe = pick(language, "тяжёлые условия", "ağır şərait", "severe conditions") if m.get("severe") else None
        text = " · ".join(str(p) for p in [*parts, severe] if p)
        add("maintenance", m["job_key"], text, _source_text(m.get("source")), labels.get("secondary") if m.get("secondary") else None)
    for issue in view["weak_points"]:
        text = issue["title"] + (f"; {', '.join(issue['symptoms'][:4])}" if issue.get("symptoms") else "") + \
            (f"; {issue['how_to_check']}" if issue.get("how_to_check") else "") + (f"; {issue['typical']}" if issue.get("typical") else "")
        add("issue", issue.get("component_code") or "issue", text, None, issue.get("note"))
    for r in view["recalls"]:
        add("recall", "recall", f"Recall {r['number']}: {r.get('component') or ''} — {r.get('summary') or ''}".strip(" —"),
            "NHTSA", r.get("note"))
    owner = tt(language, "owner_log")
    if view["mileage"]["text"]:
        add("owner", "mileage", f"{pick(language, 'Пробег', 'Yürüş', 'Mileage')}: {view['mileage']['text']}"
            + (f" ({pick(language, 'оценка', 'təxmini', 'estimate')})" if view["mileage"]["estimated"] else ""), owner)
    add("owner", "conditions", f"{pick(language, 'Условия', 'Şərait', 'Conditions')}: {view['conditions']['label']}", owner)
    for r in view["log"][:12]:
        add("owner", "log", f"{r['label']} · {r['on'] or '—'} · {r['km_text'] or '—'} · {r['status']}", owner)
    for s in view["services"]:
        if s["status"] in ("OVERDUE", "SOON", "OK", "CHECK", "SET_INTERVAL"):
            add("app", "due", f"{s['label']}: {s['when']}" + (f" ({s['unconfirmed_note']})" if s.get("unconfirmed_note") else ""),
                tt(language, "app_calc"))
    return {"title": view["title"], "configuration": view["configuration"], "facts": facts}


# --- numbers -----------------------------------------------------------------------------------
def readings(token: str) -> set[str]:
    """The canonical readings of one number token: "87 000" / "87,000" -> 87000; "7,3" / "7.3" ->
    7.3; "15,000" can be 15000 or 15 (both readings kept)."""
    token = token.replace(" ", " ").replace(" ", " ")
    groups = re.split(r"[ ,.]", token)
    seps = re.findall(r"[ ,.]", token)
    if not seps:
        return {str(int(token))}
    out: set[str] = set()
    if all(len(g) == 3 for g in groups[1:]):
        out.add(str(int("".join(groups))))  # thousands separators
    if seps[-1] in ",." and seps.count(seps[-1]) == 1:
        out.add(_decimal("".join(groups[:-1]) + "." + groups[-1]))  # a decimal mark
    if not out:
        out.update(str(int(g)) for g in groups)  # neighbouring numbers ("2 5")
    return out


def tokens(text: str) -> list[set[str]]:
    return [readings(t) for t in NUMBER.findall(CITATION.sub(" ", str(text or "")))]


def numbers(text: str) -> set[str]:
    return set().union(*tokens(text)) if tokens(text) else set()


def unknown_numbers(text: str, allowed: set[str]) -> list[str]:
    """Number tokens of a text none of whose readings is allowed."""
    return [sorted(r)[0] for r in tokens(text) if not r & allowed]


def _decimal(text: str) -> str:
    value = float(text)
    return str(int(value)) if value == int(value) else f"{value:g}"


# --- the model ---------------------------------------------------------------------------------
SYSTEM = """You are the Auto Expert mechanic for ONE specific car. You answer the owner's question using ONLY the facts listed below (each has an id F1, F2, ...). Rules, strictly:
1. Every statement about this car must cite the fact ids it is based on. Every number you write about this car (capacity, approval, viscosity, interval, pressure, mileage, date) must be copied from the cited facts. Never invent or convert numbers.
2. If the facts do not contain what is asked, say so plainly in "not_in_data" (for example: "the manual does not state the coolant capacity for this car"). Do not guess.
3. General mechanic advice that is not from the facts goes ONLY to "general", must contain no numbers at all, and must not contradict the facts.
4. Facts marked as reference-book data or as owner reports keep that mark in your wording.
5. Answer in {language_name}. Be short and practical.
Return ONLY a JSON object: {{"answer": [{{"text": "...", "facts": ["F3"]}}], "general": [{{"text": "..."}}], "not_in_data": ["..."]}}"""
LANGUAGE_NAMES = {"ru": "Russian", "az": "Azerbaijani (Latin script)", "en": "English"}


def facts_block(ctx: dict) -> str:
    lines = [f"Car: {ctx['title']} — {ctx['configuration'] or ''}"]
    for f in ctx["facts"]:
        extra = " · ".join(x for x in (f.get("note"), f.get("source") and f"source: {f['source']}") if x)
        lines.append(f"{f['id']} [{f['kind']}] {f['text']}" + (f" ({extra})" if extra else ""))
    return "\n".join(lines)


def call_claude(ctx: dict, question: str, language: str, history: list[dict], *, transport=None) -> dict:
    settings = get_settings()
    messages = []
    for h in history[-3:]:
        messages += [{"role": "user", "content": h["question"]}, {"role": "assistant", "content": json.dumps(h["answer"], ensure_ascii=False)}]
    messages.append({"role": "user", "content": f"FACTS:\n{facts_block(ctx)}\n\nQUESTION: {question}"})
    body = {"model": settings.ai_mechanic_model, "max_tokens": settings.ai_mechanic_max_tokens,
            "system": SYSTEM.format(language_name=LANGUAGE_NAMES.get(language, "English")), "messages": messages}
    headers = {"x-api-key": api_key(settings) or "", "anthropic-version": "2023-06-01", "content-type": "application/json"}
    with httpx.Client(transport=transport, timeout=60) as client:
        response = client.post(API_URL, json=body, headers=headers)
    response.raise_for_status()
    payload = response.json()
    text = "".join(block.get("text", "") for block in payload.get("content") or [] if block.get("type") == "text")
    usage = payload.get("usage") or {}
    return {"draft": parse_draft(text), "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
            "model": payload.get("model") or settings.ai_mechanic_model}


def parse_draft(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return {"answer": [], "general": [], "not_in_data": []}
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return {"answer": [], "general": [], "not_in_data": []}
    return {"answer": [a for a in data.get("answer") or [] if isinstance(a, dict)],
            "general": [g if isinstance(g, dict) else {"text": str(g)} for g in data.get("general") or []],
            "not_in_data": [str(x) for x in data.get("not_in_data") or []]}


# --- the check ---------------------------------------------------------------------------------
def check(draft: dict, ctx: dict, question: str, language: str) -> tuple[dict, list[dict]]:
    """Keep only what the car's data supports. Returns (answer, rejected)."""
    by_id = {f["id"]: f for f in ctx["facts"]}
    asked = numbers(question)
    rejected = []
    answer = []
    for item in draft.get("answer") or []:
        text = str(item.get("text") or "").strip()
        ids = [str(i) for i in item.get("facts") or [] if str(i) in by_id]
        if not text:
            continue
        if not ids:
            rejected.append({"text": text, "reason": "NO_FACTS_CITED"})
            continue
        allowed = set().union(*(numbers(by_id[i]["text"]) for i in ids)) | asked
        unknown = unknown_numbers(text, allowed)
        if unknown:
            rejected.append({"text": text, "reason": "NUMBER_NOT_IN_CITED_FACTS", "numbers": unknown})
            continue
        answer.append({"text": CITATION.sub("", text).strip(), "facts": [
            {"id": i, "text": by_id[i]["text"], "source": by_id[i]["source"], "note": by_id[i].get("note")} for i in ids]})
    general = []
    for item in draft.get("general") or []:
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        if NUMBER.search(text):
            rejected.append({"text": text, "reason": "NUMBER_IN_GENERAL_ADVICE"})
            continue
        general.append({"text": text})
    missing = []
    for text in draft.get("not_in_data") or []:
        if unknown_numbers(text, asked):
            rejected.append({"text": text, "reason": "NUMBER_IN_NOT_IN_DATA"})
            continue
        missing.append(text)
    if not answer:
        missing = missing or [tt(language, "refusal")]
    return {"answer": answer, "general": general, "not_in_data": missing}, rejected


# --- data-only mode ----------------------------------------------------------------------------
def data_only(ctx: dict, question: str, limit: int = 6) -> dict:
    """No model: the car's facts that match the question's topic, verbatim."""
    q = question.lower()
    wanted: list[str] = []
    for pattern, keys in TOPICS:
        if re.search(pattern, q):
            wanted += keys
    chosen = []
    for f in ctx["facts"]:
        key = str(f["key"]).lower()
        hit = any((k == "@recalls" and f["kind"] == "recall") or (k == "@issues" and f["kind"] == "issue")
                  or (k == "@maintenance" and f["kind"] in ("maintenance", "app"))
                  or (not k.startswith("@") and k in key) for k in wanted)
        if hit:
            chosen.append(f)
    chosen.sort(key=lambda f: {"fact": 0, "app": 1, "maintenance": 2, "owner": 3, "recall": 4, "issue": 5}.get(f["kind"], 9))
    return {"answer": [{"text": f["text"], "facts": [f["id"]]} for f in chosen[:limit]], "general": [], "not_in_data": []}


# --- the request -------------------------------------------------------------------------------
def used_today(db, user_id: str) -> int:
    since = datetime.now(UTC) - timedelta(days=1)
    return db.scalar(select(func.count()).select_from(AIMechanicRequest).where(
        AIMechanicRequest.user_id == user_id, AIMechanicRequest.created_at >= since)) or 0


def history(db, vehicle: GarageVehicle, limit: int = 10) -> list[AIMechanicRequest]:
    rows = db.scalars(select(AIMechanicRequest).where(AIMechanicRequest.vehicle_id == vehicle.id)
                      .order_by(AIMechanicRequest.created_at.desc()).limit(limit))
    return list(rows)[::-1]


def ask(db, user, vehicle: GarageVehicle, question: str, language: str, *, transport=None) -> AIMechanicRequest:
    settings = get_settings()
    started = time.monotonic()
    ctx = context(db, vehicle, language)
    entry = AIMechanicRequest(user_id=user.id, vehicle_id=vehicle.id, configuration_key=vehicle.configuration_key,
                              language=language, question=question, mode="DATA_ONLY", status="OK", answer={}, rejected=[])
    draft, rejected = None, []
    if api_key(settings):
        entry.mode = "CLAUDE"
        past = [{"question": h.question, "answer": h.answer} for h in history(db, vehicle, 3) if h.mode == "CLAUDE"]
        try:
            result = call_claude(ctx, question, language, past, transport=transport)
            draft = result["draft"]
            entry.model, entry.input_tokens, entry.output_tokens = result["model"], result["input_tokens"], result["output_tokens"]
        except (httpx.HTTPError, ValueError) as exc:
            entry.status = "ERROR"
            rejected.append({"reason": "MODEL_ERROR", "text": type(exc).__name__})
            draft = data_only(ctx, question)  # the car's data is still shown
            entry.mode = "DATA_ONLY"
    else:
        draft = data_only(ctx, question)
    answer, dropped = check(draft, ctx, question, language)
    rejected += dropped
    if not answer["answer"] and entry.status == "OK":
        entry.status = "REFUSED"
    answer["mode_note"] = tt(language, "data_only") if entry.mode == "DATA_ONLY" else None
    answer["disclaimer"] = tt(language, "disclaimer")
    entry.answer, entry.rejected = answer, rejected
    entry.latency_ms = int((time.monotonic() - started) * 1000)
    db.add(entry)
    db.flush()
    return entry


def view(entry: AIMechanicRequest) -> dict:
    return {"id": entry.id, "question": entry.question, "mode": entry.mode, "status": entry.status,
            "created_at": entry.created_at.isoformat() if entry.created_at else None, **(entry.answer or {})}

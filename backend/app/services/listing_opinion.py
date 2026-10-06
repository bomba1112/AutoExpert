# ruff: noqa: E501
"""The Auto Expert opinion on one car: a Turbo.az listing link, a VIN or what the user knows
(UI-by-reference prompt, section 3), behind the expert_opinion_v1 flag.

- A link is fetched on the user's request: one page, once a day at most (provider cache), ordinary
  browser headers, a timeout, robots.txt respected. Unreachable / blocked -> the user is offered to
  paste the listing text instead. Never bulk collection.
- Make and model come from the listing AND must agree with the link (".../10556520-kia-stinger" ->
  Kia Stinger). A different model in the page than in the link is an error: no car is shown.
- The model is looked up in the US technical database by name only (known name forms such as
  "328i" -> "3 Series"), never by similarity: a model we do not have is said to be missing, never
  replaced by another one.
- The opinion: what the car is (confirmed / not), the seller's claims apart from checked data,
  discrepancies (an engine size that does not exist for that year...), known issues and what to check
  at the inspection, recalls, the next service by the listing's mileage, a short conclusion. Data
  rules are the card's (us_tech_facts.build): HIDDEN_CONFLICT never, secondary data marked.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlsplit

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.english import pick
from app.models.catalog import VehicleMake
from app.models.evidence import TechnicalEvidence
from app.models.research import ProviderCacheEntry
from app.services import garage, garage_schedule, us_tech_facts, vpic_local
from app.services.listing_intake import (
    ListingInputError,
    TurboAzUserProvidedContentAdapter,
    validate_turbo_url,
)

PROVIDER = "turbo.az.listing"
CAPABILITY = "LISTING_PAGE"
CACHE_TTL = timedelta(hours=24)
FETCH_TIMEOUT = 15
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "az,ru;q=0.9,en;q=0.8",
}
VIN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
PLATE = re.compile(r"^\d{2}\s?-?\s?[A-Z]{2}\s?-?\s?\d{3}$")
FUELS = [(r"plug|şarj", "PHEV"), (r"hibrid|гибрид|hybrid", "HEV"), (r"elektr|электр|electric", "BEV"),
         (r"dizel|дизел|diesel", "DIESEL"), (r"benzin|бензин|gasoline|petrol", "GASOLINE")]
TRANSMISSIONS = [(r"variator|вариатор|cvt", "CVT"), (r"robot|робот|dct|dsg", "DCT"), (r"mexaniki|механ|manual", "MANUAL"),
                 (r"avtomat|автомат|automatic|\bat\b", "AT")]
DRIVES = [(r"arxa|задн|rear|rwd", "RWD"), (r"\bön\b|^ön|перед|front|fwd", "FWD"), (r"tam|полн|all|awd|4wd|4x4", "AWD")]
MARKETS = [(r"amerika|америк|usa|abş", "US"), (r"avropa|европ|europe", "EU"), (r"koreya|корея|korea", "KR"),
           (r"yaponiya|япон|japan", "JP"), (r"çin|китай|china", "CN"), (r"dubay|дубай|gulf|ərəb", "GCC"),
           (r"rəsmi|официальн|official", "OFFICIAL_AZ"), (r"rusiya|росси|russia", "RU")]
T = {
    "model_mismatch": ("Модель в объявлении ({page}) не совпадает с моделью в ссылке ({url}). Мнение не показываем, чтобы не выдать чужую машину.",
                       "Elandakı model ({page}) keçiddəki modellə ({url}) üst-üstə düşmür. Başqa avtomobili göstərməmək üçün rəy verilmir.",
                       "The model in the listing ({page}) does not match the model in the link ({url}). No opinion is shown so as not to describe a different car."),
    "not_in_base": ("Модели {model} пока нет в нашей базе. Похожую модель мы не подставляем.",
                    "{model} modeli hələ bazamızda yoxdur. Oxşar modeli əvəz etmirik.",
                    "{model} is not in our database yet. We do not substitute a similar model."),
    "year_not_in_base": ("Для {model} {year} года в базе нет конфигураций. Есть годы: {years}.",
                         "{model} {year} üçün bazada konfiqurasiya yoxdur. Mövcud illər: {years}.",
                         "Our database has no {year} {model} configuration. Available years: {years}."),
    "unreadable": ("Не удалось прочитать объявление. Вставьте текст объявления — разберём его так же.",
                   "Elanı oxumaq mümkün olmadı. Elanın mətnini daxil edin — eyni qaydada təhlil edəcəyik.",
                   "The listing could not be read. Paste the listing text and we will analyse it the same way."),
    "unavailable": ("Сайт объявления сейчас не ответил или ограничил доступ. Вставьте текст объявления — разберём его.",
                    "Elan saytı hazırda cavab vermədi və ya girişi məhdudlaşdırdı. Elanın mətnini daxil edin.",
                    "The listing site did not answer or restricted access. Paste the listing text and we will analyse it."),
    "plate": ("Проверка по госномеру пока недоступна: нет подключённого источника. Используйте VIN или ссылку на объявление.",
              "Dövlət nömrəsi ilə yoxlama hələ mümkün deyil: qoşulmuş mənbə yoxdur. VIN və ya elan keçidindən istifadə edin.",
              "Checking by plate number is not available yet: no source is connected. Use the VIN or a listing link."),
    "unknown_input": ("Вставьте VIN (17 знаков), ссылку на объявление Turbo.az или марку, модель и год.",
                      "VIN (17 simvol), Turbo.az elanının keçidini və ya marka, model və ili daxil edin.",
                      "Paste a VIN (17 characters), a Turbo.az listing link, or the make, model and year."),
    "vin_unknown": ("VIN не удалось расшифровать по базе NHTSA vPIC.", "VIN NHTSA vPIC bazası ilə deşifrə edilmədi.",
                    "The VIN could not be decoded with the NHTSA vPIC database."),
    "confirmed": ("Конфигурация определена однозначно", "Konfiqurasiya birmənalı müəyyən edilib", "The configuration is determined"),
    "several": ("Подходит несколько версий — уточните по VIN или у продавца", "Bir neçə versiya uyğun gəlir — VIN və ya satıcı ilə dəqiqləşdirin",
                "Several versions fit — confirm by VIN or with the seller"),
    "us_market_note": ("В базе — американские версии. Рынок объявления: {market}; комплектация и оборудование могут отличаться.",
                       "Bazada Amerika versiyaları var. Elanın bazarı: {market}; komplektasiya fərqli ola bilər.",
                       "Our database holds US versions. The listing's market: {market}; equipment may differ."),
    "check_recall": ("Проверить по VIN, выполнена ли отзывная кампания {number}{component}", "VIN üzrə {number}{component} geri çağırma kampaniyasının icrasını yoxlayın",
                     "Check by VIN that recall {number}{component} was done"),
    "check_belt": ("Спросить документы о замене ремня ГРМ: по пробегу замена уже положена по регламенту",
                   "Qazpaylama kəmərinin dəyişmə sənədlərini soruşun: yürüşə görə reqlament artıq dəyişməni tələb edir",
                   "Ask for proof of the timing belt replacement: by the mileage the schedule already calls for it"),
    "summary_issues": ("Известных проблем у этой версии: {n}, из них серьёзных: {serious}", "Bu versiyanın məlum problemləri: {n}, ciddi olanlar: {serious}",
                       "Known issues of this version: {n}, serious: {serious}"),
    "summary_recalls": ("Отзывных кампаний: {n} — проверить выполнение по VIN у дилера", "Geri çağırma kampaniyaları: {n} — icrasını dilerdə VIN üzrə yoxlayın",
                        "Recalls: {n} — check at a dealer by VIN that they were done"),
    "summary_discrepancies": ("Расхождения объявления с базой: {n} — уточните у продавца", "Elanla baza arasında uyğunsuzluq: {n} — satıcı ilə dəqiqləşdirin",
                              "Listing vs database discrepancies: {n} — ask the seller"),
    "summary_service": ("По пробегу {km}: ближайшее ТО — {job}", "{km} yürüşə görə ən yaxın TXQ — {job}", "At {km}: next service — {job}"),
    "summary_vin": ("Попросите VIN: по нему проверяются история и отзывные кампании", "VIN-i istəyin: tarixçə və kampaniyalar onunla yoxlanılır",
                    "Ask for the VIN: history and recalls are checked by it"),
    "no_schedule": ("Регламента ТО для этой версии пока нет в базе — ближайшее ТО по пробегу не считаем",
                    "Bu versiya üçün TXQ reqlamenti hələ bazada yoxdur — yürüşə görə ən yaxın TXQ hesablanmır",
                    "The maintenance schedule of this version is not in our database yet — the next service is not calculated"),
    "seller_claim": ("указано в объявлении", "elanda göstərilib", "stated in the listing"),
    "discrepancy_engine": ("Объём {value} л для {model} {year} в базе не встречается (есть: {options})",
                           "{model} {year} üçün {value} l həcm bazada yoxdur (var: {options})",
                           "A {value} L engine is not listed for the {year} {model} (listed: {options})"),
    "discrepancy_drive": ("Привод «{value}» для {model} {year} в базе не встречается (есть: {options})",
                          "{model} {year} üçün «{value}» ötürücü bazada yoxdur (var: {options})",
                          "A {value} drive is not listed for the {year} {model} (listed: {options})"),
    "discrepancy_fuel": ("Тип двигателя «{value}» для {model} {year} в базе не встречается (есть: {options})",
                         "{model} {year} üçün «{value}» mühərrik növü bazada yoxdur (var: {options})",
                         "A {value} powertrain is not listed for the {year} {model} (listed: {options})"),
    "discrepancy_transmission": ("Коробка «{value}» для {model} {year} в базе не встречается (есть: {options})",
                                 "{model} {year} üçün «{value}» sürətlər qutusu bazada yoxdur (var: {options})",
                                 "A {value} transmission is not listed for the {year} {model} (listed: {options})"),
}
MARKET_NAMES = {"US": ("США", "ABŞ", "USA"), "EU": ("Европа", "Avropa", "Europe"), "KR": ("Корея", "Koreya", "Korea"),
                "JP": ("Япония", "Yaponiya", "Japan"), "CN": ("Китай", "Çin", "China"), "GCC": ("Персидский залив", "Fars körfəzi", "Gulf"),
                "OFFICIAL_AZ": ("официальный рынок Азербайджана", "Azərbaycanın rəsmi bazarı", "official Azerbaijan market"),
                "RU": ("Россия", "Rusiya", "Russia")}


def enabled(settings=None) -> bool:
    settings = settings or get_settings()
    if settings.expert_opinion_v1 is not None:
        return bool(settings.expert_opinion_v1)
    return settings.environment != "production"


def tt(language: str, key: str, **values) -> str:
    text = pick(language, *T[key])
    return text.format(**values) if values else text


def norm(text) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def classify(value: str) -> str:
    """What the user pasted: LINK, VIN, PLATE, TEXT (make / model / year), or UNKNOWN."""
    value = (value or "").strip()
    if value.lower().startswith(("http://", "https://", "turbo.az/", "www.turbo.az/")):
        return "LINK"
    compact = re.sub(r"[\s-]", "", value).upper()
    if VIN.match(compact):
        return "VIN"
    if PLATE.match(value.upper()):
        return "PLATE"
    if re.search(r"\b(19|20)\d{2}\b", value) and re.search(r"[A-Za-zА-Яа-я]{2,}", value):
        return "TEXT"
    return "UNKNOWN"


def url_slug(url: str) -> str | None:
    """The make-model part of a Turbo.az link: /autos/10556520-kia-stinger -> 'kia-stinger'."""
    m = re.match(r"^/autos/\d+-(?P<slug>[a-z0-9-]+?)/?$", urlsplit(url).path.lower())
    return m["slug"] if m else None


def slug_agrees(slug: str | None, make: str, model: str) -> bool:
    if not slug:
        return True  # a link without the name part: only the page says what the car is
    s, mk, md = norm(slug), norm(make), norm(model)
    if not s.startswith(mk):
        return False
    rest = s[len(mk):]
    return bool(rest) and (rest == md or md.startswith(rest) or rest.startswith(md))


def _first(patterns, text) -> str | None:
    t = str(text or "").lower()
    return next((code for pattern, code in patterns if re.search(pattern, t)), None)


def normalize_listing(data: dict) -> dict:
    """The seller's claims as codes we can compare with the database."""
    engine = str(data.get("engine") or "")
    power = re.search(r"(\d{2,4})\s*(?:a\.?g\.?|л\.?\s?с\.?|hp)", engine.lower())
    displacement = re.search(r"(?<![\d.,])(\d[.,]\d)(?![\d.,])", engine)
    cc = None if displacement else re.search(r"(?<![\d.,])(\d{3,4})\s*(?:cc|см3|sm3|см³|sm³)?(?![\d.,])", engine)
    if cc and (not 600 <= int(cc[1]) <= 8500 or (power and power[1] == cc[1])):
        cc = None
    litres = float(displacement[1].replace(",", ".")) if displacement else round(int(cc[1]) / 1000, 1) if cc else None
    return {
        "make": (data.get("make") or "").strip() or None,
        "model": (data.get("model") or "").strip() or None,
        "year": data.get("year"),
        "displacement_l": litres,
        "power_hp": int(power[1]) if power else None,
        "fuel": _first(FUELS, engine) or _first(FUELS, data.get("fuel")),
        "transmission": _first(TRANSMISSIONS, data.get("transmission")),
        "drivetrain": _first(DRIVES, data.get("drivetrain")),
        "market": _first(MARKETS, data.get("market_claim")),
        "mileage_km": data.get("mileage_km"),
        "price": data.get("price"), "currency": data.get("currency"),
        "city": data.get("city"), "vin": data.get("vin"),
        "body": data.get("body"), "color": data.get("color"),
        "description": (data.get("description") or "")[:2000] or None,
        "raw": {k: data.get(k) for k in ("title", "engine", "transmission", "drivetrain", "market_claim", "condition_claim", "body") if data.get(k)},
    }


# --- fetching ----------------------------------------------------------------------------------
def default_fetch(url: str) -> dict:
    """One page on the user's request (app.providers.listings: SSRF-safe, robots.txt, size limits)."""
    from app.providers import listings

    return listings.import_listing(url, headers=BROWSER_HEADERS, timeout=FETCH_TIMEOUT)


def fetch_listing(db, url: str, fetch: Callable[[str], dict] = default_fetch) -> dict:
    key = hashlib.sha256(url.encode()).hexdigest()
    cached = db.scalar(select(ProviderCacheEntry).where(ProviderCacheEntry.provider_id == PROVIDER,
                                                        ProviderCacheEntry.capability == CAPABILITY,
                                                        ProviderCacheEntry.cache_key == key))
    now = datetime.now(UTC)
    if cached is not None:
        expires = cached.expires_at if cached.expires_at.tzinfo else cached.expires_at.replace(tzinfo=UTC)
        if now < expires:
            return {**cached.raw_payload, "cached": True}
    result = fetch(url)
    payload = {"status": result.get("status"), "reason": result.get("reason"), "data": result.get("data") or {},
               "retrieved_at": result.get("retrieved_at")}
    if result.get("status") == "IMPORTED":  # only good pages are kept a day; failures are retried next time
        payload["data"] = {k: v for k, v in payload["data"].items() if k != "photos"} | {"photos": (payload["data"].get("photos") or [])[:6]}
        if cached is None:
            db.add(ProviderCacheEntry(provider_id=PROVIDER, capability=CAPABILITY, cache_key=key, status="CONFIRMED",
                                      source_url=url, normalized_payload=[], raw_payload=payload, retrieved_at=now,
                                      expires_at=now + CACHE_TTL))
        else:
            cached.raw_payload, cached.retrieved_at, cached.expires_at = payload, now, now + CACHE_TTL
        db.flush()
    return {**payload, "cached": False}


def text_listing(text: str) -> dict:
    """The listing text the user pasted, with the intake parser."""
    from app.schemas.listing_intake import ListingIntakeCreate

    claims, _ = TurboAzUserProvidedContentAdapter().parse(ListingIntakeCreate(input_type="TEXT", text=text[:59000], language="ru"))
    value = lambda k: claims[k].raw_value if k in claims else None  # noqa: E731
    mileage = claims.get("mileage")
    price = claims.get("price")
    return {"make": value("make"), "model": value("model"), "year": claims["year"].normalized_value if "year" in claims else None,
            "engine": " / ".join(x for x in (value("engine"), value("fuel")) if x), "transmission": value("transmission"),
            "drivetrain": value("drivetrain"), "market_claim": value("market"), "city": value("city"), "body": value("body"),
            "mileage_km": mileage.normalized_value if mileage and isinstance(mileage.normalized_value, (int, float)) else None,
            "price": price.normalized_value if price and isinstance(price.normalized_value, (int, float)) else None,
            "currency": claims["price"].unit if price else None, "vin": value("vin"), "description": value("description"),
            "title": text.strip().splitlines()[0][:160] if text.strip() else None}


# --- the database --------------------------------------------------------------------------------
def model_names(make: str, model: str) -> list[str]:
    """Our model names a listing's model may stand for (no similarity guessing)."""
    names = [model]
    m = norm(model)
    if norm(make) == "bmw":
        hit = re.match(r"^([1-8])\d{2}[a-z]*$", m) or re.match(r"^([1-8])series$", m)
        if hit:
            names.append(f"{hit[1]} Series")
        x = re.match(r"^(x[1-7]|z4|i[3-8x])", m)
        if x:
            names.append(x[1].upper())
    if norm(make) in ("mercedesbenz", "mercedes"):
        hit = re.match(r"^(cla|cls|glc|gle|gls|gla|glb|clk|slk|sl|gl|ml|[abcegs])[\s-]?(\d{2,3}|class)?", model.strip().lower())
        if hit:
            names.append(f"{hit[1].upper()}-Class")
    if norm(make) == "lexus":
        hit = re.match(r"^([a-z]{2})\s?\d", model.strip().lower())
        if hit:
            names.append(hit[1].upper())
    return names


def find_model(db, make: str, model: str) -> tuple[str | None, str | None]:
    """(our make name, our model name) by name only; (make, None) when the model is not in the base."""
    make_row = db.scalar(select(VehicleMake).where(func.lower(VehicleMake.name).in_({make.lower(), make.lower().replace("mercedes", "mercedes-benz")})))
    if make_row is None:
        return None, None
    ours = {norm(r[2]): r[2] for r in db.execute(us_tech_facts._catalog_query().where(TechnicalEvidence.make_id == make_row.id))}
    for name in model_names(make_row.name, model):
        if norm(name) in ours:
            return make_row.name, ours[norm(name)]
    return make_row.name, None


def model_years(db, make: str, model: str) -> list[int]:
    rows = db.execute(us_tech_facts._catalog_query().where(func.lower(VehicleMake.name) == make.lower())).all()
    years = set()
    for row, _mk, md in rows:
        if norm(md) == norm(model) and row.year_from:
            years.update(range(row.year_from, (row.year_to or row.year_from) + 1))
    return sorted(years)


def _identity_sets(db, make: str, model: str, year: int) -> dict:
    rows = db.execute(us_tech_facts._catalog_query().where(
        func.lower(VehicleMake.name) == make.lower(), TechnicalEvidence.year_from <= year, TechnicalEvidence.year_to >= year)).all()
    out = {"displacement_l": set(), "drivetrain": set(), "fuel": set(), "transmission": set()}
    for row, _mk, md in rows:
        if norm(md) != norm(model):
            continue
        ident = (row.conditions or {}).get("identity") or {}
        if ident.get("displacement_l"):
            out["displacement_l"].add(round(float(ident["displacement_l"]), 1))
        drive = garage._drive(ident.get("drivetrain"))
        if drive:
            out["drivetrain"].add(drive)
        power = "DIESEL" if "-diesel-" in (row.configuration_key or "") else str(ident.get("powertrain") or "").upper()
        if power:
            out["fuel"].add({"ICE": "GASOLINE"}.get(power, power))
        family = us_tech_facts._gearbox(ident.get("epa_transmission"))[0]
        if family:
            out["transmission"].add(family)
    return out


def discrepancies(db, claims: dict, make: str, model: str, year: int, language: str) -> list[dict]:
    sets = _identity_sets(db, make, model, year)
    out = []
    checks = (("displacement_l", "discrepancy_engine"), ("drivetrain", "discrepancy_drive"), ("fuel", "discrepancy_fuel"),
              ("transmission", "discrepancy_transmission"))
    for field, key in checks:
        value, options = claims.get(field), sets[field]
        if value is None or not options:
            continue
        if field == "displacement_l":
            fits = any(abs(value - o) <= 0.06 for o in options)
        elif field == "fuel":
            fits = value in options or (value == "GASOLINE" and "ICE" in options)
        else:
            fits = value in options
        if not fits:
            shown = ", ".join(sorted(f"{o:.1f}" if isinstance(o, float) else str(o) for o in options))
            out.append({"field": field, "claimed": value, "catalog": sorted(map(str, options)),
                        "text": tt(language, key, value=value, model=f"{make} {model}", year=year, options=shown)})
    return out


# --- the opinion ---------------------------------------------------------------------------------
def _next_service(card: dict, km: int | None, conditions: str, language: str) -> list[dict]:
    if not km or not card.get("maintenance"):
        return []
    schedule = [m for m in card["maintenance"] if m.get("job_key") not in garage_schedule.OIL_JOBS]
    plans = garage_schedule.plans(schedule, conditions)
    items = []
    for plan in plans.values():
        due = garage_schedule.due(plan, [], km, date.today())
        if due["status"] in ("ON_SIGNAL", "NO_INTERVAL", "DONE") or due.get("next_km") is None and due["status"] != "CHECK":
            continue
        entry = (plan.every or plan.subsequent or plan.first).item if (plan.every or plan.subsequent or plan.first) else {}
        fluid = garage._fluid(card.get("categories") or [], plan.job)
        items.append({"job": plan.job, "label": entry.get("job") or plan.job, "action": entry.get("action"),
                      "status": due["status"], "next_km": due.get("next_km"), "remaining_km": (due.get("next_km") or km) - km,
                      "interval": entry.get("interval"), "fluid": fluid, "note": pick(language, "по регламенту, история не подтверждена",
                                                                                     "reqlamentə görə, tarixçə təsdiqlənməyib", "per schedule, history not confirmed")})
    items.sort(key=lambda i: (i["status"] != "CHECK", i["remaining_km"]))
    return items[:5]


def opinion_for(db, *, make: str, model: str, year: int | None, claims: dict, language: str, source: dict) -> dict:
    """The opinion once make / model / year are known (from a listing, a VIN or the user)."""
    our_make, our_model = find_model(db, make, model)
    base = {"source": source, "claims": claims, "language": language}
    if our_model is None:
        return base | {"status": "MODEL_NOT_IN_BASE", "message": tt(language, "not_in_base", model=f"{make} {model}")}
    years = model_years(db, our_make, our_model)
    if not year or year not in years:
        return base | {"status": "YEAR_NOT_IN_BASE", "years": years,
                       "message": tt(language, "year_not_in_base", model=f"{our_make} {our_model}", year=year or "?",
                                     years=", ".join(map(str, years[-8:])))}
    decoded = {"displacement_l": claims.get("displacement_l"), "drive": claims.get("drivetrain"),
               "transmission": {"CVT": "continuously variable", "DCT": "dual-clutch", "MANUAL": "manual", "AT": "automatic"}.get(claims.get("transmission") or ""),
               "fuel": {"DIESEL": "diesel", "GASOLINE": "gasoline", "BEV": "electric"}.get(claims.get("fuel") or ""),
               "electrification": {"HEV": "HEV", "PHEV": "PHEV", "BEV": "BEV"}.get(claims.get("fuel") or ""),
               "model": our_model}
    candidates = garage.candidates(db, our_make, our_model, year, decoded, language)
    if not candidates:
        return base | {"status": "YEAR_NOT_IN_BASE", "years": years,
                       "message": tt(language, "year_not_in_base", model=f"{our_make} {our_model}", year=year, years=", ".join(map(str, years[-8:])))}
    primary = candidates[0]
    card = us_tech_facts.build(db, primary["configuration_key"], language) or {}
    found = discrepancies(db, claims, our_make, our_model, year, language)
    market = claims.get("market")
    conditions = "NORMAL" if market == "US" and source.get("kind") == "VIN" else "SEVERE"  # a car in AZ: severe by default
    service = _next_service(card, claims.get("mileage_km"), conditions, language)
    checklist = []
    for issue in card.get("weak_points") or []:
        checklist.append({"text": issue["title"] + (f": {issue['how_to_check']}" if issue.get("how_to_check") else ""),
                          "note": issue.get("note"), "kind": "issue"})
    for recall in card.get("campaigns") or []:
        if any(recall["number"] in c["text"] for c in checklist):
            continue  # already named by a known issue
        component = f" ({recall['component']})" if recall.get("component") else ""
        checklist.append({"text": tt(language, "check_recall", number=recall["number"], component=component), "kind": "recall"})
    if any(s["job"] == "timing_belt" and s["status"] in ("CHECK", "OVERDUE") for s in service):
        checklist.append({"text": tt(language, "check_belt"), "kind": "service"})
    serious = sum(1 for i in card.get("weak_points") or [] if i.get("severity_code") in ("HIGH", "CRITICAL"))
    summary = [tt(language, "confirmed") if len(candidates) == 1 else tt(language, "several")]
    if card.get("weak_points"):
        summary.append(tt(language, "summary_issues", n=len(card["weak_points"]), serious=serious))
    if card.get("campaigns"):
        summary.append(tt(language, "summary_recalls", n=len(card["campaigns"])))
    if found:
        summary.append(tt(language, "summary_discrepancies", n=len(found)))
    if service:
        summary.append(tt(language, "summary_service", km=garage.distance(claims.get("mileage_km"), language), job=service[0]["label"]))
    if not claims.get("vin") and source.get("kind") != "VIN":
        summary.append(tt(language, "summary_vin"))
    notes = []
    if claims.get("mileage_km") and not card.get("maintenance"):
        notes.append(tt(language, "no_schedule"))
    if market and market != "US":
        notes.append(tt(language, "us_market_note", market=pick(language, *MARKET_NAMES.get(market, (market,) * 3))))
    return base | {
        "status": "OK", "make": our_make, "model": our_model, "year": year,
        "confirmed": len(candidates) == 1,
        "configuration": {"key": primary["configuration_key"], "label": primary["label"], "generation": card.get("generation")},
        "alternatives": [c["label"] for c in candidates[1:6]],
        "discrepancies": found, "notes": notes,
        "weak_points": card.get("weak_points") or [], "campaigns": card.get("campaigns") or [],
        "checklist": checklist, "next_service": service, "summary": summary,
        "labels": card.get("labels") or {},
        "seller_label": tt(language, "seller_claim"),
        "vin_check": bool(claims.get("vin")),
    }


def opinion(db, *, query: str | None = None, text: str | None = None, manual: dict | None = None, language: str = "ru",
            fetch: Callable[[str], dict] = default_fetch) -> dict:
    if manual:
        claims = normalize_listing({**manual, "engine": " ".join(str(manual.get(k) or "") for k in ("engine", "fuel"))})
        if not claims["make"] or not claims["model"]:
            return {"status": "INPUT_UNKNOWN", "message": tt(language, "unknown_input")}
        return opinion_for(db, make=claims["make"], model=claims["model"], year=_int(manual.get("year")), claims=claims, language=language,
                           source={"kind": "MANUAL"})
    query = (query or "").strip()
    kind = classify(query) if query else ("PASTED_TEXT" if text else "UNKNOWN")
    if kind == "PLATE":
        return {"status": "PLATE_UNAVAILABLE", "message": tt(language, "plate")}
    if kind == "VIN":
        decoded = vpic_local.decode(query)
        if not decoded.get("make") or not decoded.get("model"):
            return {"status": "VIN_UNKNOWN", "message": tt(language, "vin_unknown"), "vin": decoded.get("vin")}
        claims = {"make": decoded["make"], "model": decoded.get("series") or decoded["model"], "year": decoded.get("model_year"),
                  "displacement_l": vpic_local._number(decoded.get("displacement_l")), "drivetrain": garage._drive(decoded.get("drive")),
                  "transmission": None, "fuel": None, "market": "US", "vin": decoded["vin"], "mileage_km": None}
        out = opinion_for(db, make=decoded["make"], model=decoded["model"], year=decoded.get("model_year"), claims=claims, language=language,
                          source={"kind": "VIN", "vin": decoded["vin"], "database": decoded.get("database")})
        if out["status"] == "MODEL_NOT_IN_BASE" and decoded.get("series"):
            out = opinion_for(db, make=decoded["make"], model=decoded["series"], year=decoded.get("model_year"), claims=claims, language=language,
                              source={"kind": "VIN", "vin": decoded["vin"], "database": decoded.get("database")})
        return out
    if kind == "TEXT":
        hit = re.match(r"^\s*(.+?)\s+((?:19|20)\d{2})\b(.*)$", query)
        words = hit[1].split() if hit else []
        if len(words) < 2:
            return {"status": "INPUT_UNKNOWN", "message": tt(language, "unknown_input")}
        multi = next((m for m in ("Land Rover", "Alfa Romeo", "Mercedes-Benz", "Mercedes Benz") if hit[1].lower().startswith(m.lower() + " ")), None)
        make = multi or words[0]
        model = hit[1][len(multi):].strip() if multi else " ".join(words[1:])
        claims = normalize_listing({"make": make, "model": model, "year": int(hit[2]), "engine": hit[3]})
        return opinion_for(db, make=make, model=model, year=int(hit[2]), claims=claims, language=language, source={"kind": "TEXT"})
    if kind == "LINK" or text:
        url = None
        if kind == "LINK":
            raw = query if query.startswith("http") else "https://" + query
            try:
                url, _ = validate_turbo_url(raw)
            except ListingInputError:
                return {"status": "INPUT_UNKNOWN", "message": tt(language, "unknown_input")}
        if text:
            result = {"status": "IMPORTED", "data": text_listing(text), "cached": False}
        else:
            result = fetch_listing(db, url, fetch)
        source = {"kind": "LINK" if url else "PASTED_TEXT", "url": url, "cached": result.get("cached", False)}
        if result.get("status") != "IMPORTED":
            unreadable = result.get("reason") == "VEHICLE_METADATA_NOT_FOUND"
            return {"status": "LISTING_UNREADABLE" if unreadable else "LISTING_UNAVAILABLE", "source": source,
                    "message": tt(language, "unreadable" if unreadable else "unavailable"), "paste_text": True}
        claims = normalize_listing(result["data"])
        if not claims["make"] or not claims["model"]:
            return {"status": "LISTING_UNREADABLE", "source": source, "message": tt(language, "unreadable"), "paste_text": True}
        slug = url_slug(url) if url else None
        if not slug_agrees(slug, claims["make"], claims["model"]):
            return {"status": "MODEL_MISMATCH", "source": source, "claims": claims,
                    "message": tt(language, "model_mismatch", page=f"{claims['make']} {claims['model']}", url=slug)}
        return opinion_for(db, make=claims["make"], model=claims["model"], year=_int(claims.get("year")), claims=claims,
                           language=language, source=source | {"photos": (result["data"].get("photos") or [])[:3]})
    return {"status": "INPUT_UNKNOWN", "message": tt(language, "unknown_input")}


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

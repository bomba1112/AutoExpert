"""User-assisted Turbo.az intake. A URL is a reference and is never fetched here."""

from __future__ import annotations

from app.core.english import pick

import hashlib
import json
import re
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from threading import RLock
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.vin import VINValidationError, validate_vin
from app.models.catalog import VehicleVariant
from app.models.knowledge_ops import CommercialFactClaim, SourceRegistry
from app.models.listing_intake import (
    ListingFieldClaim,
    ListingIntakeRequest,
    ListingMatchResult,
    ListingSnapshot,
)
from app.schemas.listing_intake import ListingIntakeCreate
from app.services import catalog_buyer as buyer
from app.services.catalog_scope import POLICY_PATH

PARSER_VERSION = "turbo-user-content-1.0"
_CATALOG_CACHE: dict[object, tuple[tuple, list]] = {}
_CATALOG_CACHE_LOCK = RLock()
ALLOWED_HOSTS = frozenset({"turbo.az", "www.turbo.az", "ru.turbo.az", "en.turbo.az"})
LISTING_PATH = re.compile(r"^/autos/(?P<id>[0-9]{4,12})(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?/?$")
VIN_IN_TEXT = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.IGNORECASE)
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
PRICE = re.compile(
    r"(?P<n>\d{1,3}(?:[\s\u00a0]\d{3})+|\d{4,8})(?:[.,]00)?\s*(?P<u>AZN|USD|EUR|₼|\$|€)(?=$|[\s.,;])",
    re.IGNORECASE,
)
MILEAGE = re.compile(
    r"(?P<n>\d{1,3}(?:[\s\u00a0]\d{3})+|\d{3,7})\s*(?P<u>km|км|kilometr|mile|mi|миль)\b",
    re.IGNORECASE,
)
YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")

LABELS = {
    "make": ("Marka", "Марка", "Make", "Brand"),
    "model": ("Model", "Модель"),
    "year": ("Buraxılış ili", "Год выпуска", "Год", "İl", "Year"),
    "engine": ("Mühərrik", "Двигатель", "Объем двигателя", "Объём двигателя", "Engine"),
    "fuel": ("Yanacaq növü", "Yanacaq", "Тип топлива", "Топливо", "Fuel"),
    "transmission": ("Sürətlər qutusu", "Коробка передач", "Коробка", "Transmission"),
    "drivetrain": ("Ötürücü", "Привод", "Drive"),
    "body": ("Ban növü", "Тип кузова", "Кузов", "Body"),
    "market": ("Hansı bazar üçün yığılıb", "Рынок сборки", "Рынок", "Market"),
    "price": ("Qiymət", "Цена", "Price"),
    "mileage": ("Yürüş", "Пробег", "Mileage"),
    "vin": ("VIN", "VIN код", "VIN-код"),
    "city": ("Şəhər", "Город", "City"),
    "color": ("Rəng", "Цвет", "Color"),
    "owners": ("Sahiblərinin sayı", "Количество владельцев", "Владельцев", "Owners"),
    "condition": ("Vəziyyəti", "Состояние", "Condition"),
    "description": ("Əlavə məlumat", "Описание", "Description"),
    "seller_type": ("Satıcı", "Тип продавца", "Продавец", "Seller"),
    "listing_id": ("Elan nömrəsi", "Номер объявления", "Listing ID"),
}
FIELD_ORDER = tuple(LABELS) + ("currency", "mileage_unit")
TITLE_MAKES = (
    "Mercedes-Benz",
    "Volkswagen",
    "Land Rover",
    "Range Rover",
    "Mitsubishi",
    "Chevrolet",
    "Cadillac",
    "Infiniti",
    "Hyundai",
    "Toyota",
    "Honda",
    "Nissan",
    "Lexus",
    "Tesla",
    "Audi",
    "BMW",
    "Kia",
    "Jeep",
    "Ferrari",
    "Porsche",
    "Renault",
    "Opel",
    "Ford",
    "Тойота",
    "Хендай",
    "Хундай",
    "Шевроле",
    "Мерседес",
    "Фольксваген",
    "Киа",
    "Ауди",
    "БМВ",
)
MAKE_ALIASES = {
    "тойота": "Toyota",
    "хендай": "Hyundai",
    "хундай": "Hyundai",
    "шевроле": "Chevrolet",
    "мерседес": "Mercedes-Benz",
    "фольксваген": "Volkswagen",
    "киа": "Kia",
    "ауди": "Audi",
    "бмв": "BMW",
    "mercedes": "Mercedes-Benz",
    "vw": "Volkswagen",
}
MODEL_ALIASES = {
    "камри": "Camry",
    "королла": "Corolla",
    "элантра": "Elantra",
    "соната": "Sonata",
    "спортейдж": "Sportage",
    "круз": "Cruze",
}
TRANSLITERATION = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "i",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ы": "y",
        "э": "e",
        "ю": "yu",
        "я": "ya",
        "ə": "e",
        "ı": "i",
        "ğ": "g",
        "ş": "sh",
        "ç": "ch",
        "ö": "o",
        "ü": "u",
    }
)


class ListingInputError(ValueError):
    """A user-controlled input cannot be accepted as a Turbo.az snapshot."""


def validate_turbo_url(url: str) -> tuple[str, str]:
    """Normalize only an individual Turbo.az listing URL; never resolve or fetch it."""
    if (
        not isinstance(url, str)
        or len(url) > 2000
        or CONTROL.search(url)
        or any(c.isspace() for c in url)
    ):
        raise ListingInputError("Invalid Turbo.az listing URL")
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme.casefold() != "https"
            or parsed.hostname not in ALLOWED_HOSTS
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
            or not parsed.netloc
        ):
            raise ListingInputError("Only HTTPS Turbo.az listing URLs are supported")
    except ValueError as exc:
        raise ListingInputError("Invalid Turbo.az listing URL") from exc
    path = parsed.path.casefold()
    match = LISTING_PATH.fullmatch(path)
    if not match or "%" in path or "\\" in path:
        raise ListingInputError("URL must identify one Turbo.az advertisement")
    normalized_path = path.rstrip("/")
    return urlunsplit(("https", parsed.hostname, normalized_path, "", "")), match["id"]


def _key(value: object) -> str:
    raw = unicodedata.normalize("NFKD", str(value or "").casefold()).translate(TRANSLITERATION)
    raw = "".join(c for c in raw if not unicodedata.combining(c))
    return "".join(c for c in raw if c.isalnum())


LABEL_LOOKUP = {_key(alias): field for field, aliases in LABELS.items() for alias in aliases}


def _plain(value: object, *, limit: int = 4000) -> str:
    """No HTML is returned or stored as a field value, including embedded scripts."""
    text = CONTROL.sub("", str(value or ""))
    if "<" in text:
        soup = BeautifulSoup(text, "html.parser")
        for tag in soup(["script", "style", "iframe", "object", "svg", "template", "form"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
    return " ".join(text.split())[:limit]


def _number(value: str) -> int | float | None:
    match = re.search(r"\d[\d\s\u00a0]*(?:[.,]\d+)?", value)
    if not match:
        return None
    raw = re.sub(r"[\s\u00a0]", "", match[0]).replace(",", ".")
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return None
    if not number.is_finite() or number < 0:
        return None
    return int(number) if number == int(number) else float(number)


def _currency(value: str) -> str | None:
    value = value.upper()
    return next(
        (
            code
            for token, code in (
                ("AZN", "AZN"),
                ("₼", "AZN"),
                ("USD", "USD"),
                ("$", "USD"),
                ("EUR", "EUR"),
                ("€", "EUR"),
            )
            if token in value
        ),
        None,
    )


def _unit_mileage(value: str) -> str | None:
    lowered = value.casefold()
    if re.search(r"\b(?:km|км|kilometr)\b", lowered):
        return "km"
    if re.search(r"\b(?:mi|mile|миль)\b", lowered):
        return "mi"
    return None


def _normalize(field: str, raw: str) -> tuple[object, str | None]:
    lower = _key(raw)
    if field == "year":
        year = YEAR.search(raw)
        return (int(year[1]) if year else None), None
    if field == "price":
        return _number(raw), _currency(raw)
    if field == "currency":
        return _currency(raw), None
    if field == "mileage":
        return _number(raw), _unit_mileage(raw)
    if field == "mileage_unit":
        return _unit_mileage(raw), None
    if field == "engine":
        displacement = re.search(
            r"\b(\d{1,2}[.,]\d{1,2})\s*(?:l|л|litr|литр)?\b", raw, re.IGNORECASE
        )
        return (displacement[1].replace(",", ".") if displacement else raw), (
            "L" if displacement else None
        )
    if field == "fuel":
        for tokens, value in (
            ("бенз", "GASOLINE"),
            ("benzin", "GASOLINE"),
            ("gasoline", "GASOLINE"),
            ("дизел", "DIESEL"),
            ("dizel", "DIESEL"),
            ("diesel", "DIESEL"),
            ("электр", "ELECTRICITY"),
            ("elektr", "ELECTRICITY"),
        ):
            if tokens in raw.casefold():
                return value, None
    if field == "transmission":
        if any(token in lower for token in ("avtomat", "автомат", "automatic")):
            return "AUTOMATIC_UNSPECIFIED", None
        if any(token in lower for token in ("mexanika", "механ", "manual")):
            return "MANUAL", None
        if any(token in lower for token in ("вариатор", "variator", "cvt", "ivt")):
            return "CVT", None
        if any(token in lower for token in ("dct", "dsg", "dualclutch")):
            return "DCT", None
        if "робот" in raw.casefold() or "robot" in lower:
            return "AMT_UNSPECIFIED", None
    if field == "drivetrain":
        if (
            any(token in lower for token in ("frontwheel", "peredni", "on", "fwd"))
            or "передн" in raw.casefold()
        ):
            return "FWD", None
        if (
            any(token in lower for token in ("rearwheel", "arxa", "rwd"))
            or "задн" in raw.casefold()
        ):
            return "RWD", None
        if (
            any(token in lower for token in ("awd", "4wd", "4x4", "full", "tam"))
            or "полн" in raw.casefold()
        ):
            return "AWD_OR_4WD", None
    if field == "body":
        for token, value in (
            ("sedan", "SEDAN"),
            ("седан", "SEDAN"),
            ("suv", "SUV"),
            ("crossover", "CROSSOVER"),
            ("кроссов", "CROSSOVER"),
            ("hatchback", "HATCHBACK"),
            ("хетч", "HATCHBACK"),
            ("coupe", "COUPE"),
            ("купе", "COUPE"),
            ("wagon", "WAGON"),
            ("универсал", "WAGON"),
        ):
            if token in raw.casefold():
                return value, None
    if field == "market":
        if lower in {_key(x) for x in ("Amerika", "America", "USA", "US", "США", "Америка", "ABŞ")}:
            return "US", None
        if lower in {_key(x) for x in ("Rəsmi diler", "Официальный дилер", "Official dealer")}:
            return "OFFICIAL_DEALER_CHANNEL", None
    if field == "vin":
        try:
            return validate_vin(raw), None
        except VINValidationError:
            return None, None
    if field == "owners":
        return _number(raw), None
    return raw, None


@dataclass(frozen=True)
class ClaimDraft:
    field_name: str
    raw_value: str
    normalized_value: object
    unit: str | None
    source_locator: str
    confidence: float


def _claim(field: str, value: object, locator: str, confidence: float) -> ClaimDraft | None:
    raw = _plain(value, limit=4000 if field == "description" else 200)
    if not raw:
        return None
    # An official-dealer label is a sales-channel claim, never a market identity.
    if field == "market" and _normalize(field, raw)[0] == "OFFICIAL_DEALER_CHANNEL":
        field = "seller_type"
    normalized, unit = _normalize(field, raw)
    return ClaimDraft(field, raw, normalized, unit, locator, confidence)


def _put(
    out: dict[str, ClaimDraft], field: str, value: object, locator: str, confidence: float
) -> None:
    if field in out:
        return
    claim = _claim(field, value, locator, confidence)
    if claim:
        out[claim.field_name] = claim
        if field == "price" and claim.unit and "currency" not in out:
            out["currency"] = ClaimDraft(
                "currency", claim.unit, claim.unit, None, locator, confidence
            )
        if field == "mileage" and claim.unit and "mileage_unit" not in out:
            out["mileage_unit"] = ClaimDraft(
                "mileage_unit", claim.unit, claim.unit, None, locator, confidence
            )


def _title_claims(out: dict[str, ClaimDraft], line: str, locator: str) -> None:
    title = _plain(line, limit=160)
    for make in sorted(TITLE_MAKES, key=len, reverse=True):
        if not title.casefold().startswith(make.casefold() + " "):
            continue
        rest = title[len(make) :].strip()
        model = rest.split(",", 1)[0].strip()
        model = YEAR.sub("", model).strip(" ,-·")
        if not model or len(model) > 45:
            break
        _put(out, "make", "Land Rover" if make == "Range Rover" else make, locator, 0.8)
        _put(
            out, "model", ("Range Rover " + model) if make == "Range Rover" else model, locator, 0.8
        )
        year = YEAR.search(title)
        if year:
            _put(out, "year", year[1], locator, 0.8)
        engine = re.search(r"(?:,|\s)(\d[.,]\d)\s*(?:L|л)\b", title, re.IGNORECASE)
        if engine:
            _put(out, "engine", engine[0].strip(" ,"), locator, 0.7)
        break


def _text_claims(
    text: str, *, initial: dict[str, ClaimDraft] | None = None
) -> dict[str, ClaimDraft]:
    out = dict(initial or {})
    lines = [_plain(line, limit=4000) for line in CONTROL.sub("", text).splitlines()]
    lines = [line for line in lines if line]
    if lines:
        _title_claims(out, lines[0], "text:line:1")
    for index, line in enumerate(lines):
        locator = f"text:line:{index + 1}"
        if ":" in line:
            label, value = line.split(":", 1)
            field = LABEL_LOOKUP.get(_key(label))
            if field and value.strip():
                _put(out, field, value, locator, 0.92)
                continue
        field = LABEL_LOOKUP.get(_key(line))
        if field and index + 1 < len(lines):
            _put(out, field, lines[index + 1], locator, 0.86)
    joined = "\n".join(lines)
    price = PRICE.search(joined)
    if price:
        _put(out, "price", price[0], "text:price", 0.76)
    mileage = MILEAGE.search(joined)
    if mileage:
        _put(out, "mileage", mileage[0], "text:mileage", 0.76)
    vin = VIN_IN_TEXT.search(joined)
    if vin:
        _put(out, "vin", vin[0], "text:vin", 0.8)
    if "rəsmi diler" in joined.casefold() or "официальный дилер" in joined.casefold():
        _put(
            out,
            "seller_type",
            "Rəsmi diler" if "rəsmi diler" in joined.casefold() else "Официальный дилер",
            "text:seller",
            0.75,
        )
    return out


class ListingSourceAdapter(ABC):
    @abstractmethod
    def parse(self, value: ListingIntakeCreate) -> tuple[dict[str, ClaimDraft], str | None]:
        """Return seller claims and sanitized visible text, without network access."""


class TurboAzUserProvidedContentAdapter(ListingSourceAdapter):
    def parse(self, value: ListingIntakeCreate) -> tuple[dict[str, ClaimDraft], str]:
        if value.input_type == "TEXT":
            raw = value.text or ""
            soup = BeautifulSoup(raw, "html.parser")
            for tag in soup(["script", "style", "iframe", "object", "svg", "template", "form"]):
                tag.decompose()
            visible = soup.get_text("\n") if "<" in raw else raw
            visible = CONTROL.sub("", visible)[:60_000]
            return _text_claims(visible), visible
        if value.input_type != "HTML_SNAPSHOT":
            raise ListingInputError("Unsupported supplied content type")
        soup = BeautifulSoup(value.html or "", "html.parser")
        for tag in soup(["script", "style", "iframe", "object", "svg", "template", "form"]):
            tag.decompose()
        out: dict[str, ClaimDraft] = {}
        title_meta = soup.select_one('meta[property="og:title"]')
        if title_meta and title_meta.get("content"):
            _title_claims(out, str(title_meta["content"]), "html:meta:og:title")
        description_meta = soup.select_one('meta[property="og:description"]')
        if description_meta and description_meta.get("content"):
            _put(
                out,
                "description",
                description_meta["content"],
                "html:meta:og:description",
                0.72,
            )
        for index, item in enumerate(soup.select(".product-properties__i")[:80]):
            label = item.select_one(".product-properties__i-name")
            actual = item.select_one(".product-properties__i-value")
            if (
                label
                and actual
                and (field := LABEL_LOOKUP.get(_key(label.get_text(" ", strip=True))))
            ):
                _put(out, field, actual.get_text(" ", strip=True), f"html:property:{index}", 0.94)
        for index, label in enumerate(soup.select("dt")[:80]):
            actual = label.find_next_sibling("dd")
            if actual and (field := LABEL_LOOKUP.get(_key(label.get_text(" ", strip=True)))):
                _put(out, field, actual.get_text(" ", strip=True), f"html:dt:{index}", 0.9)
        price = soup.select_one(".product-price__i, .product-price")
        if price:
            _put(out, "price", price.get_text(" ", strip=True), "html:price", 0.9)
        description = soup.select_one(".product-description__content, .product-description")
        if description:
            _put(
                out, "description", description.get_text(" ", strip=True), "html:description", 0.86
            )
        title = soup.select_one("h1")
        if title:
            _title_claims(out, title.get_text(" ", strip=True), "html:h1")
        visible = CONTROL.sub("", soup.get_text("\n", strip=True))[:60_000]
        return _text_claims(visible, initial=out), visible


class TurboAzManualInputAdapter(ListingSourceAdapter):
    def parse(self, value: ListingIntakeCreate) -> tuple[dict[str, ClaimDraft], None]:
        out: dict[str, ClaimDraft] = {}
        fields = value.fields or {}
        for field in FIELD_ORDER:
            if field in fields:
                _put(out, field, fields[field], f"manual:{field}", 1.0)
        if "currency" in fields and "price" in out:
            price = out["price"]
            out["price"] = ClaimDraft(
                price.field_name,
                price.raw_value,
                price.normalized_value,
                out["currency"].normalized_value,
                price.source_locator,
                price.confidence,
            )
        if "mileage_unit" in fields and "mileage" in out:
            mileage = out["mileage"]
            out["mileage"] = ClaimDraft(
                mileage.field_name,
                mileage.raw_value,
                mileage.normalized_value,
                out["mileage_unit"].normalized_value,
                mileage.source_locator,
                mileage.confidence,
            )
        return out, None


class TurboAzAuthorizedConnector(ListingSourceAdapter):
    """Permission-gated extension point; no live implementation is activated."""

    def parse(self, value: ListingIntakeCreate) -> tuple[dict[str, ClaimDraft], None]:
        if not value.source_url:
            raise ListingInputError("Authorized Turbo.az connector requires a listing URL")
        self.import_url(value.source_url)
        raise AssertionError("Unreachable while connector has no authorized implementation")

    def import_url(self, url: str) -> None:
        settings = get_settings()
        if not (
            settings.turbo_az_authorized_connector_enabled
            and settings.turbo_az_authorized_connector_credentials
            and settings.turbo_az_authorized_connector_permission_reference
        ):
            raise ListingInputError("Authorized Turbo.az connector is disabled")
        validate_turbo_url(url)
        raise ListingInputError("Authorized Turbo.az connector is not configured")


def _canonical(value: str, options: set[str], aliases: dict[str, str]) -> str:
    key = _key(value)
    alias = aliases.get(value.casefold())
    if alias and alias in options:
        return alias
    exact = sorted(option for option in options if _key(option) == key)
    if len(exact) == 1:
        return exact[0]
    ratios = sorted(
        ((SequenceMatcher(None, key, _key(option)).ratio(), option) for option in options),
        reverse=True,
    )
    if (
        ratios
        and ratios[0][0] >= 0.80
        and (len(ratios) == 1 or ratios[0][0] - ratios[1][0] >= 0.08)
    ):
        return ratios[0][1]
    return value


def _canonical_claims(claims: dict[str, ClaimDraft], rows: list) -> dict[str, ClaimDraft]:
    result = dict(claims)
    make = result.get("make")
    if make:
        canonical_make = _canonical(make.raw_value, {c["make"] for _, c in rows}, MAKE_ALIASES)
        result["make"] = ClaimDraft(
            "make", make.raw_value, canonical_make, None, make.source_locator, make.confidence
        )
    model = result.get("model")
    if model:
        selected_make = result.get("make")
        models = {
            c["model"]
            for _, c in rows
            if not selected_make or _key(c["make"]) == _key(selected_make.normalized_value)
        }
        canonical_model = _canonical(model.raw_value, models, MODEL_ALIASES)
        result["model"] = ClaimDraft(
            "model",
            model.raw_value,
            canonical_model,
            None,
            model.source_locator,
            model.confidence,
        )
    return result


def _confirmed(catalog: dict, fact_name: str) -> object | None:
    value = buyer.fact_value(catalog, fact_name)
    if value is None or str(value).strip().upper() in {"", "UNKNOWN", "UNRESOLVED", "UNVERIFIED"}:
        return None
    return value


def _candidate(variant, catalog: dict) -> dict:
    """A small rights-cleared display projection, with no EPA research fields."""
    engine = _confirmed(catalog, "engine_description") or _confirmed(catalog, "motor_description")
    transmission = _confirmed(catalog, "transmission_description")
    drive = _confirmed(catalog, "drivetrain")
    body = _confirmed(catalog, "body")
    fuel = _confirmed(catalog, "fuel")
    return {
        "variant_id": variant.id,
        "make": catalog["make"],
        "model": catalog["model"],
        "year": catalog["model_year"],
        "configuration": " · ".join(str(v) for v in (engine, transmission, drive) if v),
        "engine": str(engine) if engine else None,
        "transmission": str(transmission) if transmission else None,
        "drivetrain": str(drive) if drive else None,
        "body": str(body) if body else None,
        "fuel": str(fuel) if fuel else None,
        # Values come from the same rights-cleared projection used for the
        # match. Clients can localize these facts without parsing English prose.
        "engine_displacement": str(value)
        if (value := _confirmed(catalog, "engine_displacement")) is not None
        else None,
        "cylinders": str(value)
        if (value := _confirmed(catalog, "cylinders")) is not None
        else None,
        "powertrain": str(value)
        if (value := _confirmed(catalog, "powertrain")) is not None
        else None,
        "transmission_family": str(value)
        if (value := _confirmed(catalog, "transmission_family")) is not None
        else None,
        "gears": str(value)
        if (value := _confirmed(catalog, "gears")) is not None
        else None,
    }


def _claim_fit(field: str, expected: object, actual: object) -> bool | None:
    """None means the catalogue cannot resolve this seller assertion."""
    if actual is None or expected is None:
        return None
    if field == "engine":
        try:
            return Decimal(str(expected)) == Decimal(str(actual))
        except (InvalidOperation, ValueError):
            return _key(expected) == _key(actual)
    if field == "transmission":
        fit = buyer._transmission_fit(str(actual), str(expected))
        return None if fit == "UNKNOWN" else fit == "MATCH"
    if field == "drivetrain" and expected == "AWD_OR_4WD":
        return actual in {"AWD", "4WD", "PART_TIME_4WD"}
    if field == "body" and expected == "CROSSOVER":
        return actual in {"CROSSOVER", "SUV"}
    return _key(actual) == _key(expected)


def _transmission_claim_fit(expected: object, catalog: dict) -> bool | None:
    family = _confirmed(catalog, "transmission_family")
    if family is not None:
        return _claim_fit("transmission", expected, family)
    # A confirmed description can support a broad seller label. This never
    # turns "automatic" into AT/CVT/DCT or writes a family to the catalogue.
    description = _confirmed(catalog, "transmission_description")
    if description is None:
        return None
    key = _key(description)
    manual = "manual" in key or "mexan" in key
    automatic = any(
        token in key
        for token in ("automatic", "dualclutch", "dct", "dsg", "cvt", "ecvt", "variator")
    )
    if expected == "AUTOMATIC_UNSPECIFIED":
        return False if manual else True if automatic else None
    if expected == "MANUAL":
        return True if manual else False if automatic else None
    if expected == "DCT" and any(token in key for token in ("dualclutch", "dct", "dsg")):
        return True
    if expected == "CVT" and any(token in key for token in ("cvt", "variator")):
        return True
    return None


def _question(rows: list, claims: dict[str, ClaimDraft], language: str) -> str:
    def display(field: str, value: str) -> str:
        if field == "engine":
            return f"{Decimal(value):.1f}"
        labels = buyer.VALUE_LABELS.get(value)
        return pick(language, labels[0], labels[1]) if labels else value

    for field, fact_name, ru, az in (
        (
            "engine",
            "engine_displacement",
            "Какой объём двигателя указан",
            "Mühərrikin həcmi necə göstərilib",
        ),
        ("drivetrain", "drivetrain", "Какой привод указан", "Hansı ötürücü göstərilib"),
        (
            "transmission",
            "transmission_description",
            "Какая коробка указана",
            "Hansı sürətlər qutusu göstərilib",
        ),
        ("body", "body", "Какой кузов указан", "Hansı ban növü göstərilib"),
        ("fuel", "fuel", "Какое топливо указано", "Hansı yanacaq göstərilib"),
    ):
        if field in claims:
            continue
        values = sorted({str(v) for _, c in rows if (v := _confirmed(c, fact_name)) is not None})
        if 2 <= len(values) <= 4:
            # Source transmission descriptions can be English free text. Ask
            # for the seller's documented type without echoing that prose.
            if field == "transmission" or (
                field != "engine" and any(value not in buyer.VALUE_LABELS for value in values)
            ):
                return f"{az if language == 'az' else ru}?"
            joined = (" или " if language == "ru" else " və ya ").join(
                display(field, value) for value in values
            )
            suffix = " л" if field == "engine" else ""
            return f"{az if language == 'az' else ru}: {joined}{suffix}?"
    if "year" not in claims:
        return (
            pick(language, "Какой год выпуска указан?", "Avtomobilin buraxılış ili neçədir?")
        )
    return (
        pick(language, "Какой двигатель указан в документах автомобиля?", "Avtomobilin sənədlərində hansı mühərrik göstərilib?")
    )


def _conflict_display(field: str, value: object, language: str) -> str:
    raw = str(value)
    if field == "transmission":
        labels = buyer.VALUE_LABELS.get(raw)
        if labels:
            return pick(language, labels[0], labels[1])
        key = _key(raw)
        if "manual" in key or "mexan" in key:
            return pick(language, "Механика", "Mexaniki")
        if "cvt" in key or "variator" in key:
            return pick(language, "Вариатор", "Variator")
        if "automatic" in key or "dct" in key or "dsg" in key:
            return pick(language, "Автоматическая", "Avtomatik")
        return pick(language, "Коробка передач", "Sürətlər qutusu")
    if field == "drivetrain" and _key(raw) in {"front", "frontwheeldrive"}:
        raw = "FWD"
    if field == "fuel" and _key(raw) in {"gasoline", "petrol"}:
        raw = "GASOLINE"
    if field == "body" and raw.upper() in buyer.VALUE_LABELS:
        raw = raw.upper()
    labels = buyer.VALUE_LABELS.get(raw)
    return pick(language, labels[0], labels[1]) if labels else raw


def _match(rows: list, claims: dict[str, ClaimDraft], language: str) -> dict:
    empty = {"status": "NO_MATCH", "candidates": [], "question": None, "conflicts": []}
    make = claims.get("make")
    model = claims.get("model")
    if not make or not model:
        return empty
    market = claims.get("market")
    if market and market.normalized_value not in {"US", "USA", None, ""}:
        return {**empty, "status": "OUT_OF_PRODUCT_SCOPE"}
    named = [
        (v, c)
        for v, c in rows
        if _key(c["make"]) == _key(make.normalized_value)
        and _key(c["model"]) == _key(model.normalized_value)
    ]
    if not named:
        return {**empty, "status": "OUT_OF_PRODUCT_SCOPE"}
    year = claims.get("year")
    if year and year.normalized_value:
        named = [(v, c) for v, c in named if c["model_year"] == year.normalized_value]
        if not named:
            return empty
    candidates = named
    field_fact = (
        ("fuel", "fuel"),
        ("engine", "engine_displacement"),
        ("transmission", "transmission_family"),
        ("drivetrain", "drivetrain"),
        ("body", "body"),
    )
    for field, fact_name in field_fact:
        if field not in claims or claims[field].normalized_value is None:
            continue
        compatible = []
        catalog_values = set()
        for variant, catalog in candidates:
            actual = _confirmed(catalog, fact_name)
            if field == "transmission" and actual is None:
                actual = _confirmed(catalog, "transmission_description")
            if actual is not None:
                catalog_values.add(_conflict_display(field, actual, language))
            fits = (
                _transmission_claim_fit(claims[field].normalized_value, catalog)
                if field == "transmission"
                else _claim_fit(field, claims[field].normalized_value, actual)
            )
            if fits is not False:
                compatible.append((variant, catalog))
        if not compatible and catalog_values:
            return {
                "status": "CLAIM_CONFLICT",
                "candidates": [_candidate(v, c) for v, c in candidates[:8]],
                "question": None,
                "conflicts": [
                    {
                        "field_name": field,
                        "claimed": claims[field].raw_value,
                        "catalog_values": sorted(catalog_values)[:8],
                    }
                ],
            }
        candidates = compatible
    if not candidates:
        return empty
    unresolved = any(
        (
            _transmission_claim_fit(claims[field].normalized_value, catalog)
            if field == "transmission"
            else _claim_fit(field, claims[field].normalized_value, _confirmed(catalog, fact_name))
        )
        is None
        for field, fact_name in field_fact
        if field in claims and claims[field].normalized_value is not None
        for _, catalog in candidates
    )
    status = (
        "EXACT_MATCH" if len(candidates) == 1 and year and not unresolved else "MULTIPLE_CANDIDATES"
    )
    return {
        "status": status,
        "candidates": [_candidate(v, c) for v, c in candidates[:8]],
        "question": _question(candidates, claims, language)
        if status == "MULTIPLE_CANDIDATES"
        else None,
        "conflicts": [],
    }


def _consumer_rows(db) -> list:
    # The established buyer projection applies fact-level commercial rights.
    # Its source, candidate and resolver tables are never mutated by an intake.
    if db is None:
        rows = buyer.records(db, production_safe=True)
        return [(v, c) for v, c in buyer.active_us_rows(rows) if c.get("model_year", 0) >= 2012]
    bind = db.get_bind()

    def stamp() -> tuple:
        # Listing writes do not alter these catalog/rights tables. A rights
        # revocation or publication changes an ORM updated_at and invalidates
        # the cache before the next intake. Scope file changes invalidate it too.
        tables = (VehicleVariant, CommercialFactClaim, SourceRegistry)
        states = []
        for table in tables:
            count, newest = db.execute(
                select(func.count(table.id), func.max(table.updated_at))
            ).one()
            states.append((count, newest.isoformat() if newest else None))
        stat = POLICY_PATH.stat()
        return (*states, stat.st_mtime_ns, stat.st_size)

    before = stamp()
    with _CATALOG_CACHE_LOCK:
        cached = _CATALOG_CACHE.get(bind)
        if cached and cached[0] == before:
            return cached[1]
        rows = buyer.records(db, production_safe=True)
        visible = [(v, c) for v, c in buyer.active_us_rows(rows) if c.get("model_year", 0) >= 2012]
        after = stamp()
        if before == after:
            if len(_CATALOG_CACHE) >= 4:
                _CATALOG_CACHE.pop(next(iter(_CATALOG_CACHE)))
            _CATALOG_CACHE[bind] = (after, visible)
        return visible


def production_visible_us_rows(db) -> list:
    """Rights-cleared, active US model-year rows shared by consumer surfaces."""
    return _consumer_rows(db)


def _read(request: ListingIntakeRequest) -> dict:
    snapshot = request.snapshot
    match = request.match
    return {
        "id": request.id,
        "snapshot": {
            "source_type": snapshot.source_type,
            "source_url": snapshot.source_url,
            "source_listing_id": snapshot.source_listing_id,
            "captured_at": snapshot.captured_at.replace(tzinfo=UTC)
            if snapshot.captured_at.tzinfo is None
            else snapshot.captured_at,
            "input_type": snapshot.input_type,
            "content_hash": snapshot.content_hash,
            "raw_content_locator": snapshot.raw_content_locator,
            "language": snapshot.language,
            "parser_version": snapshot.parser_version,
        },
        "claims": [
            {
                "field_name": claim.field_name,
                "raw_value": claim.raw_value,
                "normalized_value": claim.normalized_value,
                "unit": claim.unit,
                "claim_type": claim.claim_type,
                "source_locator": claim.source_locator,
                "confidence": claim.confidence,
            }
            for claim in sorted(
                snapshot.claims,
                key=lambda c: (
                    FIELD_ORDER.index(c.field_name)
                    if c.field_name in FIELD_ORDER
                    else len(FIELD_ORDER)
                ),
            )
        ],
        "match": {
            "status": match.status,
            "candidates": match.candidates,
            "question": match.question,
            "conflicts": match.conflicts,
        },
        "next_step": "PROVIDE_CONTENT" if snapshot.input_type == "URL_REFERENCE" else "VIEW_RESULT",
    }


def get_intake(db, user_id: str, intake_id: str) -> dict | None:
    request = db.scalar(
        select(ListingIntakeRequest).where(
            ListingIntakeRequest.id == intake_id,
            ListingIntakeRequest.user_id == user_id,
        )
    )
    return _read(request) if request else None


def _existing_in_language(
    db,
    existing: ListingIntakeRequest,
    value: ListingIntakeCreate,
    claims: dict[str, ClaimDraft],
) -> dict:
    # Language is presentation state, not a new seller snapshot. Re-importing
    # the same material in AZ/RU keeps one source and one claim set.
    if existing.language != value.language:
        existing.language = value.language
        existing.snapshot.language = value.language
        if value.input_type != "URL_REFERENCE":
            rows = _consumer_rows(db)
            localized = _match(rows, _canonical_claims(claims, rows), value.language)
            existing.match.status = localized["status"]
            existing.match.candidates = localized["candidates"]
            existing.match.question = localized["question"]
            existing.match.conflicts = localized["conflicts"]
        db.commit()
    return _read(existing)


def create_intake(db, user_id: str, value: ListingIntakeCreate) -> dict:
    source_url, listing_id = (None, None)
    if value.source_url:
        source_url, listing_id = validate_turbo_url(value.source_url)
    if value.input_type == "URL_REFERENCE":
        claims: dict[str, ClaimDraft] = {}
        sanitized_content = None
        raw_content = source_url or ""
    elif value.input_type == "MANUAL":
        claims, sanitized_content = TurboAzManualInputAdapter().parse(value)
        raw_content = json.dumps(value.fields, ensure_ascii=False, sort_keys=True)
    else:
        claims, sanitized_content = TurboAzUserProvidedContentAdapter().parse(value)
        raw_content = value.text if value.input_type == "TEXT" else value.html
    if listing_id is None and "listing_id" in claims:
        claimed_id = str(claims["listing_id"].normalized_value)
        if re.fullmatch(r"[0-9]{4,12}", claimed_id):
            listing_id = claimed_id
    content_hash = hashlib.sha256((raw_content or "").encode("utf-8")).hexdigest()
    request_key = hashlib.sha256(
        json.dumps(
            [value.input_type, source_url, content_hash],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    existing = db.scalar(
        select(ListingIntakeRequest).where(
            ListingIntakeRequest.user_id == user_id,
            ListingIntakeRequest.request_key == request_key,
        )
    )
    if existing:
        return _existing_in_language(db, existing, value, claims)
    if value.input_type == "URL_REFERENCE":
        match = {"status": "NO_MATCH", "candidates": [], "question": None, "conflicts": []}
    else:
        rows = _consumer_rows(db)
        claims = _canonical_claims(claims, rows)
        match = _match(rows, claims, value.language)
    request = ListingIntakeRequest(
        user_id=user_id, request_key=request_key, language=value.language
    )
    snapshot = ListingSnapshot(
        source_type="TURBO_AZ" if source_url else "USER_PROVIDED",
        source_url=source_url,
        source_listing_id=listing_id,
        captured_at=datetime.now(UTC),
        input_type=value.input_type,
        content_hash=content_hash,
        language=value.language,
        parser_version=PARSER_VERSION,
        sanitized_content=sanitized_content,
    )
    request.snapshot = snapshot
    request.match = ListingMatchResult(**match)
    snapshot.claims = [
        ListingFieldClaim(
            field_name=draft.field_name,
            raw_value=draft.raw_value,
            normalized_value=draft.normalized_value,
            unit=draft.unit,
            claim_type="SELLER_CLAIM",
            source_locator=draft.source_locator,
            confidence=draft.confidence,
        )
        for draft in claims.values()
    ]
    db.add(request)
    db.flush()
    if sanitized_content is not None:
        snapshot.raw_content_locator = f"db:listing_snapshots/{snapshot.id}/sanitized_content"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(ListingIntakeRequest).where(
                ListingIntakeRequest.user_id == user_id,
                ListingIntakeRequest.request_key == request_key,
            )
        )
        if existing is None:
            raise
        return _existing_in_language(db, existing, value, claims)
    return _read(request)

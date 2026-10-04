# ruff: noqa: E501
"""Plans and rights (product phase, stage 6), behind the subscription_v1 flag.

Free: the garage with one car, the basic maintenance schedule and its reminders, reading the
owners club, the public car pages.
Subscription ("my car under the expert's eye"): several cars, personal hints (the car's known
issues) and recall notifications, the AI mechanic, writing in the club, the service log export,
no ads. One-time: the VIN report (unchanged, outside the subscription).

Prices per region come from the configuration (subscription_prices); a trial period
(subscription_trial_days) once per user. Payment through App Store / Google Play is a stub:
outside production a "purchase" activates a period without any charge; in production the
purchase answers STORE_NOT_CONNECTED until the stores are connected. While the flag is off every
right is granted (the behaviour before this stage).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.core.english import pick
from app.models.subscription import Subscription
from app.models.user import User

FEATURES = ("GARAGE_MULTIPLE_CARS", "PERSONAL_HINTS", "RECALL_ALERTS", "AI_MECHANIC", "CLUB_WRITE", "LOG_EXPORT", "NO_ADS")
FREE_FEATURES = ("GARAGE_ONE_CAR", "MAINTENANCE_SCHEDULE", "CLUB_READ", "PUBLIC_PAGES")
FREE_CARS = 1
LABELS = {
    "GARAGE_ONE_CAR": ("Гараж: 1 машина", "Qaraj: 1 avtomobil", "Garage: 1 car"),
    "MAINTENANCE_SCHEDULE": ("Базовый регламент ТО и напоминания", "Əsas texniki xidmət reqlamenti və xatırlatmalar", "Basic maintenance schedule and reminders"),
    "CLUB_READ": ("Чтение клуба владельцев", "Sahiblər klubunu oxumaq", "Reading the owners club"),
    "PUBLIC_PAGES": ("Публичные страницы по машинам", "Avtomobillər üzrə açıq səhifələr", "Public car pages"),
    "GARAGE_MULTIPLE_CARS": ("Несколько машин в гараже", "Qarajda bir neçə avtomobil", "Several cars in the garage"),
    "PERSONAL_HINTS": ("Персональные подсказки: известные проблемы вашей машины", "Fərdi ipuçları: avtomobilinizin məlum problemləri", "Personal hints: your car's known issues"),
    "RECALL_ALERTS": ("Уведомления об отзывных кампаниях", "Geri çağırma kampaniyaları barədə bildirişlər", "Recall alerts"),
    "AI_MECHANIC": ("ИИ-механик по вашей машине", "Avtomobiliniz üzrə Sİ-mexanik", "AI mechanic for your car"),
    "CLUB_WRITE": ("Писать в клубе владельцев", "Sahiblər klubunda yazmaq", "Writing in the owners club"),
    "LOG_EXPORT": ("Экспорт журнала обслуживания (PDF)", "Xidmət jurnalının ixracı (PDF)", "Service log export (PDF)"),
    "NO_ADS": ("Без рекламы", "Reklamsız", "No ads"),
}


class SubscriptionRequired(Exception):
    def __init__(self, feature: str):
        super().__init__(feature)
        self.feature = feature


def enabled(settings=None) -> bool:
    settings = settings or get_settings()
    if settings.subscription_v1 is not None:
        return bool(settings.subscription_v1)
    return settings.environment != "production"


def _aware(value: datetime | None) -> datetime | None:
    return value if value is None or value.tzinfo else value.replace(tzinfo=UTC)


def current(db, user: User) -> Subscription | None:
    """The subscription that gives rights now (TRIAL / ACTIVE / CANCELED until its period ends)."""
    now = datetime.now(UTC)
    rows = db.scalars(select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.period_end.desc()))
    for row in rows:
        if row.status in ("TRIAL", "ACTIVE", "CANCELED") and _aware(row.period_end) > now:
            return row
        if row.status in ("TRIAL", "ACTIVE") and _aware(row.period_end) <= now:
            row.status = "EXPIRED"
    return None


def subscribed(db, user: User) -> bool:
    return current(db, user) is not None


def allows(db, user: User, feature: str) -> bool:
    if not enabled() or user.is_admin:
        return True
    if feature in FREE_FEATURES:
        return True
    return subscribed(db, user)


def require(db, user: User, feature: str) -> None:
    if not allows(db, user, feature):
        raise SubscriptionRequired(feature)


def region_of(user: User) -> str:
    country = (user.country_code or "").upper()
    if country in ("US", "CA", "AZ"):
        return country
    return "AZ" if user.preferred_language == "az" else "US"


def price(region: str) -> dict:
    prices = get_settings().subscription_prices
    return prices.get(region) or prices["US"]


def offer(db, user: User, language: str) -> dict:
    sub = current(db, user)
    region = region_of(user)
    p = price(region)
    trial_used = db.scalar(select(Subscription).where(Subscription.user_id == user.id, Subscription.store == "TRIAL")) is not None
    settings = get_settings()
    return {
        "enabled": enabled(),
        "tier": "SUBSCRIPTION" if sub else "FREE",
        "status": sub.status if sub else None,
        "period_end": _aware(sub.period_end).isoformat() if sub else None,
        "store": sub.store if sub else None,
        "region": region,
        "price": {"amount_minor": p["monthly_minor"], "currency": p["currency"], "period": "MONTH"},
        "trial": {"days": settings.subscription_trial_days, "available": not trial_used and sub is None},
        "free": [{"key": k, "label": pick(language, *LABELS[k])} for k in FREE_FEATURES],
        "subscription": [{"key": k, "label": pick(language, *LABELS[k])} for k in FEATURES],
        "one_time": [{"key": "VIN_REPORT", "label": pick(language, "VIN-отчёт об истории — разовая покупка", "VIN tarixçə hesabatı — birdəfəlik alış", "VIN history report — a one-time purchase")}],
        "stores": {"APP_STORE": "STUB", "GOOGLE_PLAY": "STUB"},
        "purchase_stub": settings.environment != "production",
        "rights": {f: allows(db, user, f) for f in (*FREE_FEATURES, *FEATURES)},
    }


def start_trial(db, user: User) -> Subscription:
    if current(db, user):
        raise ValueError("ALREADY_SUBSCRIBED")
    if db.scalar(select(Subscription).where(Subscription.user_id == user.id, Subscription.store == "TRIAL")):
        raise ValueError("TRIAL_USED")
    sub = Subscription(user_id=user.id, status="TRIAL", store="TRIAL", region=region_of(user),
                       period_end=datetime.now(UTC) + timedelta(days=get_settings().subscription_trial_days))
    db.add(sub)
    db.flush()
    return sub


def purchase_stub(db, user: User, store: str) -> Subscription:
    """A store purchase without a store: outside production only, no charge."""
    if get_settings().environment == "production":
        raise ValueError("STORE_NOT_CONNECTED")
    region = region_of(user)
    p = price(region)
    sub = current(db, user)
    if sub and sub.store == "TRIAL":
        sub.status, sub.period_end = "EXPIRED", datetime.now(UTC)
    paid = Subscription(user_id=user.id, status="ACTIVE", store="STUB", region=region, price_minor=p["monthly_minor"],
                        currency=p["currency"], period_end=datetime.now(UTC) + timedelta(days=30), external_id=f"stub:{store}")
    db.add(paid)
    db.flush()
    return paid


def cancel(db, user: User) -> Subscription | None:
    sub = current(db, user)
    if sub and sub.status != "CANCELED":
        sub.status, sub.canceled_at = "CANCELED", datetime.now(UTC)  # rights stay until the period ends
    return sub

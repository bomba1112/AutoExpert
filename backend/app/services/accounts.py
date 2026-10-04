# ruff: noqa: E501
"""Account readiness (product phase, stage 4): email confirmation, password recovery and
protection against password guessing, before users can write in the owners club.

- Tokens are random, single-use and short-lived; only their sha256 is stored.
- A password reset request answers the same whether the address exists or not (no enumeration).
- Login: 5 failed attempts for one address within 15 minutes, or 30 from one IP, lock further
  attempts for 15 minutes (429). A successful reset or change revokes older sessions.
- Messages go to the outbox; a real mail / SMS provider implements MessageSender at deployment
  (the default sender only logs). Phone confirmation needs an SMS provider: the outbox already has
  the SMS channel.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.english import pick
from app.models.account import AuthToken, LoginAttempt, OutboxMessage
from app.models.user import User

log = logging.getLogger("autoexpert.accounts")
WINDOW = timedelta(minutes=15)
MAX_PER_EMAIL = 5
MAX_PER_IP = 30
TTL = {"VERIFY_EMAIL": timedelta(hours=48), "RESET_PASSWORD": timedelta(hours=1)}
TEXT = {
    "VERIFY_EMAIL": (("Подтвердите почту — Auto Expert", "E-poçtunuzu təsdiqləyin — Auto Expert", "Confirm your email — Auto Expert"),
                     ("Чтобы писать в клубе владельцев, подтвердите адрес: {link}\nСсылка действует 48 часов.",
                      "Sahiblər klubunda yazmaq üçün ünvanı təsdiqləyin: {link}\nKeçid 48 saat etibarlıdır.",
                      "To write in the owners club, confirm your address: {link}\nThe link is valid for 48 hours.")),
    "RESET_PASSWORD": (("Восстановление пароля — Auto Expert", "Şifrənin bərpası — Auto Expert", "Reset your password — Auto Expert"),
                       ("Ссылка для нового пароля: {link}\nОна действует 1 час. Если вы не просили — просто игнорируйте письмо.",
                        "Yeni şifrə üçün keçid: {link}\n1 saat etibarlıdır. Siz istəməmisinizsə, məktubu nəzərə almayın.",
                        "Your password reset link: {link}\nIt is valid for 1 hour. If you didn't ask for it, ignore this email.")),
}


class MessageSender(Protocol):
    def send(self, message: OutboxMessage) -> bool: ...


class LogOnlySender:
    def send(self, message: OutboxMessage) -> bool:
        log.info("outbox (no provider) %s %s %s", message.channel, message.purpose, message.id)
        return False


_SENDER: MessageSender = LogOnlySender()


def set_sender(sender: MessageSender) -> None:
    global _SENDER
    _SENDER = sender


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue_token(db, user: User, purpose: str) -> str:
    raw = secrets.token_urlsafe(32)
    db.add(AuthToken(user_id=user.id, purpose=purpose, token_hash=_hash(raw), expires_at=datetime.now(UTC) + TTL[purpose]))
    return raw


def consume_token(db, raw: str, purpose: str) -> User | None:
    token = db.scalar(select(AuthToken).where(AuthToken.token_hash == _hash(raw or ""), AuthToken.purpose == purpose))
    if token is None or token.used_at is not None or _aware(token.expires_at) < datetime.now(UTC):
        return None
    token.used_at = datetime.now(UTC)
    return db.get(User, token.user_id)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def send_link(db, user: User, purpose: str, raw: str, language: str) -> OutboxMessage:
    base = get_settings().public_app_url.rstrip("/")
    route = {"VERIFY_EMAIL": "verify-email", "RESET_PASSWORD": "reset-password"}[purpose]
    subject, body = TEXT[purpose]
    message = OutboxMessage(user_id=user.id, channel="EMAIL", purpose=purpose, recipient=user.email,
                            subject=pick(language, *subject), body=pick(language, *body).format(link=f"{base}/#/{route}/{raw}"))
    db.add(message)
    db.flush()
    if _SENDER.send(message):
        message.sent_at = datetime.now(UTC)
    return message


def start_email_verification(db, user: User, language: str) -> OutboxMessage | None:
    if user.email_verified_at or user.email.endswith(".invalid"):
        return None  # demo sessions have no mailbox
    return send_link(db, user, "VERIFY_EMAIL", issue_token(db, user, "VERIFY_EMAIL"), language)


def login_blocked(db, email: str, ip: str | None) -> bool:
    since = datetime.now(UTC) - WINDOW
    failed = select(func.count()).select_from(LoginAttempt).where(LoginAttempt.success.is_(False), LoginAttempt.created_at >= since)
    if (db.scalar(failed.where(LoginAttempt.email == email)) or 0) >= MAX_PER_EMAIL:
        return True
    return bool(ip) and (db.scalar(failed.where(LoginAttempt.ip == ip)) or 0) >= MAX_PER_IP


def record_attempt(db, email: str, ip: str | None, success: bool) -> None:
    db.add(LoginAttempt(email=email, ip=ip, success=success))


def can_write(user: User) -> bool:
    """Writing in the club needs a confirmed email; the preview's demo sessions are allowed."""
    settings = get_settings()
    if user.email_verified_at is not None:
        return True
    return settings.environment != "production" and settings.demo_mode and user.email.endswith(".invalid")

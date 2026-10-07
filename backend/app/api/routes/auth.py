from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DBSession, oauth2_scheme
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import (
    DemoLoginRequest,
    EmailRequest,
    LoginRequest,
    PasswordResetConfirm,
    RegisterRequest,
    TokenRequest,
    TokenResponse,
    UserResponse,
)
from app.services import accounts

router = APIRouter(prefix="/auth", tags=["auth"])


def _token(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, is_admin=user.is_admin),
        user=UserResponse.model_validate(user),
    )


@router.post("/local-session/renew", response_model=TokenResponse)
def renew_local_session(
    db: DBSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> TokenResponse:
    """Renew a signed local test session without replacing its user or saved reports."""
    settings = get_settings()
    if (
        settings.environment == "production"
        or not settings.developer_mode
        or not settings.demo_mode
    ):
        raise HTTPException(404, "Local session renewal unavailable")
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            options={"verify_exp": False, "require": ["sub", "iat", "exp"]},
        )
        if datetime.now(UTC).timestamp() - float(payload["exp"]) > 30 * 86400:
            raise ValueError("Session too old")
        user = db.get(User, payload["sub"])
        if user is None or not user.is_active:
            raise ValueError("User unavailable")
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(401, "Invalid local session") from None
    return _token(user)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(value: RegisterRequest, db: DBSession) -> TokenResponse:
    email = value.email.casefold()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=email,
        password_hash=hash_password(value.password),
        preferred_language=value.preferred_language,
        country_code=value.country_code,
        is_admin=False,
    )
    db.add(user)
    db.flush()
    accounts.start_email_verification(db, user, value.preferred_language)
    db.commit()
    db.refresh(user)
    return _token(user)


@router.post("/login", response_model=TokenResponse)
def login(value: LoginRequest, db: DBSession, request: Request) -> TokenResponse:
    email = value.email.casefold()
    ip = request.client.host if request.client else None
    if accounts.login_blocked(db, email, ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Too many attempts, try again in 15 minutes")
    user = db.scalar(select(User).where(User.email == email))
    # An inactive account gets the same answer as a wrong password (no account enumeration);
    # the password is still checked, so both answers take the same time.
    ok = user is not None and verify_password(value.password, user.password_hash) and user.is_active
    accounts.record_attempt(db, email, ip, ok)
    db.commit()
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _token(user)


@router.post("/verify-email", response_model=UserResponse)
def verify_email(value: TokenRequest, db: DBSession) -> UserResponse:
    user = accounts.consume_token(db, value.token, "VERIFY_EMAIL")
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid or expired link")
    user.email_verified_at = user.email_verified_at or datetime.now(UTC)
    db.commit()
    return UserResponse.model_validate(user)


@router.post("/verify-email/resend", status_code=status.HTTP_202_ACCEPTED)
def resend_verification(db: DBSession, user: CurrentUser) -> dict:
    accounts.start_email_verification(db, user, user.preferred_language)
    db.commit()
    return {"accepted": True}


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def password_reset_request(value: EmailRequest, db: DBSession) -> dict:
    """The same answer whether the address exists or not."""
    user = db.scalar(select(User).where(User.email == value.email.casefold()))
    if user is not None and user.is_active and not user.email.endswith(".invalid"):
        raw = accounts.issue_token(db, user, "RESET_PASSWORD")
        accounts.send_link(db, user, "RESET_PASSWORD", raw, value.language)
        db.commit()
    return {"accepted": True}


@router.post("/password-reset/confirm", response_model=TokenResponse)
def password_reset_confirm(value: PasswordResetConfirm, db: DBSession) -> TokenResponse:
    user = accounts.consume_token(db, value.token, "RESET_PASSWORD")
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid or expired link")
    user.password_hash = hash_password(value.password)
    user.password_changed_at = datetime.now(UTC).replace(microsecond=0)
    # the link proved the mailbox
    user.email_verified_at = user.email_verified_at or datetime.now(UTC)
    db.commit()
    return _token(user)


@router.post("/demo", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def create_isolated_demo_session(value: DemoLoginRequest, db: DBSession) -> TokenResponse:
    settings = get_settings()
    if settings.environment == "production" or not settings.demo_mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo mode is disabled")
    identity = uuid4()
    user = User(
        email=f"demo-{identity}@demo.autoexpert.invalid",
        password_hash=hash_password(f"unused-{uuid4()}"),
        preferred_language=value.preferred_language,
        country_code="AZ",
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token(user)

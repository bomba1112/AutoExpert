from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import DBSession, oauth2_scheme
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import (
    DemoLoginRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

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
    db.commit()
    db.refresh(user)
    return _token(user)


@router.post("/login", response_model=TokenResponse)
def login(value: LoginRequest, db: DBSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == value.email.casefold()))
    if user is None or not verify_password(value.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
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

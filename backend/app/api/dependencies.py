from datetime import UTC
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# The app's own token travels in X-AutoExpert-Token: on the closed staging the Authorization header
# belongs to the site's Basic Auth (the browser attaches it), and a Bearer token there would replace
# it and make the proxy ask for the site password again. Authorization: Bearer keeps working
# (mobile apps, tests); Authorization: Basic is not an app token and is ignored.
TOKEN_HEADER = "X-AutoExpert-Token"
_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
DBSession = Annotated[Session, Depends(get_db)]


def oauth2_scheme(request: Request, bearer: Annotated[str | None, Depends(_bearer)]) -> str:
    token = (request.headers.get(TOKEN_HEADER) or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    token = token or bearer
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def get_current_user(db: DBSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise credentials_error
    except jwt.PyJWTError as exc:
        raise credentials_error from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    changed = user.password_changed_at
    if changed is not None:
        changed = changed if changed.tzinfo else changed.replace(tzinfo=UTC)
        if int(payload.get("iat") or 0) < int(changed.timestamp()):
            raise credentials_error  # a session from before the password reset
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]

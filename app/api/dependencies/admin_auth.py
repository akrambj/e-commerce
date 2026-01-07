from __future__ import annotations

from fastapi import Cookie, Depends

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import ACCESS_TOKEN_COOKIE, decode_access_token


def require_admin(
    access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
):
    if not access_token:
        raise AppError(message="Not authenticated", code="auth_required")

    payload = decode_access_token(access_token)

    s = get_settings()
    if payload.get("sub") != s.admin_email:
        raise AppError(message="Not authorized", code="not_admin")

    return payload

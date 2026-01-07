from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt

from app.core.config import get_settings
from app.core.exceptions import AppError


@dataclass
class AuthError(AppError):
    code: str = "auth_error"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(*, subject: str) -> str:
    """
    Create a signed JWT access token.
    subject: stable identifier (for v1 we use admin email).
    """
    s = get_settings()

    now = _utcnow()
    exp = now + timedelta(minutes=int(s.jwt_access_token_expires_minutes))

    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "access",
    }

    token = jwt.encode(payload, s.jwt_secret_key, algorithm="HS256")
    # pyjwt may return str already; keep return type stable
    return token if isinstance(token, str) else token.decode("utf-8")


def decode_access_token(token: str) -> dict:
    """
    Validate + decode JWT. Raises AuthError on any failure.
    """
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as e:
        raise AuthError(message="Token expired", details={"reason": "expired"}) from e
    except jwt.InvalidTokenError as e:
        raise AuthError(message="Invalid token", details={"reason": "invalid"}) from e

    if payload.get("type") != "access":
        raise AuthError(message="Invalid token type", details={"type": payload.get("type")})

    if "sub" not in payload:
        raise AuthError(message="Invalid token payload", details={"missing": "sub"})

    return payload


# Cookie name (v1)
ACCESS_TOKEN_COOKIE = "access_token"


def build_auth_cookie(*, token: str) -> dict:
    """
    Central place for cookie settings.
    We'll later add refresh tokens + CSRF, but not now.
    """
    s = get_settings()
    max_age = int(s.jwt_access_token_expires_minutes) * 60

    return {
        "key": ACCESS_TOKEN_COOKIE,
        "value": token,
        "httponly": True,
        "secure": False if s.env == "development" else True,
        "samesite": "lax",
        "path": "/",
        "max_age": max_age,
    }

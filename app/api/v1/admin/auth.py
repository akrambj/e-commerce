from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.responses import ok
from app.core.security import ACCESS_TOKEN_COOKIE, build_auth_cookie, create_access_token

router = APIRouter(prefix="/admin", tags=["admin:auth"])


class AdminLoginIn(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


@router.post("/login", response_model=None)
def admin_login(payload: AdminLoginIn, response: Response):
    s = get_settings()

    email = payload.email.strip().lower()
    password = payload.password

    # v1: single admin from env
    if email != s.admin_email.strip().lower() or password != s.admin_password:
        # keep response generic (don’t leak which one failed)
        return ok({"authenticated": False}, message="Invalid credentials")

    token = create_access_token(subject=email)
    cookie = build_auth_cookie(token=token)

    response.set_cookie(**cookie)
    return ok({"authenticated": True}, message="Logged in")


@router.post("/logout", response_model=None)
def admin_logout(response: Response):
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
    )
    return ok({"logged_out": True}, message="Logged out")

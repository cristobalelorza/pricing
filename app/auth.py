"""Simple session-based authentication for Precio."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

SECRET_KEY = os.getenv("SECRET_KEY", "pricing-dev-secret-change-in-prod")
SESSION_COOKIE = "pricing_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

PUBLIC_PATHS = {"/login", "/register", "/static"}


def _sign(data: str) -> str:
    sig = hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{data}.{sig}"


def _verify(token: str) -> str | None:
    if "." not in token:
        return None
    data, sig = token.rsplit(".", 1)
    expected = hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
    if hmac.compare_digest(sig, expected):
        return data
    return None


def create_session_token(user_id: str) -> str:
    payload = json.dumps({"uid": user_id, "exp": int(time.time()) + SESSION_MAX_AGE})
    return _sign(payload)


def get_user_id_from_token(token: str) -> str | None:
    data = _verify(token)
    if not data:
        return None
    try:
        payload = json.loads(data)
        if payload.get("exp", 0) < time.time():
            return None
        return payload.get("uid")
    except (json.JSONDecodeError, Exception):
        return None


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow public paths
        if path.startswith("/static") or path in PUBLIC_PATHS:
            return await call_next(request)

        # Check session cookie
        token = request.cookies.get(SESSION_COOKIE, "")
        user_id = get_user_id_from_token(token)

        if not user_id:
            return RedirectResponse(url="/login", status_code=302)

        # Attach user_id to request state
        request.state.user_id = user_id
        return await call_next(request)

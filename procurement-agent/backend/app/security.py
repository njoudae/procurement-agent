from __future__ import annotations

import base64
import hashlib
import hmac
import time

from fastapi import HTTPException, Request, Response, status

from app.config import get_settings
from app.decorators import require_permission


ADMIN_SESSION_COOKIE = "procurement_admin_session"
DEV_SESSION_TTL_SECONDS = 8 * 60 * 60
LOCAL_CLIENT_HOSTS = {"127.0.0.1", "::1", "localhost"}


def create_dev_admin_session(response: Response, request: Request) -> dict[str, str]:
    """Create a local-development admin session without exposing secrets to JS.

    Production auth should replace this endpoint with SSO/OIDC login, server-side
    sessions, RBAC claims, CSRF protection, and audit identity propagation.
    """
    settings = get_settings()
    if settings.environment.lower() != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dev auth is disabled")
    if not settings.admin_api_token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="ADMIN_API_TOKEN must be set")
    if not _is_local_request(request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dev auth is local-only")

    token = _sign_session("dev-admin", int(time.time()), settings.admin_api_token)
    response.set_cookie(
        key=ADMIN_SESSION_COOKIE,
        value=token,
        max_age=DEV_SESSION_TTL_SECONDS,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )
    return {"status": "ok", "mode": "development"}


def clear_admin_session(response: Response) -> dict[str, str]:
    response.delete_cookie(ADMIN_SESSION_COOKIE, path="/")
    return {"status": "ok"}


@require_permission("admin")
def require_admin(request: Request) -> None:
    settings = get_settings()
    environment = settings.environment.lower()

    if environment == "test":
        return

    if environment == "development":
        if _is_valid_session(request.cookies.get(ADMIN_SESSION_COOKIE), settings.admin_api_token):
            return
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin session required")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Production admin authentication is not configured. Add SSO/OIDC session RBAC before deployment.",
    )


def _is_local_request(request: Request) -> bool:
    client_host = request.client.host if request.client else ""
    return client_host in LOCAL_CLIENT_HOSTS


def _sign_session(subject: str, issued_at: int, secret: str) -> str:
    payload = f"{subject}:{issued_at}".encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def _is_valid_session(token: str | None, secret: str | None) -> bool:
    if not token or not secret or "." not in token:
        return False
    encoded_payload, signature = token.rsplit(".", 1)
    expected_signature = hmac.new(secret.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return False
    try:
        padded = encoded_payload + "=" * (-len(encoded_payload) % 4)
        payload = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        subject, issued_at_text = payload.rsplit(":", 1)
        issued_at = int(issued_at_text)
    except (ValueError, UnicodeDecodeError):
        return False
    if subject != "dev-admin":
        return False
    return time.time() - issued_at <= DEV_SESSION_TTL_SECONDS

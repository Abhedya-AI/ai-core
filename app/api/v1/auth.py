"""
app/api/v1/auth.py — Authentication & Authorization Endpoints.

Public endpoints (no auth required):
  POST /auth/login      — username/password → JWT pair
  POST /auth/refresh    — refresh token → new JWT pair

Protected endpoints (require valid JWT):
  POST /auth/logout     — revoke current session
  POST /auth/logout-all — revoke all sessions (all devices)
  GET  /auth/me         — current user profile

Admin endpoints (require admin.users.write):
  GET  /admin/users     — list all users (in admin.py)
  POST /admin/users     — create user (in admin.py)
  POST /admin/api-keys  — create API key
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import get_current_principal
from app.modules.auth.models import Principal
from app.modules.auth.schemas import LoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.modules.auth.service import AuthService, get_auth_service_instance

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_svc() -> AuthService:
    return get_auth_service_instance()


@router.post(
    "/login",
    response_model=StandardResponse[TokenResponse],
    summary="Login with username and password",
    operation_id="auth_login",
)
async def login(
    body: LoginRequest,
    request: Request,
    svc: AuthService = Depends(_get_svc),
) -> StandardResponse[TokenResponse]:
    """Authenticate with username/password credentials and receive a JWT token pair."""
    request_id = getattr(request.state, "request_id", "")
    ip = request.client.host if request.client else None
    ua = request.headers.get("User-Agent")
    tokens = await svc.login(body, ip=ip, ua=ua)
    return make_response(data=tokens, trace_id=request_id, request_id=request_id)


@router.post(
    "/refresh",
    response_model=StandardResponse[TokenResponse],
    summary="Rotate JWT access token using refresh token",
    operation_id="auth_refresh",
)
async def refresh_token(
    body: RefreshRequest,
    request: Request,
    svc: AuthService = Depends(_get_svc),
) -> StandardResponse[TokenResponse]:
    """Exchange a valid refresh token for a new access + refresh token pair (rotation)."""
    request_id = getattr(request.state, "request_id", "")
    tokens = await svc.refresh(body.refresh_token)
    return make_response(data=tokens, trace_id=request_id, request_id=request_id)


@router.post(
    "/logout",
    response_model=StandardResponse[dict],
    summary="Logout from current session",
    operation_id="auth_logout",
)
async def logout(
    request: Request,
    principal: Principal = Depends(get_current_principal),
    svc: AuthService = Depends(_get_svc),
) -> StandardResponse[dict]:
    """Revoke the current session (single device logout)."""
    request_id = getattr(request.state, "request_id", "")
    session_id = principal.session_id or ""
    await svc.logout(session_id=session_id, user_id=principal.user_id or "")
    return make_response(data={"logged_out": True}, trace_id=request_id, request_id=request_id)


@router.post(
    "/logout-all",
    response_model=StandardResponse[dict],
    summary="Logout from all sessions (all devices)",
    operation_id="auth_logout_all",
)
async def logout_all(
    request: Request,
    principal: Principal = Depends(get_current_principal),
    svc: AuthService = Depends(_get_svc),
) -> StandardResponse[dict]:
    """Revoke all active sessions for the current user."""
    request_id = getattr(request.state, "request_id", "")
    count = await svc.logout_all(principal.user_id or "")
    return make_response(
        data={"sessions_revoked": count},
        trace_id=request_id,
        request_id=request_id,
    )


@router.get(
    "/me",
    response_model=StandardResponse[UserResponse],
    summary="Get current user profile",
    operation_id="auth_me",
)
async def get_me(
    request: Request,
    principal: Principal = Depends(get_current_principal),
    svc: AuthService = Depends(_get_svc),
) -> StandardResponse[UserResponse]:
    """Return the authenticated user's profile and permission set."""
    request_id = getattr(request.state, "request_id", "")
    user_resp = await svc.get_me(principal.user_id or "")
    return make_response(data=user_resp, trace_id=request_id, request_id=request_id)

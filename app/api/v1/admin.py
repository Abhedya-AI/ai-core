"""
app/api/v1/admin.py — Administration Endpoints.

System administration: user management, role management, audit log access.
All routes require SYSTEM_ADMIN role or specific admin.* permissions.

Endpoints:
  GET  /admin/users                   — List all users
  POST /admin/users                   — Create a new user
  GET  /admin/users/{user_id}         — Get user details
  PUT  /admin/users/{user_id}/roles   — Update user roles
  GET  /admin/audit                   — Get auth audit log
  POST /admin/api-keys                — Create API key
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.api.responses import PaginatedResponse, PaginationMeta, ResponseMetadata, StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.auth.schemas import (
    ApiKeyResponse,
    CreateApiKeyRequest,
    CreateUserRequest,
    UpdateRolesRequest,
    UserResponse,
)
from app.modules.auth.service import AuthService, get_auth_service_instance
from app.modules.auth.store import InMemoryAuthStore

router = APIRouter(prefix="/admin", tags=["Administration"])


def _get_svc() -> AuthService:
    return get_auth_service_instance()


def _get_store() -> InMemoryAuthStore:
    return InMemoryAuthStore.get_instance()


@router.get(
    "/users",
    response_model=PaginatedResponse[UserResponse],
    summary="List all users",
    operation_id="admin_list_users",
)
async def list_users(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    principal: Principal = Depends(require_permission(Permission.ADMIN_USERS_READ)),
    svc: AuthService = Depends(_get_svc),
) -> PaginatedResponse[UserResponse]:
    """Return all registered users (admin only)."""
    request_id = getattr(request.state, "request_id", "")
    users = await svc.list_users()
    paginated = users[:limit]
    return PaginatedResponse(
        data=paginated,
        pagination=PaginationMeta(
            total=len(users),
            page=1,
            page_size=limit,
            has_next=len(users) > limit,
            has_prev=False,
        ),
        metadata=ResponseMetadata(trace_id=request_id, request_id=request_id),
    )


@router.post(
    "/users",
    response_model=StandardResponse[UserResponse],
    status_code=201,
    summary="Create a new user",
    operation_id="admin_create_user",
)
async def create_user(
    body: CreateUserRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ADMIN_USERS_WRITE)),
    svc: AuthService = Depends(_get_svc),
) -> StandardResponse[UserResponse]:
    """Create a new user account with specified roles (admin only)."""
    request_id = getattr(request.state, "request_id", "")
    user = await svc.create_user(body)
    return make_response(data=user, trace_id=request_id, request_id=request_id)


@router.put(
    "/users/{user_id}/roles",
    response_model=StandardResponse[dict],
    summary="Update user roles",
    operation_id="admin_update_user_roles",
)
async def update_user_roles(
    user_id: str,
    body: UpdateRolesRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ADMIN_ROLES_WRITE)),
    store: InMemoryAuthStore = Depends(_get_store),
) -> StandardResponse[dict]:
    """Update the roles assigned to a user (admin only)."""
    from app.api.exceptions import NotFoundError
    request_id = getattr(request.state, "request_id", "")
    user = store.get_user_by_id(user_id)
    if not user:
        raise NotFoundError(message=f"User '{user_id}' not found.")
    updated = user.model_copy(update={"roles": body.roles})
    store.save_user(updated)
    return make_response(
        data={"user_id": user_id, "roles": body.roles},
        trace_id=request_id,
        request_id=request_id,
    )


@router.get(
    "/audit",
    response_model=PaginatedResponse[dict],
    summary="Get auth audit log",
    operation_id="admin_audit_log",
)
async def get_audit_log(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    principal: Principal = Depends(require_permission(Permission.ADMIN_AUDIT_READ)),
    store: InMemoryAuthStore = Depends(_get_store),
) -> PaginatedResponse[dict]:
    """Return recent auth audit log entries (admin/auditor only)."""
    request_id = getattr(request.state, "request_id", "")
    entries = store.list_audit_entries(limit=limit)
    data = [
        {
            "entry_id": e.entry_id,
            "timestamp": e.timestamp.isoformat(),
            "actor_id": e.actor_id,
            "actor_type": e.actor_type.value,
            "action": e.action,
            "result": e.result,
            "ip_address": e.ip_address,
        }
        for e in entries
    ]
    return PaginatedResponse(
        data=data,
        pagination=PaginationMeta(
            total=len(data),
            page=1,
            page_size=limit,
            has_next=False,
            has_prev=False,
        ),
        metadata=ResponseMetadata(trace_id=request_id, request_id=request_id),
    )


@router.post(
    "/api-keys",
    response_model=StandardResponse[ApiKeyResponse],
    status_code=201,
    summary="Create a new API key",
    operation_id="admin_create_api_key",
)
async def create_api_key(
    body: CreateApiKeyRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.ADMIN_SETTINGS)),
    svc: AuthService = Depends(_get_svc),
) -> StandardResponse[ApiKeyResponse]:
    """Generate a new API key for integrations. The raw key is shown only once."""
    request_id = getattr(request.state, "request_id", "")
    api_key = await svc.create_api_key(body, owner_id=principal.user_id or "admin")
    return make_response(data=api_key, trace_id=request_id, request_id=request_id)

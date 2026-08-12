"""
app/modules/auth/dependencies.py — FastAPI Auth Dependencies.

Usage in route handlers::

    from app.modules.auth.dependencies import require_permission, get_current_principal

    @router.post("/incidents")
    async def create_incident(
        body: CreateIncidentRequest,
        principal: Principal = Depends(require_permission(Permission.INCIDENT_CREATE)),
    ):
        ...

The `require_permission` factory returns a FastAPI dependency function that:
  1. Resolves the Principal from the request (JWT / API key)
  2. Checks the required permission
  3. Raises PermissionDeniedError or AuthenticationError if not satisfied
  4. Returns the Principal on success
"""

from __future__ import annotations

from fastapi import Depends, Request

from app.api.exceptions import AuthenticationError, PermissionDeniedError
from app.modules.auth.authentication import get_auth_service, AuthenticationService
from app.modules.auth.models import Principal, PrincipalType
from app.modules.auth.permissions import Permission


async def _resolve_principal(
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> Principal | None:
    """
    FastAPI dependency: resolves Principal from request headers.
    Returns None for anonymous callers.
    """
    principal = await auth_service.resolve_principal(request)
    if principal:
        request.state.principal = principal
        request.state.principal_id = principal.user_id or principal.principal_id
        request.state.principal_type = principal.principal_type.value
    return principal


def get_current_principal(
    principal: Principal | None = Depends(_resolve_principal),
) -> Principal:
    """
    FastAPI dependency: returns Principal or raises AuthenticationError.
    Use this when any authenticated identity is required (any role).
    """
    if principal is None:
        raise AuthenticationError()
    return principal


def require_permission(permission: Permission):
    """
    Factory that returns a FastAPI dependency enforcing a specific permission.

    Args:
        permission: The Permission code the caller must possess.

    Returns:
        A FastAPI dependency function returning the Principal on success.

    Example::

        @router.post("/risk/analyze")
        async def analyze(p: Principal = Depends(require_permission(Permission.RISK_RUN))):
            ...
    """

    async def _dependency(
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if not principal.has_permission(permission):
            raise PermissionDeniedError(
                message=f"Permission '{permission.value}' is required for this action.",
                details={"required": permission.value, "user_roles": principal.roles},
            )
        return principal

    return _dependency


def require_any_permission(*permissions: Permission):
    """
    Factory: caller must have at least one of the given permissions.
    """

    async def _dependency(
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if not principal.has_any_permission(*permissions):
            required = [p.value for p in permissions]
            raise PermissionDeniedError(
                message=f"One of these permissions is required: {required}",
                details={"required_any": required, "user_roles": principal.roles},
            )
        return principal

    return _dependency


def require_role(role: str):
    """
    Factory: caller must have a specific role.
    Use `require_permission` whenever possible — prefer permissions over roles
    to keep business code decoupled from role names.
    """

    async def _dependency(
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if role not in principal.roles:
            raise PermissionDeniedError(
                message=f"Role '{role}' is required for this action.",
            )
        return principal

    return _dependency

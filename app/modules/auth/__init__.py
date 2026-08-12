"""
app/modules/auth/__init__.py — Auth module public interface.
"""

from app.modules.auth.models import Principal, PrincipalType, User, Session, ApiKey
from app.modules.auth.permissions import Permission, ROLE_PERMISSIONS, get_permissions_for_roles
from app.modules.auth.dependencies import (
    get_current_principal,
    require_permission,
    require_any_permission,
    require_role,
)
from app.modules.auth.service import AuthService, get_auth_service_instance
from app.modules.auth.store import InMemoryAuthStore

__all__ = [
    "Principal",
    "PrincipalType",
    "User",
    "Session",
    "ApiKey",
    "Permission",
    "ROLE_PERMISSIONS",
    "get_permissions_for_roles",
    "get_current_principal",
    "require_permission",
    "require_any_permission",
    "require_role",
    "AuthService",
    "get_auth_service_instance",
    "InMemoryAuthStore",
]

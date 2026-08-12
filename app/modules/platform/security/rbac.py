from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from app.core.logging import get_logger

log = get_logger(__name__)

ROLE_HIERARCHY: dict[str, list[str]] = {
    "SUPER_ADMIN": ["ORG_ADMIN", "PLANT_ADMIN", "ENGINEER", "OPERATOR", "VIEWER"],
    "ORG_ADMIN": ["PLANT_ADMIN", "ENGINEER", "OPERATOR", "VIEWER"],
    "PLANT_ADMIN": ["ENGINEER", "OPERATOR", "VIEWER"],
    "ENGINEER": ["OPERATOR", "VIEWER"],
    "OPERATOR": ["VIEWER"],
    "VIEWER": [],
}

PERMISSION_MATRIX: dict[str, set[str]] = {
    "SUPER_ADMIN": {"platform:*", "model:*", "feature:*", "tenant:*", "plant:*", "governance:*", "admin:*", "security:*"},
    "ORG_ADMIN": {"platform:read", "model:read", "model:write", "model:promote", "feature:*", "tenant:read", "plant:*", "governance:read", "governance:write"},
    "PLANT_ADMIN": {"platform:read", "model:read", "model:write", "feature:read", "feature:write", "plant:read", "plant:write", "governance:read"},
    "ENGINEER": {"platform:read", "model:read", "model:write", "feature:read", "feature:write", "plant:read"},
    "OPERATOR": {"platform:read", "model:read", "feature:read", "plant:read"},
    "VIEWER": {"platform:read", "model:read", "plant:read"},
}

class RBACManager:
    def __init__(self) -> None:
        pass

    def has_permission(self, role: str, action: str, resource: str) -> bool:
        start_time = time.perf_counter()
        try:
            effective_perms = self.get_effective_permissions(role)
            target = f"{resource}:{action}"
            wildcard = f"{resource}:*"
            platform_wildcard = "platform:*"
            return target in effective_perms or wildcard in effective_perms or platform_wildcard in effective_perms
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"has_permission checked role={role} action={action} resource={resource} in {latency:.4f}s")

    def get_effective_permissions(self, role: str) -> set[str]:
        start_time = time.perf_counter()
        try:
            perms = set(PERMISSION_MATRIX.get(role, []))
            for child_role in ROLE_HIERARCHY.get(role, []):
                perms.update(PERMISSION_MATRIX.get(child_role, []))
            return perms
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_effective_permissions computed for role={role} in {latency:.4f}s")

    def get_role_level(self, role: str) -> int:
        levels = {
            "SUPER_ADMIN": 6,
            "ORG_ADMIN": 5,
            "PLANT_ADMIN": 4,
            "ENGINEER": 3,
            "OPERATOR": 2,
            "VIEWER": 1
        }
        return levels.get(role, 0)

    def can_manage(self, manager_role: str, target_role: str) -> bool:
        return self.get_role_level(manager_role) > self.get_role_level(target_role)

    async def validate_access(self, user_roles: list[str], required_permission: str, context: dict = {}) -> dict:
        start_time = time.perf_counter()
        try:
            if ":" not in required_permission:
                return {"allowed": False, "matched_role": None, "permission": required_permission, "reason": "Invalid permission format"}
            
            resource, action = required_permission.split(":", 1)
            
            for role in user_roles:
                if self.has_permission(role, action, resource):
                    return {
                        "allowed": True,
                        "matched_role": role,
                        "permission": required_permission,
                        "reason": f"Access granted via role {role}"
                    }
            return {
                "allowed": False,
                "matched_role": None,
                "permission": required_permission,
                "reason": "No roles have the required permission"
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"validate_access evaluated in {latency:.4f}s")

    async def list_role_permissions(self, role: str) -> dict:
        start_time = time.perf_counter()
        try:
            direct_perms = list(PERMISSION_MATRIX.get(role, set()))
            inherited_roles = ROLE_HIERARCHY.get(role, [])
            effective = list(self.get_effective_permissions(role))
            return {
                "role": role,
                "permissions": direct_perms,
                "inherited_from": inherited_roles,
                "effective_permissions": effective
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"list_role_permissions completed in {latency:.4f}s")

    async def assign_role(self, user_id: str, role: str, assigned_by: str, tenant_id: str) -> dict:
        start_time = time.perf_counter()
        try:
            record_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()
            log.info(f"Role {role} assigned to {user_id} by {assigned_by}")
            return {
                "assignment_id": record_id,
                "user_id": user_id,
                "role": role,
                "assigned_by": assigned_by,
                "tenant_id": tenant_id,
                "assigned_at": timestamp
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"assign_role executed in {latency:.4f}s")

_service_instance = None
def get_service() -> RBACManager:
    global _service_instance
    if _service_instance is None:
        _service_instance = RBACManager()
    return _service_instance

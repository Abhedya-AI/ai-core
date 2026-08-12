from __future__ import annotations

import contextvars
from typing import Any

from app.core.logging import get_logger

log = get_logger(__name__)

_tenant_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("tenant_id", default="")
_plant_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("plant_id", default="")
_user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")
_roles_var: contextvars.ContextVar[list[str]] = contextvars.ContextVar("roles", default=[])

class TenantContext:
    @staticmethod
    def set_context(tenant_id: str, plant_id: str, user_id: str, roles: list[str]) -> None:
        _tenant_id_var.set(tenant_id)
        _plant_id_var.set(plant_id)
        _user_id_var.set(user_id)
        _roles_var.set(roles)

    @staticmethod
    def get_tenant_id() -> str:
        return _tenant_id_var.get()

    @staticmethod
    def get_plant_id() -> str:
        return _plant_id_var.get()

    @staticmethod
    def get_user_id() -> str:
        return _user_id_var.get()

    @staticmethod
    def get_roles() -> list[str]:
        return _roles_var.get()

    @staticmethod
    def get_context() -> dict:
        return {
            "tenant_id": _tenant_id_var.get(),
            "plant_id": _plant_id_var.get(),
            "user_id": _user_id_var.get(),
            "roles": _roles_var.get()
        }

    @staticmethod
    def clear() -> None:
        _tenant_id_var.set("")
        _plant_id_var.set("")
        _user_id_var.set("")
        _roles_var.set([])

class TenantMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        
        tenant_id = headers.get(b"x-tenant-id", b"").decode()
        plant_id = headers.get(b"x-plant-id", b"").decode()
        
        user_id = ""
        roles = []
        
        auth_header = headers.get(b"authorization", b"").decode()
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                from app.modules.platform.security.jwt_rotation import get_service
                jwt_manager = get_service()
                # Fast inline decode attempt
                payload = await jwt_manager.verify_token(token)
                if payload:
                    user_id = payload.get("sub", "")
                    roles = payload.get("roles", [])
                    # Overwrite tenant if present in token
                    if "tenant_id" in payload and payload["tenant_id"]:
                        tenant_id = payload["tenant_id"]
                    if "plant_id" in payload and payload["plant_id"]:
                        plant_id = payload["plant_id"]
            except Exception as e:
                log.debug(f"Failed to parse JWT in middleware: {e}")

        TenantContext.set_context(
            tenant_id=tenant_id,
            plant_id=plant_id,
            user_id=user_id,
            roles=roles
        )

        try:
            await self.app(scope, receive, send)
        finally:
            TenantContext.clear()

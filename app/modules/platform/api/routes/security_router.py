from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Any
from app.core.logging import get_logger
import time
log = get_logger(__name__)

try:
    from app.api.responses import StandardResponse, make_response
except ImportError:
    from typing import Generic, TypeVar
    from pydantic import BaseModel
    T = TypeVar('T')
    class StandardResponse(BaseModel, Generic[T]):
        success: bool = True
        data: T | None = None
        error: dict | None = None
    def make_response(data: Any = None) -> StandardResponse:
        return StandardResponse(data=data)

try:
    from app.modules.auth.dependencies import require_permission
    from app.modules.auth.models import Principal
except ImportError:
    class Principal:
        pass
    def require_permission(perm: str):
        def _dep(): return Principal()
        return _dep

from app.modules.platform.api.dependencies import PlatformServiceDep

router = APIRouter(prefix="/platform/security", tags=["Platform - Security"])

@router.post("/api-keys")
async def create_api_key(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("security:write")),
    tenant_id: str = "default"
):
    start = time.perf_counter()
    try:
        result = await service.create_api_key(request=request, tenant_id=tenant_id)
        log.info(f"Created API key in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/api-keys")
async def list_api_keys(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("security:read")),
    tenant_id: str = "default"
):
    start = time.perf_counter()
    try:
        result = await service.list_api_keys(tenant_id=tenant_id)
        log.info(f"Listed API keys in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("security:write")),
    revoked_by: str = "admin"
):
    start = time.perf_counter()
    try:
        result = await service.revoke_api_key(key_id=key_id, revoked_by=revoked_by)
        log.info(f"Revoked API key in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/rbac/roles")
async def list_rbac_roles(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("security:read"))
):
    start = time.perf_counter()
    try:
        result = await service.list_rbac_roles()
        log.info(f"Listed RBAC roles in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/rbac/roles/{role}/permissions")
async def get_role_permissions(
    role: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("security:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_role_permissions(role=role)
        log.info(f"Got role permissions in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/abac/policies")
async def add_abac_policy(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("security:write"))
):
    start = time.perf_counter()
    try:
        result = await service.add_abac_policy(request=request)
        log.info(f"Added ABAC policy in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/abac/policies")
async def list_abac_policies(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("security:read"))
):
    start = time.perf_counter()
    try:
        result = await service.list_abac_policies()
        log.info(f"Listed ABAC policies in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/rate-limits")
async def get_rate_limit_status(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("security:read")),
    tenant_id: str = "default"
):
    start = time.perf_counter()
    try:
        result = await service.get_rate_limit_status(tenant_id=tenant_id)
        log.info(f"Got rate limit status in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

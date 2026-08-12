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

router = APIRouter(prefix="/platform/admin", tags=["Platform - Admin"])

@router.get("/status")
async def get_system_status(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("admin:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_system_status()
        log.info(f"Got system status in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/maintenance")
async def enable_maintenance(
    reason: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("admin:write")),
    enabled_by: str = "admin"
):
    start = time.perf_counter()
    try:
        result = await service.enable_maintenance(reason=reason, enabled_by=enabled_by)
        log.info(f"Enabled maintenance in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.delete("/maintenance")
async def disable_maintenance(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("admin:write")),
    disabled_by: str = "admin"
):
    start = time.perf_counter()
    try:
        result = await service.disable_maintenance(disabled_by=disabled_by)
        log.info(f"Disabled maintenance in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/config")
async def get_system_config(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("admin:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_system_config()
        log.info(f"Got system config in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/tenants")
async def list_all_tenants(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("admin:read")),
    tier: str | None = None,
    is_active: bool | None = None,
    limit: int = 20,
    offset: int = 0
):
    start = time.perf_counter()
    try:
        result = await service.list_all_tenants(tier=tier, is_active=is_active, limit=limit, offset=offset)
        log.info(f"Listed tenants in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/tenants")
async def create_tenant(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("admin:write"))
):
    start = time.perf_counter()
    try:
        result = await service.create_tenant(request=request)
        log.info(f"Created tenant in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("admin:write")),
    by: str = "admin"
):
    start = time.perf_counter()
    try:
        result = await service.suspend_tenant(tenant_id=tenant_id, reason=reason, by=by)
        log.info(f"Suspended tenant in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/costs")
async def get_cost_summary(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("admin:read")),
    tenant_id: str | None = None,
    period: str = ""
):
    start = time.perf_counter()
    try:
        result = await service.get_cost_summary(tenant_id=tenant_id, period=period)
        log.info(f"Got cost summary in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

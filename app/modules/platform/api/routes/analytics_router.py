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

router = APIRouter(prefix="/platform/analytics", tags=["Platform - Analytics"])

@router.get("/")
async def get_platform_analytics(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("analytics:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_platform_analytics()
        log.info(f"Got platform analytics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/models")
async def get_model_analytics(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("analytics:read")),
    module: str | None = None,
    days: int = 30
):
    start = time.perf_counter()
    try:
        result = await service.get_model_analytics(module=module, days=days)
        log.info(f"Got model analytics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/features")
async def get_feature_analytics(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("analytics:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_feature_analytics()
        log.info(f"Got feature analytics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/tenants/{tenant_id}")
async def get_tenant_analytics(
    tenant_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("analytics:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_tenant_analytics(tenant_id=tenant_id)
        log.info(f"Got tenant analytics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/executive")
async def get_executive_summary(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("analytics:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_executive_summary()
        log.info(f"Got executive summary in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/export")
async def export_analytics(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("analytics:read")),
    format: str = "json",
    tenant_id: str | None = None
):
    start = time.perf_counter()
    try:
        result = await service.export_analytics(format=format, tenant_id=tenant_id)
        log.info(f"Exported analytics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

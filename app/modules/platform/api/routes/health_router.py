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

router = APIRouter(prefix="/platform/health", tags=["Platform - Health"])

@router.get("/")
async def get_platform_health(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("health:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_platform_health()
        log.info(f"Got platform health in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/components")
async def get_component_health(
    component: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("health:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_component_health(component=component)
        log.info(f"Got component health in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/ready")
async def readiness_check(
    service: PlatformServiceDep
):
    start = time.perf_counter()
    try:
        result = await service.readiness_check()
        log.info(f"Readiness check in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/live")
async def liveness_check(
    service: PlatformServiceDep
):
    start = time.perf_counter()
    try:
        result = await service.liveness_check()
        log.info(f"Liveness check in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

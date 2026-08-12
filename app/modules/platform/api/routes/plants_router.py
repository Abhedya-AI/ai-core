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

router = APIRouter(prefix="/platform/plants", tags=["Platform - Plants"])

@router.get("/")
async def list_plants(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("plant:read")),
    tenant_id: str = "default",
    status: str | None = None,
    limit: int = 20,
    offset: int = 0
):
    start = time.perf_counter()
    try:
        result = await service.list_plants(tenant_id=tenant_id, status=status, limit=limit, offset=offset)
        log.info(f"Listed plants in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/")
async def register_plant(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("plant:write"))
):
    start = time.perf_counter()
    try:
        result = await service.register_plant(request=request)
        log.info(f"Registered plant in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/{plant_id}")
async def get_plant(
    plant_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("plant:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_plant(plant_id=plant_id)
        log.info(f"Got plant in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/fleet/health")
async def get_fleet_health(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("plant:read")),
    tenant_id: str = "default"
):
    start = time.perf_counter()
    try:
        result = await service.get_fleet_health(tenant_id=tenant_id)
        log.info(f"Got fleet health in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/fleet/analytics")
async def get_fleet_analytics(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("plant:read")),
    tenant_id: str = "default"
):
    start = time.perf_counter()
    try:
        result = await service.get_fleet_analytics(tenant_id=tenant_id)
        log.info(f"Got fleet analytics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/fleet/benchmarks")
async def get_fleet_benchmarks(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("plant:read")),
    tenant_id: str = "default"
):
    start = time.perf_counter()
    try:
        result = await service.get_fleet_benchmarks(tenant_id=tenant_id)
        log.info(f"Got fleet benchmarks in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.put("/{plant_id}/metrics")
async def update_plant_metrics(
    plant_id: str,
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("plant:write"))
):
    start = time.perf_counter()
    try:
        result = await service.update_plant_metrics(plant_id=plant_id, request=request)
        log.info(f"Updated plant metrics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.delete("/{plant_id}")
async def deregister_plant(
    plant_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("plant:write"))
):
    start = time.perf_counter()
    try:
        result = await service.deregister_plant(plant_id=plant_id)
        log.info(f"Deregistered plant in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

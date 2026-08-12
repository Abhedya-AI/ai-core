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

router = APIRouter(prefix="/platform/organizations", tags=["Platform - Organizations"])

@router.get("/")
async def list_organizations(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("organization:read")),
    tenant_id: str = "default",
    limit: int = 20,
    offset: int = 0
):
    start = time.perf_counter()
    try:
        result = await service.list_organizations(tenant_id=tenant_id, limit=limit, offset=offset)
        log.info(f"Listed organizations in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/")
async def create_organization(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("organization:write"))
):
    start = time.perf_counter()
    try:
        result = await service.create_organization(request=request)
        log.info(f"Created organization in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/{org_id}")
async def get_organization(
    org_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("organization:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_organization(org_id=org_id)
        log.info(f"Got organization in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.put("/{org_id}")
async def update_organization(
    org_id: str,
    updates: dict,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("organization:write"))
):
    start = time.perf_counter()
    try:
        result = await service.update_organization(org_id=org_id, updates=updates)
        log.info(f"Updated organization in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/{org_id}/members")
async def list_members(
    org_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("organization:read"))
):
    start = time.perf_counter()
    try:
        result = await service.list_members(org_id=org_id)
        log.info(f"Listed members in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/{org_id}/members/{user_id}")
async def add_member(
    org_id: str,
    user_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("organization:write"))
):
    start = time.perf_counter()
    try:
        result = await service.add_member(org_id=org_id, user_id=user_id)
        log.info(f"Added member in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

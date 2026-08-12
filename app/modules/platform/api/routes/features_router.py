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
from app.modules.platform.api.schemas import (
    CreateFeatureRequest, ServeFeatureRequest, MaterializeFeatureRequest
)

router = APIRouter(prefix="/platform/features", tags=["Platform - Features"])

@router.get("/")
async def list_features(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("feature:read")),
    entity_type: str | None = Query(None),
    source_module: str | None = Query(None),
    limit: int = 20,
    offset: int = 0
):
    start = time.perf_counter()
    try:
        result = await service.list_features(entity_type=entity_type, source_module=source_module, limit=limit, offset=offset)
        log.info(f"Listed features in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/")
async def register_feature(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("feature:write"))
):
    start = time.perf_counter()
    try:
        result = await service.register_feature(request=request)
        log.info(f"Registered feature in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/{feature_id}")
async def get_feature(
    feature_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("feature:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_feature(feature_id=feature_id)
        log.info(f"Fetched feature in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/serve")
async def serve_feature(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("feature:read"))
):
    start = time.perf_counter()
    try:
        result = await service.serve_feature(request=request)
        log.info(f"Served feature in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/materialize")
async def materialize_feature(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("feature:write"))
):
    start = time.perf_counter()
    try:
        result = await service.materialize_feature(request=request)
        log.info(f"Materialized feature in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/{feature_id}/validate")
async def validate_feature(
    feature_id: str,
    value: dict,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("feature:read"))
):
    start = time.perf_counter()
    try:
        result = await service.validate_feature(feature_id=feature_id, value=value)
        log.info(f"Validated feature in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/{feature_id}/statistics")
async def get_feature_statistics(
    feature_id: str,
    entity_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("feature:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_feature_statistics(feature_id=feature_id, entity_id=entity_id)
        log.info(f"Got feature statistics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/{feature_id}/lineage")
async def get_feature_lineage(
    feature_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("feature:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_feature_lineage(feature_id=feature_id)
        log.info(f"Got feature lineage in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

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
    RegisterModelRequest, PromoteModelRequest, SubmitForReviewRequest,
    ApproveModelRequest, RejectModelRequest
)

router = APIRouter(prefix="/platform/models", tags=["Platform - Models"])

@router.get("/")
async def list_models(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("model:read")),
    module: str | None = Query(None),
    stage: str | None = Query(None),
    limit: int = 20,
    offset: int = 0
):
    start = time.perf_counter()
    try:
        result = await service.list_models(module=module, stage=stage, limit=limit, offset=offset)
        log.info(f"Listed models in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/")
async def register_model(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("model:write")),
    tenant_id: str = "default"
):
    start = time.perf_counter()
    try:
        result = await service.register_model(request, tenant_id=tenant_id)
        log.info(f"Registered model in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/{model_id}")
async def get_model(
    model_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("model:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_model(model_id=model_id)
        log.info(f"Fetched model in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/{model_id}/promote")
async def promote_model(
    model_id: str,
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("model:write"))
):
    start = time.perf_counter()
    try:
        result = await service.promote_model(model_id=model_id, request=request)
        log.info(f"Promoted model in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/{model_id}/review")
async def submit_for_review(
    model_id: str,
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("model:write"))
):
    start = time.perf_counter()
    try:
        result = await service.approve_model_workflow(model_id=model_id, request=request)
        log.info(f"Submitted for review in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/{model_id}/approve")
async def approve_model(
    model_id: str,
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("model:write"))
):
    start = time.perf_counter()
    try:
        result = await service.approve_model(model_id=model_id, request=request)
        log.info(f"Approved model in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/{model_id}/reject")
async def reject_model(
    model_id: str,
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("model:write"))
):
    start = time.perf_counter()
    try:
        result = await service.reject_model(model_id=model_id, request=request)
        log.info(f"Rejected model in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/{model_id}/lineage")
async def get_model_lineage(
    model_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("model:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_model_lineage(model_id=model_id)
        log.info(f"Got model lineage in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/{model_id}/metrics")
async def get_model_metrics(
    model_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("model:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_model_metrics(model_id=model_id)
        log.info(f"Got model metrics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/compare")
async def compare_models(
    model_id_a: str,
    model_id_b: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("model:read"))
):
    start = time.perf_counter()
    try:
        result = await service.compare_models(model_id_a=model_id_a, model_id_b=model_id_b)
        log.info(f"Compared models in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

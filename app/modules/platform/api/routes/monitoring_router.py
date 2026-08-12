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
from app.modules.platform.api.schemas import RunDriftCheckRequest, SubmitFeedbackRequest

router = APIRouter(prefix="/platform/monitoring", tags=["Platform - Monitoring"])

@router.get("/drift")
async def get_drift_status(
    model_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("monitoring:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_drift_status(model_id=model_id)
        log.info(f"Got drift status in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/drift/check")
async def run_drift_check(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("monitoring:write"))
):
    start = time.perf_counter()
    try:
        result = await service.run_drift_check(request=request)
        log.info(f"Ran drift check in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/drift/history")
async def get_drift_history(
    model_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("monitoring:read")),
    limit: int = 20
):
    start = time.perf_counter()
    try:
        result = await service.get_drift_history(model_id=model_id, limit=limit)
        log.info(f"Got drift history in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/drift/features")
async def get_feature_drift(
    model_id: str,
    feature_name: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("monitoring:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_feature_drift(model_id=model_id, feature_name=feature_name)
        log.info(f"Got feature drift in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/metrics")
async def get_performance_metrics(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("monitoring:read")),
    module: str | None = None,
    window_minutes: int = 60
):
    start = time.perf_counter()
    try:
        result = await service.get_performance_metrics(module=module, window_minutes=window_minutes)
        log.info(f"Got performance metrics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/metrics/ai-pipeline")
async def get_ai_pipeline_metrics(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("monitoring:read")),
    module: str | None = None,
    window_minutes: int = 60
):
    start = time.perf_counter()
    try:
        result = await service.get_ai_pipeline_metrics(module=module, window_minutes=window_minutes)
        log.info(f"Got AI pipeline metrics in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/retraining")
async def get_retraining_jobs(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("monitoring:read")),
    model_id: str | None = None,
    limit: int = 20
):
    start = time.perf_counter()
    try:
        result = await service.get_retraining_jobs(model_id=model_id, limit=limit)
        log.info(f"Got retraining jobs in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/feedback")
async def submit_feedback(
    request: Any,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("monitoring:write"))
):
    start = time.perf_counter()
    try:
        result = await service.submit_feedback(request=request)
        log.info(f"Submitted feedback in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

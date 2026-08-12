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

router = APIRouter(prefix="/platform/governance", tags=["Platform - Governance"])

@router.get("/decisions")
async def list_governance_decisions(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("governance:read")),
    model_id: str | None = None,
    limit: int = 50,
    offset: int = 0
):
    start = time.perf_counter()
    try:
        result = await service.list_governance_decisions(model_id=model_id, limit=limit, offset=offset)
        log.info(f"Listed governance decisions in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/decisions/{decision_id}")
async def get_governance_decision(
    decision_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("governance:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_governance_decision(decision_id=decision_id)
        log.info(f"Got governance decision in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/approvals")
async def list_pending_approvals(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("governance:read")),
    tenant_id: str = "default"
):
    start = time.perf_counter()
    try:
        result = await service.list_pending_approvals(tenant_id=tenant_id)
        log.info(f"Listed pending approvals in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/policies")
async def list_policies(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("governance:read"))
):
    start = time.perf_counter()
    try:
        result = await service.list_policies()
        log.info(f"Listed policies in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/policies")
async def add_policy(
    name: str,
    policy_type: str,
    rule: dict,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("governance:write")),
    threshold: float = 0.5
):
    start = time.perf_counter()
    try:
        result = await service.add_policy(name=name, policy_type=policy_type, rule=rule, threshold=threshold)
        log.info(f"Added policy in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/reports/{model_id}")
async def get_compliance_report(
    model_id: str,
    model_version: str,
    reporting_period: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("governance:read")),
    tenant_id: str = "default"
):
    start = time.perf_counter()
    try:
        result = await service.get_compliance_report(model_id=model_id, model_version=model_version, reporting_period=reporting_period, tenant_id=tenant_id)
        log.info(f"Got compliance report in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/explainability/{model_id}")
async def get_explainability(
    model_id: str,
    prediction_id: str,
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("governance:read"))
):
    start = time.perf_counter()
    try:
        result = await service.get_explainability(model_id=model_id, prediction_id=prediction_id)
        log.info(f"Got explainability in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/audit")
async def get_governance_audit(
    service: PlatformServiceDep,
    principal: Principal = Depends(require_permission("governance:read")),
    tenant_id: str | None = None,
    action: str | None = None,
    limit: int = 100
):
    start = time.perf_counter()
    try:
        result = await service.get_governance_audit(tenant_id=tenant_id, action=action, limit=limit)
        log.info(f"Got governance audit in {time.perf_counter() - start:.4f}s")
        return make_response(data=result)
    except Exception as e:
        raise HTTPException(500, str(e))

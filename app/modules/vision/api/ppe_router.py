"""
api/ppe_router.py — PPE Compliance API Endpoints (/api/v1/ppe).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.vision.application.dto.vision_safety_dto import PPECheckRequest
from app.modules.vision.intelligence.ppe_engine import PPEComplianceEngine

router = APIRouter(prefix="/ppe", tags=["Vision Safety — PPE Compliance"])
_engine = PPEComplianceEngine()


@router.post(
    "/check",
    response_model=StandardResponse[dict[str, Any]],
    summary="Evaluate PPE compliance for a frame",
    operation_id="vision_ppe_check",
)
async def check_ppe(
    body: PPECheckRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Evaluate PPE items against zone, role, and equipment policies."""
    request_id = getattr(request.state, "request_id", "")
    score, missing, viol = _engine.evaluate(
        detected_ppe=body.detected_ppe,
        camera_id=body.camera_id,
        zone_id=body.zone_id,
        worker_id=body.worker_id,
        worker_role=body.worker_role,
        equipment_type=body.equipment_type,
    )
    data = {
        "compliance_score_pct": score,
        "missing_ppe": missing,
        "detected_ppe": body.detected_ppe,
        "violation": viol.model_dump() if viol else None,
        "status": "COMPLIANT" if not missing else "NON_COMPLIANT",
    }
    return make_response(data=data, trace_id=request_id, request_id=request_id)


@router.get(
    "/repeat-offenders",
    response_model=StandardResponse[dict[str, int]],
    summary="List repeat PPE offenders",
    operation_id="vision_ppe_repeat_offenders",
)
async def list_repeat_offenders(
    request: Request,
    threshold: int = Query(default=3, ge=1, le=10),
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, int]]:
    """Get list of worker IDs exceeding PPE violation thresholds."""
    request_id = getattr(request.state, "request_id", "")
    offenders = _engine.get_repeat_offenders(threshold=threshold)
    return make_response(data=offenders, trace_id=request_id, request_id=request_id)

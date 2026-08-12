"""
api/fall_detection_router.py — Fall Detection Endpoints (/api/v1/fall-detection).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.vision.application.dto.vision_safety_dto import FallEvaluationRequest
from app.modules.vision.intelligence.fall_detection_engine import FallDetectionEngine

router = APIRouter(prefix="/fall-detection", tags=["Vision Safety — Fall Detection"])
_engine = FallDetectionEngine()


@router.post(
    "/evaluate",
    response_model=StandardResponse[dict[str, Any]],
    summary="Evaluate pose kinematics for fall confirmation",
    operation_id="vision_evaluate_fall",
)
async def evaluate_fall(
    body: FallEvaluationRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Evaluate aspect ratio and downward velocity for fall detection."""
    request_id = getattr(request.state, "request_id", "")
    is_fall, viol, emerg = _engine.evaluate_pose_and_motion(
        worker_id=body.worker_id,
        camera_id=body.camera_id,
        zone_id=body.zone_id,
        bbox_aspect_ratio=body.bbox_aspect_ratio,
        downward_velocity=body.downward_velocity,
        is_crouching=body.is_crouching,
    )
    data = {
        "is_confirmed_fall": is_fall,
        "violation": viol.model_dump() if viol else None,
        "emergency": emerg.model_dump() if emerg else None,
    }
    return make_response(data=data, trace_id=request_id, request_id=request_id)

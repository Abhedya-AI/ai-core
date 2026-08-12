"""
api/fire_verification_router.py — Multi-Modal Fire & Smoke Verification Endpoints (/api/v1/fire-verification).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.vision.application.dto.vision_safety_dto import FireVerificationRequest
from app.modules.vision.intelligence.fire_smoke_verification import FireSmokeVerificationEngine

router = APIRouter(prefix="/fire-verification", tags=["Vision Safety — Fire & Smoke Verification"])
_engine = FireSmokeVerificationEngine()


@router.post(
    "/verify",
    response_model=StandardResponse[dict[str, Any]],
    summary="Multi-modal verification of fire or smoke detections",
    operation_id="vision_verify_fire",
)
async def verify_fire(
    body: FireVerificationRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Fuse camera visual detection with IoT telemetry and KG context."""
    request_id = getattr(request.state, "request_id", "")
    status, f_conf, viol, emerg = _engine.verify_fire_smoke(
        camera_id=body.camera_id,
        zone_id=body.zone_id,
        visual_type=body.visual_type,
        camera_confidence=body.camera_confidence,
        sensor_smoke_detected=body.sensor_smoke_detected,
        sensor_temp_celsius=body.sensor_temp_celsius,
        sensor_gas_ppm=body.sensor_gas_ppm,
    )
    data = {
        "verification_status": status,
        "fused_confidence": f_conf,
        "violation": viol.model_dump() if viol else None,
        "emergency": emerg.model_dump() if emerg else None,
    }
    return make_response(data=data, trace_id=request_id, request_id=request_id)

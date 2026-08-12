"""
api/restricted_zones_router.py — Restricted Zone API Endpoints (/api/v1/restricted-zones).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.vision.application.dto.vision_safety_dto import ZoneAccessCheckRequest
from app.modules.vision.intelligence.restricted_zone_engine import RestrictedZoneEngine

router = APIRouter(prefix="/restricted-zones", tags=["Vision Safety — Restricted Zones"])
_engine = RestrictedZoneEngine()


@router.post(
    "/evaluate-access",
    response_model=StandardResponse[dict[str, Any]],
    summary="Evaluate worker access against polygon zone boundary",
    operation_id="vision_evaluate_zone_access",
)
async def evaluate_zone_access(
    body: ZoneAccessCheckRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Evaluate worker position against polygon boundary & role permissions."""
    request_id = getattr(request.state, "request_id", "")
    is_inside, status, viol = _engine.evaluate_zone_access(
        worker_id=body.worker_id,
        worker_role=body.worker_role,
        camera_id=body.camera_id,
        zone_id=body.zone_id,
        worker_x=body.worker_x,
        worker_y=body.worker_y,
        zone_polygon=body.polygon,
        allowed_roles=body.allowed_roles,
        dwell_time_seconds=body.dwell_time_seconds,
    )
    data = {
        "is_inside_zone": is_inside,
        "access_status": status,
        "violation": viol.model_dump() if viol else None,
    }
    return make_response(data=data, trace_id=request_id, request_id=request_id)

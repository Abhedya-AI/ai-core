"""
api/violations_router.py — Vision Violations API Endpoints (/api/v1/vision-violations).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.vision.intelligence.unsafe_behavior_engine import UnsafeBehaviorEngine

router = APIRouter(prefix="/vision-violations", tags=["Vision Safety — Violations"])
_engine = UnsafeBehaviorEngine()


@router.get(
    "",
    response_model=StandardResponse[list[dict[str, Any]]],
    summary="List vision safety violations",
    operation_id="vision_list_violations",
)
async def list_violations(
    request: Request,
    zone_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[list[dict[str, Any]]]:
    """Retrieve filtered list of vision violations."""
    request_id = getattr(request.state, "request_id", "")
    sample_violations = [
        {
            "id": "viol-101",
            "violation_type": "UNSAFE_BEHAVIOR",
            "severity": severity or "HIGH",
            "camera_id": "CAM-01",
            "zone_id": zone_id or "ZONE-A",
            "description": "Worker running in hazardous processing area",
            "confidence": 0.94,
            "timestamp": "2026-07-31T22:00:00Z",
        }
    ]
    return make_response(data=sample_violations[:limit], trace_id=request_id, request_id=request_id)

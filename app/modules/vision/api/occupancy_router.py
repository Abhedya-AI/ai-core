"""
api/occupancy_router.py — Zone Occupancy & Density Endpoints (/api/v1/occupancy).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.vision.intelligence.occupancy_engine import OccupancyEngine

router = APIRouter(prefix="/occupancy", tags=["Vision Safety — Occupancy"])
_engine = OccupancyEngine()


@router.get(
    "/{zone_id}",
    response_model=StandardResponse[dict[str, Any]],
    summary="Get real-time zone occupancy & density",
    operation_id="vision_get_occupancy",
)
async def get_zone_occupancy(
    zone_id: str,
    request: Request,
    worker_count: int = Query(default=12, ge=0),
    capacity_limit: int = Query(default=50, ge=1),
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Get zone worker count, density ratio, and capacity excess status."""
    request_id = getattr(request.state, "request_id", "")
    occupancy = _engine.evaluate_occupancy(
        zone_id=zone_id,
        detected_worker_count=worker_count,
        capacity_limit=capacity_limit,
    )
    return make_response(data=occupancy.model_dump(), trace_id=request_id, request_id=request_id)

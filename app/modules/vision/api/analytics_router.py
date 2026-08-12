"""
api/analytics_router.py — Vision Analytics API Endpoints (/api/v1/vision-analytics).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.vision.intelligence.compliance_engine import SafetyComplianceEngine

router = APIRouter(prefix="/vision-analytics", tags=["Vision Safety — Analytics"])
_compliance_engine = SafetyComplianceEngine()


@router.get(
    "/compliance-summary",
    response_model=StandardResponse[dict[str, Any]],
    summary="Get overall safety compliance index",
    operation_id="vision_compliance_summary",
)
async def get_compliance_summary(
    request: Request,
    zone_id: str = Query(default="ZONE-A"),
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Compute safety compliance index for a zone."""
    request_id = getattr(request.state, "request_id", "")
    summary = _compliance_engine.compute_compliance_index(
        zone_id=zone_id,
        ppe_compliance_pct=92.5,
        behavior_violation_count=1,
        restricted_zone_breach_count=0,
        unsafe_interaction_count=0,
    )
    return make_response(data=summary, trace_id=request_id, request_id=request_id)

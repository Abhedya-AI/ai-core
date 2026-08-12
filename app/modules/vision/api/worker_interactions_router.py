"""
api/worker_interactions_router.py — Worker Equipment Interaction Endpoints (/api/v1/worker-interactions).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.vision.application.dto.vision_safety_dto import InteractionCheckRequest
from app.modules.vision.intelligence.worker_equipment_engine import WorkerEquipmentEngine

router = APIRouter(prefix="/worker-interactions", tags=["Vision Safety — Worker Equipment Proximity"])
_engine = WorkerEquipmentEngine()


@router.post(
    "/evaluate",
    response_model=StandardResponse[dict[str, Any]],
    summary="Evaluate worker equipment proximity",
    operation_id="vision_evaluate_worker_interaction",
)
async def evaluate_interaction(
    body: InteractionCheckRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Calculate distance meters and check unsafe proximity thresholds."""
    request_id = getattr(request.state, "request_id", "")
    interaction = _engine.evaluate_interaction(
        worker_id=body.worker_id,
        equipment_id=body.equipment_id,
        equipment_type=body.equipment_type,
        worker_pos=body.worker_pos,
        equipment_pos=body.equipment_pos,
        camera_id=body.camera_id,
        zone_id=body.zone_id,
    )
    return make_response(data=interaction.model_dump(), trace_id=request_id, request_id=request_id)

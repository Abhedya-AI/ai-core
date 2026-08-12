"""
api/vision_ai_router.py — Unified Vision AI Endpoints (/api/v1/vision-ai).

Includes:
  - POST /api/v1/vision-ai/process — Run full Vision AI Safety Intelligence pipeline
  - POST /api/v1/vision-ai/explain — Generate rich operator-facing AI decision explanation
  - POST /api/v1/vision-ai/context — Build GraphRAG vision context package
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import Principal
from app.modules.auth.permissions import Permission
from app.modules.vision.application.dto.vision_safety_dto import VisionAIProcessRequest
from app.modules.vision.intelligence.vision_ai_service import VisionAIService

router = APIRouter(prefix="/vision-ai", tags=["Vision Safety — Intelligence Engine"])
_service = VisionAIService()


@router.post(
    "/process",
    response_model=StandardResponse[dict[str, Any]],
    summary="Process frame features through Vision AI Intelligence Engine",
    operation_id="vision_ai_process",
)
async def process_vision_ai(
    body: VisionAIProcessRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Execute unified vision safety intelligence workflow."""
    request_id = getattr(request.state, "request_id", "")
    assessment, explanation = await _service.process_vision_frame_intelligence(
        camera_id=body.camera_id,
        zone_id=body.zone_id,
        detected_ppe=body.detected_ppe,
        worker_id=body.worker_id,
        behavior_type=body.behavior_type,
        velocity=body.velocity,
        equipment_id=body.equipment_id,
        equipment_type=body.equipment_type,
        bbox_aspect_ratio=body.bbox_aspect_ratio,
        visual_hazard_type=body.visual_hazard_type,
    )
    data = {
        "assessment": assessment.model_dump(),
        "explanation": explanation.model_dump(),
    }
    return make_response(data=data, trace_id=request_id, request_id=request_id)


@router.post(
    "/explain",
    response_model=StandardResponse[dict[str, Any]],
    summary="Get rich operator-facing AI decision explanation",
    operation_id="vision_ai_explain",
)
async def explain_vision_ai(
    body: VisionAIProcessRequest,
    request: Request,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Generate detailed explainability package (reasons, evidence, KG paths, citations)."""
    request_id = getattr(request.state, "request_id", "")
    assessment, explanation = await _service.process_vision_frame_intelligence(
        camera_id=body.camera_id,
        zone_id=body.zone_id,
        detected_ppe=body.detected_ppe,
        worker_id=body.worker_id,
        behavior_type=body.behavior_type,
    )
    return make_response(data=explanation.model_dump(), trace_id=request_id, request_id=request_id)


@router.post(
    "/context",
    response_model=StandardResponse[dict[str, Any]],
    summary="Build GraphRAG vision context package",
    operation_id="vision_ai_context",
)
async def get_vision_context(
    camera_id: str = Query(...),
    zone_id: str = Query(...),
    primary_entity_id: str = Query(...),
    detection_label: str = Query(default="Worker"),
    request: Request = None,
    principal: Principal = Depends(require_permission(Permission.GRAPH_READ)),
) -> StandardResponse[dict[str, Any]]:
    """Assemble multi-hop KG context, nearby sensors, and GraphRAG prompt text."""
    request_id = getattr(request.state, "request_id", "")
    package = await _service._context_builder.build_vision_context(
        zone_id=zone_id,
        camera_id=camera_id,
        primary_entity_id=primary_entity_id,
        detection_label=detection_label,
    )
    return make_response(data=package.model_dump(), trace_id=request_id, request_id=request_id)

"""
application/use_cases/vision_safety_use_cases.py — Clean Architecture Use Cases.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.vision.application.dto.vision_safety_dto import (
    FallEvaluationRequest,
    FireVerificationRequest,
    InteractionCheckRequest,
    PPECheckRequest,
    VisionAIProcessRequest,
    ZoneAccessCheckRequest,
)
from app.modules.vision.intelligence.vision_ai_service import VisionAIService

log = get_logger("vision.use_cases")


class EvaluatePPEComplianceUseCase:
    def __init__(self, service: VisionAIService | None = None) -> None:
        self._service = service or VisionAIService()

    async def execute(self, req: PPECheckRequest) -> dict[str, Any]:
        score, missing, viol = self._service._ppe.evaluate(
            detected_ppe=req.detected_ppe,
            camera_id=req.camera_id,
            zone_id=req.zone_id,
            worker_id=req.worker_id,
            worker_role=req.worker_role,
            equipment_type=req.equipment_type,
        )
        return {
            "compliance_score_pct": score,
            "missing_ppe": missing,
            "violation": viol.model_dump() if viol else None,
            "status": "COMPLIANT" if not missing else "VIOLATION_DETECTED",
        }


class CheckRestrictedZoneAccessUseCase:
    def __init__(self, service: VisionAIService | None = None) -> None:
        self._service = service or VisionAIService()

    async def execute(self, req: ZoneAccessCheckRequest) -> dict[str, Any]:
        is_inside, status, viol = self._service._zone.evaluate_zone_access(
            worker_id=req.worker_id,
            worker_role=req.worker_role,
            camera_id=req.camera_id,
            zone_id=req.zone_id,
            worker_x=req.worker_x,
            worker_y=req.worker_y,
            zone_polygon=req.polygon,
            allowed_roles=req.allowed_roles,
            dwell_time_seconds=req.dwell_time_seconds,
        )
        return {
            "is_inside_zone": is_inside,
            "access_status": status,
            "violation": viol.model_dump() if viol else None,
        }


class ProcessVisionFrameAIUseCase:
    def __init__(self, service: VisionAIService | None = None) -> None:
        self._service = service or VisionAIService()

    async def execute(self, req: VisionAIProcessRequest) -> dict[str, Any]:
        assessment, explanation = await self._service.process_vision_frame_intelligence(
            camera_id=req.camera_id,
            zone_id=req.zone_id,
            detected_ppe=req.detected_ppe,
            worker_id=req.worker_id,
            behavior_type=req.behavior_type,
            velocity=req.velocity,
            equipment_id=req.equipment_id,
            equipment_type=req.equipment_type,
            bbox_aspect_ratio=req.bbox_aspect_ratio,
            visual_hazard_type=req.visual_hazard_type,
        )
        return {
            "assessment": assessment.model_dump(),
            "explanation": explanation.model_dump(),
        }

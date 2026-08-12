"""
vision/application/detection/ppe_compliance_service.py — PPE Compliance Service.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict
from app.core.logging import get_logger
from app.modules.vision.domain.entities.detection import Detection
from app.modules.vision.domain.entities.camera_zone import CameraZone
from app.modules.vision.domain.entities.vision_alert import VisionAlert, AlertStatus
from app.modules.vision.domain.entities.detection_event import AlertSeverity
from app.modules.vision.domain.enums.hazard_type import HazardType
from app.modules.vision.domain.enums.stream_event_type import StreamEventType

log = get_logger("vision.application.detection.ppe_compliance")

DEFAULT_PPE_REQUIREMENTS = [HazardType.HELMET, HazardType.SAFETY_VEST]

class PPEViolation(BaseModel):
    model_config = ConfigDict(frozen=True)
    hazard_type: HazardType
    person_detection_id: str
    camera_id: str
    zone_id: str | None
    confidence: float
    frame_id: str

class PPEComplianceService:
    def _violation_type_for_ppe(self, ppe_required: HazardType) -> HazardType:
        mapping = {
            HazardType.HELMET: HazardType.NO_HELMET,
            HazardType.SAFETY_VEST: HazardType.NO_SAFETY_VEST,
        }
        return mapping.get(ppe_required, HazardType.NO_HELMET)

    def _ppe_present(self, ppe_type: HazardType, detections: list[Detection]) -> bool:
        for d in detections:
            if d.hazard_type == ppe_type:
                return True
        return False

    def evaluate(self, camera_id: str, zone_id: str | None, frame_id: str, detections: list[Detection], zone: CameraZone | None = None) -> tuple[list[PPEViolation], list[VisionAlert]]:
        reqs = getattr(zone, 'ppe_requirements', None) if zone else None
        if reqs is None:
            reqs = DEFAULT_PPE_REQUIREMENTS
            
        violations = []
        alerts = []
        
        persons = [d for d in detections if d.hazard_type == HazardType.PERSON]
        
        unique_violation_types = set()
        
        for p in persons:
            for req in reqs:
                if not self._ppe_present(req, detections):
                    viol_type = self._violation_type_for_ppe(req)
                    viol = PPEViolation(
                        hazard_type=viol_type,
                        person_detection_id=p.detection_id,
                        camera_id=camera_id,
                        zone_id=zone_id,
                        confidence=p.confidence,
                        frame_id=frame_id
                    )
                    violations.append(viol)
                    unique_violation_types.add(viol_type)
        
        for vt in unique_violation_types:
            alert = VisionAlert(
                alert_id=str(uuid.uuid4()),
                alert_type=vt.value if hasattr(vt, 'value') else str(vt),
                severity=AlertSeverity.HIGH,
                status=AlertStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                camera_id=camera_id,
                zone_id=zone_id,
                description=f"PPE Violation: missing {vt}",
                detection_ids=[v.person_detection_id for v in violations if v.hazard_type == vt]
            )
            alerts.append(alert)
            
        return violations, alerts

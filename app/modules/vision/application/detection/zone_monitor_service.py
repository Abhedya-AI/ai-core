"""
vision/application/detection/zone_monitor_service.py — Zone Monitor Service.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict
from app.core.logging import get_logger
from app.modules.vision.domain.entities.detection import Detection
from app.modules.vision.domain.entities.camera_zone import CameraZone
from app.modules.vision.domain.entities.vision_alert import VisionAlert, AlertStatus
from app.modules.vision.domain.entities.detection_event import AlertSeverity
from app.modules.vision.domain.enums.hazard_type import HazardType
from app.modules.vision.domain.enums.stream_event_type import StreamEventType

log = get_logger("vision.application.detection.zone_monitor")

class ZoneViolation(BaseModel):
    model_config = ConfigDict(frozen=True)
    zone_id: str
    zone_name: str
    camera_id: str
    detection_id: str
    hazard_type: str
    violation_type: str
    occupancy_count: int | None
    detected_at: datetime

class ZoneMonitorService:
    def _get_centroid(self, bbox: dict) -> tuple[float, float]:
        if not bbox:
            return (0.0, 0.0)
        return ((bbox.get("x_min", 0) + bbox.get("x_max", 0)) / 2.0, (bbox.get("y_min", 0) + bbox.get("y_max", 0)) / 2.0)
        
    def evaluate(self, camera_id: str, frame_id: str, detections: list[Detection], zones: list[CameraZone]) -> tuple[list[ZoneViolation], list[VisionAlert]]:
        violations = []
        alerts = []
        
        for zone in zones:
            inside_count = 0
            for d in detections:
                centroid = self._get_centroid(d.bounding_box)
                if hasattr(zone, 'contains_point') and zone.contains_point(centroid):
                    inside_count += 1
                    if getattr(zone, 'is_restricted', False) and getattr(d.hazard_type, 'value', str(d.hazard_type)) in ('PERSON', 'WORKER'):
                        viol = ZoneViolation(
                            zone_id=zone.zone_id,
                            zone_name=zone.name,
                            camera_id=camera_id,
                            detection_id=d.detection_id,
                            hazard_type=getattr(d.hazard_type, 'value', str(d.hazard_type)),
                            violation_type='RESTRICTED_ENTRY',
                            occupancy_count=None,
                            detected_at=datetime.now(timezone.utc)
                        )
                        violations.append(viol)
                        
                        alert = VisionAlert(
                            alert_id=str(uuid.uuid4()),
                            alert_type='RESTRICTED_ZONE_ENTRY',
                            severity=AlertSeverity.CRITICAL,
                            status=AlertStatus.ACTIVE,
                            created_at=datetime.now(timezone.utc),
                            camera_id=camera_id,
                            zone_id=zone.zone_id,
                            description=f"Restricted zone entry in {zone.name}",
                            detection_ids=[d.detection_id]
                        )
                        alerts.append(alert)
            
            max_occ = getattr(zone, 'max_occupancy', None)
            if max_occ is not None and inside_count > max_occ:
                viol = ZoneViolation(
                    zone_id=zone.zone_id,
                    zone_name=zone.name,
                    camera_id=camera_id,
                    detection_id="N/A",
                    hazard_type="MULTIPLE",
                    violation_type='OCCUPANCY_EXCEEDED',
                    occupancy_count=inside_count,
                    detected_at=datetime.now(timezone.utc)
                )
                violations.append(viol)
                alert = VisionAlert(
                    alert_id=str(uuid.uuid4()),
                    alert_type='OCCUPANCY_EXCEEDED',
                    severity=AlertSeverity.HIGH,
                    status=AlertStatus.ACTIVE,
                    created_at=datetime.now(timezone.utc),
                    camera_id=camera_id,
                    zone_id=zone.zone_id,
                    description=f"Occupancy exceeded in {zone.name} ({inside_count} > {max_occ})",
                    detection_ids=[]
                )
                alerts.append(alert)
                
        return violations, alerts

from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.domain.models import CameraTwin, _now_iso

log = get_logger(__name__)

class CameraTwinBuilder:
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        vision_data = context.get("vision_data", {})
        
        detected_workers = vision_data.get("detected_workers", [])
        detected_violations = vision_data.get("detected_violations", [])
        
        twin = CameraTwin(
            camera_id=entity_id,
            camera_name=vision_data.get("camera_name", f"Camera-{entity_id}"),
            zone_id=vision_data.get("zone_id", "UNKNOWN"),
            location=vision_data.get("location", {"x": 0.0, "y": 0.0, "z": 0.0}),
            is_online=vision_data.get("is_online", True),
            is_recording=vision_data.get("is_recording", True),
            last_frame_at=vision_data.get("last_frame_at", _now_iso()),
            detected_workers=detected_workers,
            detected_violations=detected_violations,
            occupancy_count=len(detected_workers),
            ppe_compliance_rate=vision_data.get("ppe_compliance_rate", 1.0),
            restricted_zone_violations=vision_data.get("restricted_zone_violations", 0),
            fire_detection_active=vision_data.get("fire_detection_active", False),
            smoke_detection_active=vision_data.get("smoke_detection_active", False)
        )
        return twin.model_dump()

    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]:
        updated = dict(current_state)
        vision_data = new_data.get("vision_data", {})
        
        if "detected_workers" in vision_data:
            updated["detected_workers"] = vision_data["detected_workers"]
            updated["occupancy_count"] = len(vision_data["detected_workers"])
            
        if "detected_violations" in vision_data:
            updated["detected_violations"] = vision_data["detected_violations"]
            
        for k in ["is_online", "is_recording", "ppe_compliance_rate", "restricted_zone_violations", "fire_detection_active", "smoke_detection_active"]:
            if k in vision_data:
                updated[k] = vision_data[k]
                
        updated["last_frame_at"] = _now_iso()
        updated["updated_at"] = _now_iso()
        return updated

    def validate(self, state: dict[str, Any]) -> bool:
        required = ["camera_id", "camera_name", "zone_id", "is_online", "occupancy_count"]
        return all(k in state for k in required)

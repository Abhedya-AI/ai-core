from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.domain.models import WorkerTwin, _now_iso

log = get_logger(__name__)

class WorkerTwinBuilder:
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        worker_data = context.get("worker_data", {})
        vision_data = context.get("vision_data", {})
        
        ppe_compliant = vision_data.get("ppe_compliant", worker_data.get("ppe_compliant", True))
        exposure_risk_score = context.get("risk_data", {}).get("exposure_risk_score", 0.1)
        safety_score = 1.0 if ppe_compliant else 0.5
        safety_score -= (exposure_risk_score * 0.5)
        safety_score = max(0.0, min(1.0, safety_score))
        
        fatigue_index = worker_data.get("fatigue_index", 0.0)
        
        twin = WorkerTwin(
            worker_id=entity_id,
            worker_name=worker_data.get("worker_name", f"Worker-{entity_id}"),
            worker_role=worker_data.get("worker_role", "OPERATOR"),
            current_zone_id=vision_data.get("current_zone_id", worker_data.get("current_zone_id", "UNKNOWN")),
            previous_zone_id=worker_data.get("previous_zone_id"),
            location=vision_data.get("location", {"x": 0.0, "y": 0.0}),
            safety_score=safety_score,
            exposure_risk_score=exposure_risk_score,
            fatigue_index=fatigue_index,
            ppe_compliant=ppe_compliant,
            ppe_items=worker_data.get("ppe_items", []),
            hours_on_shift=worker_data.get("hours_on_shift", 0.0),
            last_break_at=worker_data.get("last_break_at"),
            emergency_contact=worker_data.get("emergency_contact", ""),
            certifications=worker_data.get("certifications", []),
            active_tasks=worker_data.get("active_tasks", [])
        )
        return twin.model_dump()

    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]:
        updated = dict(current_state)
        
        if "vision_data" in new_data:
            vd = new_data["vision_data"]
            if "current_zone_id" in vd and vd["current_zone_id"] != updated.get("current_zone_id"):
                updated["previous_zone_id"] = updated.get("current_zone_id")
                updated["current_zone_id"] = vd["current_zone_id"]
            if "location" in vd: updated["location"] = vd["location"]
            if "ppe_compliant" in vd: updated["ppe_compliant"] = vd["ppe_compliant"]
            
        if "risk_data" in new_data:
            if "exposure_risk_score" in new_data["risk_data"]:
                updated["exposure_risk_score"] = new_data["risk_data"]["exposure_risk_score"]
                
        if "worker_data" in new_data:
            wd = new_data["worker_data"]
            if "hours_on_shift" in wd: updated["hours_on_shift"] = wd["hours_on_shift"]
            if "fatigue_index" in wd: updated["fatigue_index"] = wd["fatigue_index"]
            if "active_tasks" in wd: updated["active_tasks"] = wd["active_tasks"]

        ppe = updated.get("ppe_compliant", True)
        exposure = updated.get("exposure_risk_score", 0.0)
        ss = 1.0 if ppe else 0.5
        updated["safety_score"] = max(0.0, min(1.0, ss - (exposure * 0.5)))
        updated["updated_at"] = _now_iso()
        return updated

    def validate(self, state: dict[str, Any]) -> bool:
        required = ["worker_id", "worker_name", "current_zone_id", "safety_score"]
        return all(k in state for k in required)

from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.domain.models import ZoneTwin, _now_iso

log = get_logger(__name__)

class ZoneTwinBuilder:
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        zone_data = context.get("zone_data", {})
        equipment_states = context.get("equipment_states", [])
        sensor_states = context.get("sensor_states", [])
        worker_states = context.get("worker_states", [])
        hazard_data = context.get("hazard_data", {})
        
        eq_health = sum(e.get("health_score", 1.0) for e in equipment_states) / max(1, len(equipment_states))
        sens_health = sum(s.get("health_score", 1.0) for s in sensor_states) / max(1, len(sensor_states))
        work_health = sum(w.get("safety_score", 1.0) for w in worker_states) / max(1, len(worker_states))
        
        health_score = (eq_health * 0.4) + (sens_health * 0.3) + (work_health * 0.3)
        risk_score = zone_data.get("risk_score", 0.1)
        
        is_hazard_active = hazard_data.get("is_active", False)
        evacuation_required = hazard_data.get("evacuation_required", False)
        
        twin = ZoneTwin(
            zone_id=entity_id,
            zone_name=zone_data.get("zone_name", f"Zone-{entity_id}"),
            zone_type=zone_data.get("zone_type", "GENERAL"),
            floor_id=zone_data.get("floor_id", "UNKNOWN"),
            building_id=zone_data.get("building_id", "UNKNOWN"),
            plant_id=zone_data.get("plant_id", "UNKNOWN"),
            health_score=health_score,
            risk_score=risk_score,
            hazard_probability=zone_data.get("hazard_probability", {}),
            worker_ids=[w.get("worker_id") for w in worker_states if w.get("worker_id")],
            equipment_ids=[e.get("equipment_id") for e in equipment_states if e.get("equipment_id")],
            sensor_ids=[s.get("sensor_id") for s in sensor_states if s.get("sensor_id")],
            camera_ids=zone_data.get("camera_ids", []),
            occupancy=len(worker_states),
            max_occupancy=zone_data.get("max_occupancy", 100),
            environmental_data=zone_data.get("environmental_data", {}),
            is_restricted=zone_data.get("is_restricted", False),
            is_hazard_active=is_hazard_active,
            evacuation_required=evacuation_required
        )
        return twin.model_dump()

    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]:
        updated = dict(current_state)
        # In a real sync, we'd rebuild aggregated values. For now we merge simple fields.
        if "zone_data" in new_data:
            zd = new_data["zone_data"]
            for k in ["environmental_data", "risk_score", "is_restricted"]:
                if k in zd:
                    updated[k] = zd[k]
                    
        if "hazard_data" in new_data:
            hd = new_data["hazard_data"]
            if "is_active" in hd: updated["is_hazard_active"] = hd["is_active"]
            if "evacuation_required" in hd: updated["evacuation_required"] = hd["evacuation_required"]
            
        updated["updated_at"] = _now_iso()
        return updated

    def validate(self, state: dict[str, Any]) -> bool:
        required = ["zone_id", "zone_name", "health_score", "occupancy"]
        return all(k in state for k in required)

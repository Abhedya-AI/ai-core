from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.domain.models import PlantTwin, _now_iso

log = get_logger(__name__)

class PlantTwinBuilder:
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        plant_data = context.get("plant_data", {})
        building_states = context.get("building_states", [])
        
        b_health = sum(b.get("health_score", 1.0) for b in building_states) / max(1, len(building_states))
        worker_health = plant_data.get("worker_health_avg", 1.0)
        equipment_health = plant_data.get("equipment_health_avg", 1.0)
        
        overall_health_score = (b_health * 0.5) + (worker_health * 0.25) + (equipment_health * 0.25)
        overall_risk_score = sum(b.get("risk_score", 0.0) for b in building_states) / max(1, len(building_states))
        
        floor_ids = []
        zone_ids = []
        for b in building_states:
            floor_ids.extend(b.get("floor_ids", []))
            zone_ids.extend(b.get("zone_ids", []))
            
        twin = PlantTwin(
            plant_id=entity_id,
            plant_name=plant_data.get("plant_name", f"Plant-{entity_id}"),
            twin_id=plant_data.get("twin_id", "UNKNOWN"),
            building_ids=[b.get("building_id") for b in building_states if b.get("building_id")],
            floor_ids=floor_ids,
            zone_ids=zone_ids,
            overall_health_score=overall_health_score,
            overall_risk_score=overall_risk_score,
            operational_stability_score=plant_data.get("operational_stability_score", overall_health_score),
            emergency_readiness_score=plant_data.get("emergency_readiness_score", 1.0),
            compliance_score=plant_data.get("compliance_score", 1.0),
            worker_count=sum(b.get("worker_count", 0) for b in building_states),
            equipment_count=sum(b.get("equipment_count", 0) for b in building_states),
            sensor_count=plant_data.get("sensor_count", 0),
            camera_count=plant_data.get("camera_count", 0),
            active_hazards=plant_data.get("active_hazards", []),
            critical_zones=plant_data.get("critical_zones", []),
            critical_equipment=plant_data.get("critical_equipment", [])
        )
        return twin.model_dump()

    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]:
        updated = dict(current_state)
        updated["updated_at"] = _now_iso()
        return updated

    def validate(self, state: dict[str, Any]) -> bool:
        required = ["plant_id", "plant_name", "twin_id", "overall_health_score"]
        return all(k in state for k in required)

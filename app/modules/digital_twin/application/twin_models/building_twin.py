from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.domain.models import BuildingTwin, _now_iso

log = get_logger(__name__)

class BuildingTwinBuilder:
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        building_data = context.get("building_data", {})
        floor_states = context.get("floor_states", [])
        
        health_score = sum(f.get("health_score", 1.0) for f in floor_states) / max(1, len(floor_states))
        risk_score = sum(f.get("risk_score", 0.0) for f in floor_states) / max(1, len(floor_states))
        
        has_active_hazard = any(f.get("has_active_hazard", False) for f in floor_states)
        emergency_status = "ACTIVE" if has_active_hazard or risk_score > 0.8 else "NORMAL"
        
        zone_ids = []
        for f in floor_states:
            zone_ids.extend(f.get("zone_ids", []))
            
        twin = BuildingTwin(
            building_id=entity_id,
            building_name=building_data.get("building_name", f"Building-{entity_id}"),
            plant_id=building_data.get("plant_id", "UNKNOWN"),
            floor_ids=[f.get("floor_id") for f in floor_states if f.get("floor_id")],
            zone_ids=zone_ids,
            equipment_count=sum(f.get("equipment_count", 0) for f in floor_states),
            worker_count=sum(f.get("worker_count", 0) for f in floor_states),
            health_score=health_score,
            risk_score=risk_score,
            has_active_hazard=has_active_hazard,
            emergency_status=emergency_status
        )
        return twin.model_dump()

    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]:
        updated = dict(current_state)
        updated["updated_at"] = _now_iso()
        return updated

    def validate(self, state: dict[str, Any]) -> bool:
        required = ["building_id", "building_name", "plant_id", "health_score"]
        return all(k in state for k in required)

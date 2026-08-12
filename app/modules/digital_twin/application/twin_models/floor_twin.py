from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.domain.models import FloorTwin, _now_iso

log = get_logger(__name__)

class FloorTwinBuilder:
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        floor_data = context.get("floor_data", {})
        zone_states = context.get("zone_states", [])
        
        health_score = sum(z.get("health_score", 1.0) for z in zone_states) / max(1, len(zone_states))
        risk_score = sum(z.get("risk_score", 0.0) for z in zone_states) / max(1, len(zone_states))
        
        has_active_hazard = any(z.get("is_hazard_active", False) for z in zone_states)
        evacuation_required = any(z.get("evacuation_required", False) for z in zone_states)
        
        twin = FloorTwin(
            floor_id=entity_id,
            floor_name=floor_data.get("floor_name", f"Floor-{entity_id}"),
            floor_number=floor_data.get("floor_number", 1),
            building_id=floor_data.get("building_id", "UNKNOWN"),
            plant_id=floor_data.get("plant_id", "UNKNOWN"),
            zone_ids=[z.get("zone_id") for z in zone_states if z.get("zone_id")],
            equipment_count=sum(len(z.get("equipment_ids", [])) for z in zone_states),
            worker_count=sum(len(z.get("worker_ids", [])) for z in zone_states),
            health_score=health_score,
            risk_score=risk_score,
            has_active_hazard=has_active_hazard,
            evacuation_required=evacuation_required
        )
        return twin.model_dump()

    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]:
        updated = dict(current_state)
        updated["updated_at"] = _now_iso()
        return updated

    def validate(self, state: dict[str, Any]) -> bool:
        required = ["floor_id", "floor_name", "building_id", "health_score"]
        return all(k in state for k in required)

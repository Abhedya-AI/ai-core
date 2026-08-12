from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.domain.models import EquipmentTwin, _now_iso

log = get_logger(__name__)

class EquipmentTwinBuilder:
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        eq_data = context.get("equipment_data", {})
        risk_data = context.get("risk_data", {})
        forecast_data = context.get("forecast_data", {})
        
        health_score = risk_data.get("health_score", 0.85)
        rul_hours = forecast_data.get("rul_hours")
        
        current_load = eq_data.get("current_load", 0.0)
        rated_capacity = eq_data.get("rated_capacity", 1.0)
        utilization_pct = current_load / rated_capacity if rated_capacity > 0 else 0.0
        
        twin = EquipmentTwin(
            equipment_id=entity_id,
            equipment_name=eq_data.get("equipment_name", f"Eq-{entity_id}"),
            equipment_type=eq_data.get("equipment_type", "UNKNOWN"),
            zone_id=eq_data.get("zone_id", "UNKNOWN"),
            floor_id=eq_data.get("floor_id", "UNKNOWN"),
            building_id=eq_data.get("building_id", "UNKNOWN"),
            status=eq_data.get("status", "ACTIVE"),
            health_score=health_score,
            risk_score=risk_data.get("risk_score", 0.1),
            utilization_pct=utilization_pct,
            rul_hours=rul_hours,
            last_maintenance_at=eq_data.get("last_maintenance_at"),
            next_maintenance_at=eq_data.get("next_maintenance_at"),
            maintenance_urgency=self._determine_maintenance_urgency(health_score, rul_hours),
            anomalous_sensors=eq_data.get("anomalous_sensors", []),
            sensor_ids=eq_data.get("sensor_ids", []),
            dependency_ids=eq_data.get("dependency_ids", []),
            failure_probability=forecast_data.get("failure_probability", {}),
            current_load=current_load,
            rated_capacity=rated_capacity
        )
        return twin.model_dump()

    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]:
        updated = dict(current_state)
        
        if "equipment_data" in new_data:
            eq = new_data["equipment_data"]
            for k in ["current_load", "status", "anomalous_sensors"]:
                if k in eq:
                    updated[k] = eq[k]
            if "current_load" in eq:
                rated = updated.get("rated_capacity", 1.0)
                updated["utilization_pct"] = eq["current_load"] / rated if rated > 0 else 0.0
                
        if "risk_data" in new_data:
            rd = new_data["risk_data"]
            if "health_score" in rd: updated["health_score"] = rd["health_score"]
            if "risk_score" in rd: updated["risk_score"] = rd["risk_score"]
            
        if "forecast_data" in new_data:
            fd = new_data["forecast_data"]
            if "rul_hours" in fd: updated["rul_hours"] = fd["rul_hours"]
            if "failure_probability" in fd: updated["failure_probability"] = fd["failure_probability"]
            
        updated["maintenance_urgency"] = self._determine_maintenance_urgency(
            updated.get("health_score", 1.0), 
            updated.get("rul_hours")
        )
        updated["updated_at"] = _now_iso()
        return updated

    def validate(self, state: dict[str, Any]) -> bool:
        required = ["equipment_id", "equipment_name", "zone_id", "health_score", "risk_score"]
        return all(k in state for k in required)

    def _determine_maintenance_urgency(self, health_score: float, rul_hours: float | None) -> str:
        if health_score < 0.3 or (rul_hours is not None and rul_hours < 24):
            return "IMMEDIATE"
        if health_score < 0.5 or (rul_hours is not None and rul_hours < 72):
            return "URGENT"
        if health_score < 0.8 or (rul_hours is not None and rul_hours < 168):
            return "SCHEDULED"
        return "ROUTINE"

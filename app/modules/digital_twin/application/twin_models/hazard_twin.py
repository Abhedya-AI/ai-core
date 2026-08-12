from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.domain.models import HazardTwin, _now_iso

log = get_logger(__name__)

class HazardTwinBuilder:
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        hazard_data = context.get("hazard_propagation_data", {})
        
        intensity = hazard_data.get("current_intensity", 0.5)
        severity = hazard_data.get("severity", "MEDIUM")
        
        risk_score = intensity
        if severity == "HIGH": risk_score += 0.2
        elif severity == "CRITICAL": risk_score += 0.4
        risk_score = min(1.0, risk_score)
        
        twin = HazardTwin(
            hazard_id=entity_id,
            hazard_type=hazard_data.get("hazard_type", "UNKNOWN"),
            source_zone_id=hazard_data.get("source_zone_id", "UNKNOWN"),
            affected_zones=hazard_data.get("affected_zones", []),
            propagation_state=hazard_data.get("propagation_state", "ACTIVE"),
            severity=severity,
            current_intensity=intensity,
            containment_status=hazard_data.get("containment_status", "UNCONTAINED"),
            affected_worker_count=hazard_data.get("affected_worker_count", 0),
            affected_equipment_count=hazard_data.get("affected_equipment_count", 0),
            propagation_probability=hazard_data.get("propagation_probability", {}),
            risk_score=risk_score,
            started_at=hazard_data.get("started_at", _now_iso()),
            estimated_containment_at=hazard_data.get("estimated_containment_at"),
            graphrag_citations=hazard_data.get("graphrag_citations", []),
            kg_node_id=hazard_data.get("kg_node_id")
        )
        return twin.model_dump()

    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]:
        updated = dict(current_state)
        hd = new_data.get("hazard_propagation_data", {})
        
        for k in ["propagation_state", "severity", "current_intensity", "containment_status", 
                  "affected_worker_count", "affected_equipment_count", "propagation_probability"]:
            if k in hd:
                updated[k] = hd[k]
                
        if "current_intensity" in hd or "severity" in hd:
            intensity = updated.get("current_intensity", 0.5)
            severity = updated.get("severity", "MEDIUM")
            risk = intensity
            if severity == "HIGH": risk += 0.2
            elif severity == "CRITICAL": risk += 0.4
            updated["risk_score"] = min(1.0, risk)
            
        updated["last_updated"] = _now_iso()
        return updated

    def validate(self, state: dict[str, Any]) -> bool:
        required = ["hazard_id", "hazard_type", "source_zone_id", "risk_score"]
        return all(k in state for k in required)

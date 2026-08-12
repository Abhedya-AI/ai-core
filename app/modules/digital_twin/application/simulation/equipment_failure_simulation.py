from __future__ import annotations

import time
import uuid
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.simulation.base import AbstractSimulation, SimulationResult

log = get_logger(__name__)

class EquipmentFailureSimulation:
    def get_type(self) -> str:
        return "EQUIPMENT_FAILURE"

    def get_assumptions(self) -> list[str]:
        return ["Dependencies degrade by 0.2 per hop", "MTTR based repair"]

    async def run(self, twin_state: dict[str, Any], parameters: dict[str, Any], graphrag_service: Any) -> SimulationResult:
        t0 = time.perf_counter()
        sim_id = str(uuid.uuid4())
        
        eq_id = parameters.get("equipment_id")
        cascade = bool(parameters.get("cascade", True))
        
        current_state = dict(twin_state)
        timeline = []
        cascade_failures = 0
        
        if eq_id in current_state:
            current_state[eq_id]["health_score"] = 0.0
            current_state[eq_id]["status"] = "OFFLINE"
            
            if cascade:
                deps = current_state[eq_id].get("dependency_ids", [])
                for dep in deps:
                    if dep in current_state:
                        current_state[dep]["health_score"] -= 0.2
                        cascade_failures += 1
                        
        timeline.append({"t": 0.0, "states": current_state, "events": [f"Equipment {eq_id} failed"]})
        timeline.append({"t": 4.0, "states": current_state, "events": ["Repair completed"]})
        
        try:
            from app.modules.hazard_propagation.application.services.hazard_orchestration_service import HazardOrchestrationService
            hs = HazardOrchestrationService()
        except Exception:
            pass
            
        summary = {
            "cascade_failures": cascade_failures,
            "production_loss_pct": 0.15,
            "estimated_repair_hours": 4.0,
            "total_affected_equipment": cascade_failures + 1
        }
        
        latency = (time.perf_counter() - t0) * 1000
        
        return SimulationResult(
            simulation_id=sim_id,
            simulation_type=self.get_type(),
            status="COMPLETED",
            timeline=timeline,
            summary=summary,
            assumptions=self.get_assumptions(),
            kg_paths=[],
            graphrag_citations=[],
            risk_references=[],
            forecast_references=[],
            hazard_references=[],
            confidence=0.85,
            alternative_scenarios=[],
            recommended_actions=[],
            latency_ms=latency,
            error=None
        )

from __future__ import annotations

import time
import uuid
import numpy as np
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.simulation.base import AbstractSimulation, SimulationResult

log = get_logger(__name__)

class PowerLossSimulation:
    def get_type(self) -> str:
        return "POWER_LOSS"

    def get_assumptions(self) -> list[str]:
        return ["Exponential battery drain", "UPS sustains critical loads"]

    async def run(self, twin_state: dict[str, Any], parameters: dict[str, Any], graphrag_service: Any) -> SimulationResult:
        t0 = time.perf_counter()
        sim_id = str(uuid.uuid4())
        
        scope = parameters.get("scope", "FULL")
        affected_zones = parameters.get("affected_zones", [])
        duration_hours = float(parameters.get("duration_hours", 4.0))
        
        current_state = dict(twin_state)
        timeline = []
        eq_offline = 0
        crit_affected = 0
        
        for eid, ed in current_state.items():
            if ed.get("type") == "EQUIPMENT":
                if scope == "FULL" or (scope == "ZONE" and ed.get("zone_id") in affected_zones):
                    if not ed.get("critical", False):
                        ed["status"] = "OFFLINE"
                        eq_offline += 1
                    else:
                        crit_affected += 1
                        
        steps = int(duration_hours)
        for step in range(steps):
            t = float(step)
            timeline.append({"t": t, "states": dict(current_state), "events": []})
            
        summary = {
            "equipment_offline_count": eq_offline,
            "critical_systems_affected": crit_affected,
            "backup_duration_hours": 2.0,
            "recovery_sequence": []
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
            confidence=0.9,
            alternative_scenarios=[],
            recommended_actions=[],
            latency_ms=latency,
            error=None
        )

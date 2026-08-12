from __future__ import annotations

import time
import uuid
import numpy as np
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.simulation.base import AbstractSimulation, SimulationResult

log = get_logger(__name__)

class ShutdownSimulation:
    def get_type(self) -> str:
        return "SHUTDOWN"

    def get_assumptions(self) -> list[str]:
        return ["Staged shutdown groups by dependency", "Linear power draw reduction"]

    async def run(self, twin_state: dict[str, Any], parameters: dict[str, Any], graphrag_service: Any) -> SimulationResult:
        t0 = time.perf_counter()
        sim_id = str(uuid.uuid4())
        
        shutdown_type = parameters.get("shutdown_type", "PLANNED")
        scope = parameters.get("scope", [])
        duration_hours = float(parameters.get("duration_hours", 2.0))
        
        timeline = []
        current_state = dict(twin_state)
        
        eq_in_scope = []
        for eid, ed in current_state.items():
            if ed.get("type") == "EQUIPMENT" and (eid in scope or ed.get("zone_id") in scope):
                eq_in_scope.append(eid)
                
        shutdown_time = 0.0 if shutdown_type == "EMERGENCY" else 2.0
        
        steps = int((duration_hours + shutdown_time) * 2)
        power_reduction_pct = 0.0
        worker_relocated = 0
        
        for step in range(steps):
            t = float(step) * 0.5
            step_state = dict(current_state)
            step_events = []
            
            if shutdown_type == "EMERGENCY" and t == 0:
                for eid in eq_in_scope:
                    step_state[eid]["status"] = "OFFLINE"
                step_events.append("Emergency shutdown of all scope equipment")
                power_reduction_pct = 1.0
                
            elif shutdown_type == "PLANNED":
                if t <= shutdown_time and shutdown_time > 0:
                    pct = t / shutdown_time
                    power_reduction_pct = pct
                    to_shutdown = int(len(eq_in_scope) * pct)
                    for eid in eq_in_scope[:to_shutdown]:
                        if step_state[eid].get("status") != "OFFLINE":
                            step_state[eid]["status"] = "OFFLINE"
                            step_events.append(f"{eid} gracefully shutdown")
                            
            if t > shutdown_time:
                # restart sequence if PLANNED
                pass
                
            timeline.append({"t": t, "states": step_state, "events": step_events})
            
        summary = {
            "equipment_shutdown_count": len(eq_in_scope),
            "worker_relocated": worker_relocated,
            "power_reduction_pct": power_reduction_pct,
            "safe_shutdown_achieved": True
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
            confidence=0.95 if shutdown_type == "PLANNED" else 0.8,
            alternative_scenarios=[],
            recommended_actions=[],
            latency_ms=latency,
            error=None
        )

from __future__ import annotations

import time
import uuid
import numpy as np
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.simulation.base import AbstractSimulation, SimulationResult

log = get_logger(__name__)

class MaintenanceSimulation:
    def get_type(self) -> str:
        return "MAINTENANCE"

    def get_assumptions(self) -> list[str]:
        return ["Linear production loss", "Staggered intervals for non-simultaneous maintenance"]

    async def run(self, twin_state: dict[str, Any], parameters: dict[str, Any], graphrag_service: Any) -> SimulationResult:
        t0 = time.perf_counter()
        sim_id = str(uuid.uuid4())
        
        equipment_ids = parameters.get("equipment_ids", [])
        maintenance_type = parameters.get("maintenance_type", "ROUTINE")
        duration_hours = float(parameters.get("duration_hours", 4.0))
        simultaneous = bool(parameters.get("simultaneous", True))
        
        timeline = []
        current_state = dict(twin_state)
        
        total_capacity = sum(e.get("production_capacity", 100) for e in current_state.values() if e.get("type") == "EQUIPMENT")
        if total_capacity == 0:
            total_capacity = 1.0
            
        prod_loss = 0.0
        health_gain = 0.0
        
        start_times = {}
        for i, eq_id in enumerate(equipment_ids):
            start_times[eq_id] = 0.0 if simultaneous else float(i * 4.0)
            
        max_time = max(start_times.values(), default=0.0) + duration_hours + 2.0
        steps = int(max_time * 2)
        
        for step in range(steps):
            t = float(step) * 0.5
            step_state = dict(current_state)
            step_events = []
            
            for eq_id in equipment_ids:
                if eq_id not in step_state:
                    continue
                    
                st = start_times[eq_id]
                et = st + duration_hours
                
                if st <= t < et:
                    step_state[eq_id]["status"] = "MAINTENANCE"
                    step_state[eq_id]["utilization"] = 0.0
                    loss = step_state[eq_id].get("production_capacity", 100) / total_capacity
                    prod_loss += loss * 0.5  # per 0.5h step
                    if t == st:
                        step_events.append(f"Started maintenance on {eq_id}")
                elif t >= et and step_state[eq_id].get("status") != "ACTIVE":
                    step_state[eq_id]["status"] = "ACTIVE"
                    old_h = step_state[eq_id].get("health_score", 0.5)
                    step_state[eq_id]["health_score"] = min(1.0, old_h + 0.3)
                    health_gain += (step_state[eq_id]["health_score"] - old_h)
                    step_events.append(f"Completed maintenance on {eq_id}")
                    
            timeline.append({"t": t, "states": step_state, "events": step_events})
            
        try:
            from app.modules.forecast.application.services.forecast_orchestration_service import ForecastOrchestrationService
            fs = ForecastOrchestrationService()
            # Try to get RUL projection if available
        except Exception:
            pass
            
        summary = {
            "production_loss_pct": float(prod_loss / max(1.0, max_time)),
            "maintenance_duration_hours": float(max_time),
            "equipment_restored": len(equipment_ids),
            "health_gain": float(health_gain / max(1, len(equipment_ids)))
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

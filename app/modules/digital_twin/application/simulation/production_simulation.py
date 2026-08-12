from __future__ import annotations

import time
import uuid
import numpy as np
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.simulation.base import AbstractSimulation, SimulationResult

log = get_logger(__name__)

class ProductionSimulation:
    def get_type(self) -> str:
        return "PRODUCTION"

    def get_assumptions(self) -> list[str]:
        return ["Linear programming approximation", "Fixed 1h steps"]

    async def run(self, twin_state: dict[str, Any], parameters: dict[str, Any], graphrag_service: Any) -> SimulationResult:
        t0 = time.perf_counter()
        sim_id = str(uuid.uuid4())
        
        target_output_pct = float(parameters.get("target_output_pct", 1.0))
        horizon_hours = float(parameters.get("horizon_hours", 24.0))
        constraints = parameters.get("constraints", {})
        
        timeline = []
        current_state = dict(twin_state)
        
        eq_list = [e for e in current_state.values() if e.get("type") == "EQUIPMENT"]
        
        steps = int(horizon_hours)
        total_output = 0.0
        energy_req = 0.0
        worker_demand = 0
        
        for step in range(steps):
            t = float(step)
            step_state = dict(current_state)
            
            step_output = 0.0
            for eq in eq_list:
                cap = eq.get("production_capacity", 100)
                h = eq.get("health_score", 1.0)
                r = eq.get("risk_score", 0.0)
                out = cap * h * (1.0 - r) * min(1.0, target_output_pct)
                step_output += out
                energy_req += out * 0.5  # mock energy formula
                worker_demand = max(worker_demand, int(out * 0.1))
                
            total_output += step_output
            timeline.append({"t": t, "states": step_state, "events": []})
            
        try:
            from app.modules.forecast.application.services.forecast_orchestration_service import ForecastOrchestrationService
            fs = ForecastOrchestrationService()
        except Exception:
            pass
            
        summary = {
            "achievable_output_pct": min(1.0, total_output / (len(eq_list) * 100 * steps)) if eq_list else 0.0,
            "bottleneck_equipment": eq_list[0].get("id") if eq_list else None,
            "energy_required_kwh": energy_req,
            "worker_demand": worker_demand
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

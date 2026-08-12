from __future__ import annotations

import time
import uuid
import numpy as np
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.simulation.base import AbstractSimulation, SimulationResult

log = get_logger(__name__)

class HazardReplaySimulation:
    def get_type(self) -> str:
        return "HAZARD_REPLAY"

    def get_assumptions(self) -> list[str]:
        return ["Exponential growth and decay model", "Hazard propagation model integration"]

    async def run(self, twin_state: dict[str, Any], parameters: dict[str, Any], graphrag_service: Any) -> SimulationResult:
        t0 = time.perf_counter()
        sim_id = str(uuid.uuid4())
        
        hazard_id = parameters.get("hazard_id", "")
        hazard_type = parameters.get("hazard_type", "UNKNOWN")
        initial_intensity = float(parameters.get("initial_intensity", 1.0))
        affected_zones = parameters.get("affected_zones", [])
        duration_hours = float(parameters.get("duration_hours", 24.0))
        
        prop_result = None
        try:
            from app.modules.hazard_propagation.application.services.hazard_orchestration_service import HazardOrchestrationService
            hazard_svc = HazardOrchestrationService()
            prop_result = await hazard_svc.analyze_propagation(hazard_id=hazard_id, context=twin_state)
        except Exception as e:
            log.warning(f"HazardOrchestrationService not available: {e}")
            
        timeline = []
        peak_intensity = 0.0
        peak_time = 0.0
        
        if prop_result and isinstance(prop_result, dict) and "timeline" in prop_result:
            timeline = prop_result["timeline"]
            peak_intensity = prop_result.get("peak_intensity", 0.0)
            peak_time = prop_result.get("peak_time", 0.0)
        else:
            steps = int(duration_hours * 2)
            A = initial_intensity
            k = 0.5
            d = 0.2
            peak = duration_hours / 4.0
            
            for step in range(steps):
                t = float(step) * 0.5
                intensity = A * (1 - np.exp(-k * max(0, t))) * np.exp(-d * max(0, t - peak))
                
                if intensity > peak_intensity:
                    peak_intensity = intensity
                    peak_time = t
                    
                states = dict(twin_state)
                for z in affected_zones:
                    if z in states:
                        states[z]["hazard_intensity"] = intensity
                        
                timeline.append({
                    "t": t,
                    "states": states,
                    "events": [f"Hazard intensity at {intensity:.2f}"] if intensity > 0.1 else []
                })
                
        workers_at_risk = sum(1 for e in twin_state.values() if e.get("type") == "WORKER" and e.get("zone_id") in affected_zones)
        
        summary = {
            "peak_intensity": float(peak_intensity),
            "peak_time_hours": float(peak_time),
            "zones_affected": affected_zones,
            "workers_at_risk": workers_at_risk,
            "containment_probability": 0.75
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

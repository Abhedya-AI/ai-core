from __future__ import annotations

import time
import uuid
import numpy as np
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.simulation.base import AbstractSimulation, SimulationResult

log = get_logger(__name__)

class EmergencySimulation:
    def get_type(self) -> str:
        return "EMERGENCY"

    def get_assumptions(self) -> list[str]:
        return ["Exponential decay propagation", "15 minute time steps", "Standard evacuation protocols"]

    async def run(self, twin_state: dict[str, Any], parameters: dict[str, Any], graphrag_service: Any) -> SimulationResult:
        t0 = time.perf_counter()
        sim_id = str(uuid.uuid4())
        
        emergency_type = parameters.get("emergency_type", "GENERAL")
        source_zone_id = parameters.get("source_zone_id")
        severity = float(parameters.get("severity", 0.5))
        affected_systems = parameters.get("affected_systems", [])
        
        timeline = []
        current_state = dict(twin_state)
        affected_zones = set()
        
        if source_zone_id and source_zone_id in current_state:
            current_state[source_zone_id]["risk_score"] = min(1.0, severity)
            current_state[source_zone_id]["emergency"] = True
            affected_zones.add(source_zone_id)
            
            # Propagation
            for zone_id, zone_data in current_state.items():
                if zone_data.get("type") == "ZONE" and zone_id != source_zone_id:
                    adj_zones = zone_data.get("adjacent_zones", [])
                    if source_zone_id in adj_zones:
                        zone_data["risk_score"] = current_state[source_zone_id]["risk_score"] * 0.6
                        affected_zones.add(zone_id)
                        
        for eq_id, eq_data in current_state.items():
            if eq_data.get("zone_id") in affected_zones:
                eq_data["status"] = "DEGRADED"
                
        total_evacuated = 0
        total_workers = sum(1 for e in current_state.values() if e.get("type") == "WORKER")
        
        # Time steps (0, 15, 30, 60, 120, 240 mins)
        steps = [0, 15, 30, 60, 120, 240]
        events_by_step = {
            0: ["Emergency detected, zones affected"],
            15: ["Evacuation initiated in high-risk zones"],
            30: ["Emergency services dispatched"],
            60: ["Containment begins"],
            120: ["Situation stabilizing"],
            240: ["Resolution assessment"]
        }
        
        containment_time = 120
        isolated_eq = len([e for e in current_state.values() if e.get("zone_id") in affected_zones])
        
        for t in steps:
            evacuated_now = 0
            if t >= 15:
                evacuated_now = int(total_workers * min(1.0, t / 120.0))
            
            total_evacuated = max(total_evacuated, evacuated_now)
            
            step_state = dict(current_state)
            step_state["evacuated_count"] = total_evacuated
            
            timeline.append({
                "t": float(t) / 60.0,
                "states": step_state,
                "events": events_by_step.get(t, [])
            })
            
        summary = {
            "total_workers_evacuated": total_evacuated,
            "zones_affected": list(affected_zones),
            "equipment_isolated": isolated_eq,
            "containment_time_min": containment_time
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
            confidence=0.8,
            alternative_scenarios=[],
            recommended_actions=["Review evacuation routes", "Test emergency response times"],
            latency_ms=latency,
            error=None
        )

from __future__ import annotations

import time
import uuid
import numpy as np
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.simulation.base import AbstractSimulation, SimulationResult

log = get_logger(__name__)

class WhatIfSimulation:
    def get_type(self) -> str:
        return "WHAT_IF"

    def get_assumptions(self) -> list[str]:
        return ["Linear propagation assumed", "No external interventions", "1 hour default time steps"]

    async def run(self, twin_state: dict[str, Any], parameters: dict[str, Any], graphrag_service: Any) -> SimulationResult:
        t0 = time.perf_counter()
        sim_id = str(uuid.uuid4())
        
        scenario_name = parameters.get("scenario_name", "Unknown Scenario")
        changes = parameters.get("changes", {})
        horizon_hours = parameters.get("horizon_hours", 24)
        focus_entities = parameters.get("focus_entities", [])
        
        timeline = []
        current_state = dict(twin_state)
        affected_entities = set()
        
        step_size = 1.0
        steps = int(horizon_hours / step_size)
        
        # Initial changes
        for entity_id, fields in changes.items():
            if entity_id not in current_state:
                current_state[entity_id] = {}
            for k, v in fields.items():
                current_state[entity_id][k] = v
            affected_entities.add(entity_id)

        for step in range(steps):
            t = float(step * step_size)
            next_state = dict(current_state)
            step_events = []
            
            for entity_id, state in current_state.items():
                health_score = state.get("health_score", 1.0)
                risk_score = state.get("risk_score", 0.0)
                
                # Dependencies
                dependencies = state.get("dependency_ids", [])
                for dep_id in dependencies:
                    if dep_id in current_state:
                        dep_health = current_state[dep_id].get("health_score", 1.0)
                        if dep_health < 0.8:
                            health_drop = (1.0 - dep_health) * 0.3
                            next_state[entity_id]["health_score"] = max(0.0, health_score - health_drop)
                            affected_entities.add(entity_id)
                            step_events.append(f"{entity_id} health dropped due to {dep_id}")
                
                # Zone hazards
                zone_id = state.get("zone_id")
                if zone_id and zone_id in current_state:
                    zone_hazards = current_state[zone_id].get("hazards", [])
                    if zone_hazards and "safety_score" in state:
                        next_state[entity_id]["safety_score"] = max(0.0, state["safety_score"] - (0.2 * len(zone_hazards)))
                        affected_entities.add(entity_id)
                        
                # Sensor failure
                if state.get("type") == "SENSOR" and health_score < 0.5:
                    parent_id = state.get("parent_id")
                    if parent_id and parent_id in next_state:
                        p_health = next_state[parent_id].get("health_score", 1.0)
                        next_state[parent_id]["health_score"] = max(0.0, p_health - 0.15)
                        affected_entities.add(parent_id)
            
            current_state = next_state
            timeline.append({"t": t, "states": dict(current_state), "events": step_events})
            
        citations = []
        if graphrag_service:
            try:
                res = await graphrag_service.answer(f"What are consequences of {scenario_name} in industrial plant?")
                if hasattr(res, "citations"):
                    citations = res.citations
                elif isinstance(res, dict) and "citations" in res:
                    citations = res["citations"]
            except Exception as e:
                log.warning(f"GraphRAG error: {e}")
                
        summary = {
            "affected_entities": list(affected_entities),
            "max_risk_entity": "N/A",
            "min_health_entity": "N/A",
            "overall_plant_health_delta": -0.05
        }
        
        confidence = 0.5 + (0.4 * min(1.0, len(affected_entities) / max(1, len(current_state))))
        latency = (time.perf_counter() - t0) * 1000
        
        return SimulationResult(
            simulation_id=sim_id,
            simulation_type=self.get_type(),
            status="COMPLETED",
            timeline=timeline,
            summary=summary,
            assumptions=self.get_assumptions(),
            kg_paths=[],
            graphrag_citations=citations,
            risk_references=[],
            forecast_references=[],
            hazard_references=[],
            confidence=confidence,
            alternative_scenarios=[],
            recommended_actions=[],
            latency_ms=latency,
            error=None
        )

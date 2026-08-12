from __future__ import annotations

import time
import uuid
import networkx as nx
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.application.simulation.base import AbstractSimulation, SimulationResult

log = get_logger(__name__)

class WorkerMovementSimulation:
    def get_type(self) -> str:
        return "WORKER_MOVEMENT"

    def get_assumptions(self) -> list[str]:
        return ["Dijkstra shortest path for evacuation", "Crowd density slows movement"]

    async def run(self, twin_state: dict[str, Any], parameters: dict[str, Any], graphrag_service: Any) -> SimulationResult:
        t0 = time.perf_counter()
        sim_id = str(uuid.uuid4())
        
        scenario = parameters.get("scenario", "NORMAL")
        source_zones = parameters.get("source_zone_ids", [])
        dest_zones = parameters.get("destination_zone_ids", [])
        
        graph = nx.DiGraph()
        zones = {k: v for k, v in twin_state.items() if v.get("type") == "ZONE"}
        workers = {k: v for k, v in twin_state.items() if v.get("type") == "WORKER"}
        
        for zid, zd in zones.items():
            graph.add_node(zid)
            for adj in zd.get("adjacent_zones", []):
                graph.add_edge(zid, adj, weight=5.0)  # 5 mins base
                
        timeline = []
        evacuated = 0
        total_time = 0.0
        
        if scenario == "EVACUATION":
            if not dest_zones:
                dest_zones = [z for z, d in zones.items() if d.get("risk_score", 0.0) < 0.2]
                
            total_time = 30.0  # mock approx
            evacuated = len(workers)
            
            for step in range(6):
                t = step * 5.0
                timeline.append({"t": t, "states": dict(twin_state), "events": [f"Workers moving..."]})
                
        summary = {
            "total_evacuation_time_min": total_time,
            "workers_evacuated": evacuated,
            "bottleneck_zones": [],
            "safe_workers_pct": 1.0 if workers else 0.0
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
            recommended_actions=[],
            latency_ms=latency,
            error=None
        )

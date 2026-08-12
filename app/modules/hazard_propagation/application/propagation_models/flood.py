from __future__ import annotations
import math
import numpy as np
from typing import Any
from app.core.logging import get_logger
from app.modules.hazard_propagation.application.propagation_models.base import PropagationResult

log = get_logger(__name__)

class FloodPropagationModel:
    """Flood propagation via adjacent zones."""
    
    def __init__(self, drainage_coeff: float = 0.3, max_flood_level: float = 2.0) -> None:
        self.drainage_coeff = drainage_coeff
        self.max_flood_level = max_flood_level

    async def propagate(
        self,
        source_node_id: str,
        initial_intensity: float,
        graph_nodes: list[dict],
        graph_edges: list[dict],
        context: dict[str, Any],
        time_steps: int,
    ) -> PropagationResult:
        log.debug(f"FloodPropagationModel.propagate: source={source_node_id}")
        
        if not graph_nodes:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
            
        node_ids = [n["node_id"] for n in graph_nodes]
        water_levels = {nid: 0.0 for nid in node_ids}
        if source_node_id in water_levels:
            water_levels[source_node_id] = initial_intensity * self.max_flood_level
            
        areas = {n["node_id"]: n.get("metadata", {}).get("area_m2", 100.0) for n in graph_nodes}
        elevations = {n["node_id"]: n.get("coordinates", {}).get("z", 0.0) for n in graph_nodes}
        
        adj: dict[str, list[str]] = {nid: [] for nid in node_ids}
        for edge in graph_edges:
            src = edge.get("source_node_id", "")
            tgt = edge.get("target_node_id", "")
            if not edge.get("is_blocked", False):
                if src in adj: adj[src].append(tgt)
                if tgt in adj: adj[tgt].append(src)
                
        arrival_times = {source_node_id: 0.0}
        dt = 1.0
        
        for step in range(time_steps):
            new_levels = dict(water_levels)
            t_current = step * dt
            
            for node_id in node_ids:
                wl = water_levels[node_id]
                elev = elevations[node_id]
                total_head = wl + elev
                
                for neighbor_id in adj.get(node_id, []):
                    n_wl = water_levels[neighbor_id]
                    n_elev = elevations[neighbor_id]
                    n_total_head = n_wl + n_elev
                    
                    level_diff = total_head - n_total_head
                    if level_diff > 0:
                        flow_rate = self.drainage_coeff * areas[node_id] * level_diff
                        flow_vol = flow_rate * dt
                        
                        # transfer volume
                        actual_flow = min(flow_vol, wl * areas[node_id])
                        if actual_flow > 0:
                            new_levels[node_id] -= actual_flow / areas[node_id]
                            new_levels[neighbor_id] += actual_flow / areas[neighbor_id]
                            
                            if neighbor_id not in arrival_times and new_levels[neighbor_id] > 0.05:
                                arrival_times[neighbor_id] = t_current + dt
                                
            water_levels = new_levels
            
        intensities = {nid: min(1.0, wl / self.max_flood_level) for nid, wl in water_levels.items() if wl > 0.05}
        peak = max(intensities.values()) if intensities else 0.0
        
        return PropagationResult(
            affected_nodes=intensities,
            arrival_times_minutes={k: v for k, v in arrival_times.items() if k in intensities},
            peak_intensity=peak,
            confidence=0.85,
            model_type=self.model_type(),
        )

    def model_type(self) -> str:
        return "PHYSICS_ODES"

    def applicable_hazard_types(self) -> list[str]:
        return ["FLOOD"]

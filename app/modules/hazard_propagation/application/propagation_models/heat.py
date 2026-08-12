from __future__ import annotations
import numpy as np
from typing import Any
from app.core.logging import get_logger
from app.modules.hazard_propagation.application.propagation_models.base import PropagationResult

log = get_logger(__name__)

class HeatPropagationModel:
    """Newton heating/cooling propagation."""
    
    def __init__(self, t_ambient: float = 25.0, max_temp_diff: float = 375.0) -> None:
        self.t_ambient = t_ambient
        self.max_temp_diff = max_temp_diff

    async def propagate(
        self,
        source_node_id: str,
        initial_intensity: float,
        graph_nodes: list[dict],
        graph_edges: list[dict],
        context: dict[str, Any],
        time_steps: int,
    ) -> PropagationResult:
        log.debug(f"HeatPropagationModel.propagate: source={source_node_id}")
        
        if not graph_nodes:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
            
        node_ids = [n["node_id"] for n in graph_nodes]
        temps = {nid: self.t_ambient for nid in node_ids}
        if source_node_id in temps:
            temps[source_node_id] = self.t_ambient + initial_intensity * self.max_temp_diff
            
        adj: dict[str, list[tuple[str, float]]] = {nid: [] for nid in node_ids}
        for edge in graph_edges:
            src = edge.get("source_node_id", "")
            tgt = edge.get("target_node_id", "")
            k_wall = float(edge.get("metadata", {}).get("k_wall", 0.5))
            if src in adj: adj[src].append((tgt, k_wall))
            if tgt in adj: adj[tgt].append((src, k_wall))
            
        arrival_times = {source_node_id: 0.0}
        dt = 1.0
        
        for step in range(time_steps):
            new_temps = dict(temps)
            t_current = step * dt
            
            for node_id in node_ids:
                T = temps[node_id]
                if T <= self.t_ambient + 1.0:
                    continue
                    
                for neighbor_id, k_wall in adj.get(node_id, []):
                    nT = temps[neighbor_id]
                    if T > nT:
                        heat_transfer = k_wall * (T - nT) * dt
                        new_temps[neighbor_id] += heat_transfer
                        new_temps[node_id] -= heat_transfer
                        
                        if neighbor_id not in arrival_times and new_temps[neighbor_id] > self.t_ambient + 10.0:
                            arrival_times[neighbor_id] = t_current + dt
                            
            temps = new_temps
            
        intensities = {}
        for nid, T in temps.items():
            intensity = max(0.0, min(1.0, (T - self.t_ambient) / self.max_temp_diff))
            if intensity > 0.01:
                intensities[nid] = intensity
                
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
        return ["FIRE", "EXPLOSION", "STEAM_LEAK", "HIGH_PRESSURE"]

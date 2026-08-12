from __future__ import annotations
import math
import numpy as np
from typing import Any
from app.core.logging import get_logger
from app.modules.hazard_propagation.application.propagation_models.base import PropagationResult

log = get_logger(__name__)

class SmokePropagationModel:
    """Cellular automata smoke propagation model."""
    
    def __init__(self, base_spread_rate: float = 0.25) -> None:
        self._base_spread_rate = base_spread_rate

    async def propagate(
        self,
        source_node_id: str,
        initial_intensity: float,
        graph_nodes: list[dict],
        graph_edges: list[dict],
        context: dict[str, Any],
        time_steps: int,
    ) -> PropagationResult:
        log.debug(f"SmokePropagationModel.propagate: source={source_node_id}, steps={time_steps}")
        
        if not graph_nodes:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
        
        node_ids = [n["node_id"] for n in graph_nodes]
        intensities = {nid: 0.0 for nid in node_ids}
        if source_node_id in intensities:
            intensities[source_node_id] = initial_intensity * 0.7
        
        arrival_times = {source_node_id: 0.0}
        wind_speed = float(context.get("wind_speed_ms", 0.0))
        wind_dir = float(context.get("wind_direction_deg", 0.0))
        
        adj: dict[str, list[tuple[str, float, str]]] = {nid: [] for nid in node_ids}
        node_coords: dict[str, dict] = {n["node_id"]: n.get("coordinates", {"x": 0.0, "y": 0.0, "z": 0.0}) for n in graph_nodes}
        
        for edge in graph_edges:
            src = edge.get("source_node_id", "")
            tgt = edge.get("target_node_id", "")
            resistance = float(edge.get("resistance", 0.0))
            edge_type = edge.get("edge_type", "ADJACENCY")
            
            if edge.get("is_blocked", False):
                resistance = 1.0
            if edge_type == "VENTILATION":
                resistance = max(0.0, resistance - 0.4)
                
            if src in adj:
                adj[src].append((tgt, resistance, edge_type))
            if tgt in adj:
                adj[tgt].append((src, resistance, edge_type))
                
        dt = 1.0
        for step in range(time_steps):
            new_intensities = dict(intensities)
            t_current = step * dt
            
            for node_id, node_intensity in intensities.items():
                if node_intensity < 0.02:
                    continue
                
                src_coords = node_coords.get(node_id, {"x": 0.0, "y": 0.0, "z": 0.0})
                
                for neighbor_id, resistance, edge_type in adj.get(node_id, []):
                    if resistance >= 0.99:
                        continue
                    
                    tgt_coords = node_coords.get(neighbor_id, {"x": 0.0, "y": 0.0, "z": 0.0})
                    
                    dz = tgt_coords.get("z", 0.0) - src_coords.get("z", 0.0)
                    buoyancy_factor = 1.0 + (dz * 0.1) if dz > 0 else max(0.2, 1.0 + (dz * 0.2))
                    
                    dx = tgt_coords.get("x", 0.0) - src_coords.get("x", 0.0)
                    dy = tgt_coords.get("y", 0.0) - src_coords.get("y", 0.0)
                    edge_len = math.sqrt(dx**2 + dy**2) or 1.0
                    wind_rad = math.radians(wind_dir)
                    wind_x, wind_y = math.cos(wind_rad), math.sin(wind_rad)
                    cos_angle = (dx * wind_x + dy * wind_y) / edge_len
                    wind_factor = 1.0 + (wind_speed * max(-0.2, cos_angle)) / 8.0
                    
                    spread_rate = self._base_spread_rate * wind_factor * buoyancy_factor * (1.0 - resistance)
                    spread = node_intensity * spread_rate * dt
                    
                    new_intensity = min(1.0, new_intensities.get(neighbor_id, 0.0) + spread)
                    new_intensities[neighbor_id] = new_intensity
                    
                    if neighbor_id not in arrival_times and new_intensity > 0.05:
                        arrival_times[neighbor_id] = t_current + dt
                        
            intensities = new_intensities
            
        affected = {nid: v for nid, v in intensities.items() if v > 0.01}
        peak = max(affected.values()) if affected else 0.0
        
        return PropagationResult(
            affected_nodes=affected,
            arrival_times_minutes={k: v for k, v in arrival_times.items() if k in affected},
            peak_intensity=peak,
            confidence=0.8,
            model_type=self.model_type(),
        )

    def model_type(self) -> str:
        return "CELLULAR_AUTOMATA"

    def applicable_hazard_types(self) -> list[str]:
        return ["SMOKE", "FIRE"]

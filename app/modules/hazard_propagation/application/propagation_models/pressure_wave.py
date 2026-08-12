from __future__ import annotations
import math
from typing import Any
from app.core.logging import get_logger
from app.modules.hazard_propagation.application.propagation_models.base import PropagationResult

log = get_logger(__name__)

class PressureWavePropagationModel:
    """Hopkinson-Cranz blast wave model."""
    
    def __init__(self) -> None:
        pass

    async def propagate(
        self,
        source_node_id: str,
        initial_intensity: float,
        graph_nodes: list[dict],
        graph_edges: list[dict],
        context: dict[str, Any],
        time_steps: int,
    ) -> PropagationResult:
        log.debug(f"PressureWavePropagationModel.propagate: source={source_node_id}")
        
        if not graph_nodes:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
            
        source_node = next((n for n in graph_nodes if n["node_id"] == source_node_id), None)
        if not source_node:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
            
        E = initial_intensity * 1e9  # TNT equivalent Joules proxy
        
        src_coords = source_node.get("coordinates", {"x": 0.0, "y": 0.0, "z": 0.0})
        src_x, src_y, src_z = src_coords.get("x", 0.0), src_coords.get("y", 0.0), src_coords.get("z", 0.0)
        
        intensities = {}
        arrival_times = {}
        
        # Simple barrier reduction simulation based on graph
        barrier_reduction = {}
        for edge in graph_edges:
            res = float(edge.get("resistance", 0.0))
            if res > 0:
                tgt = edge.get("target_node_id", "")
                barrier_reduction[tgt] = max(barrier_reduction.get(tgt, 1.0), 1.0 - res)
                
        for node in graph_nodes:
            nid = node["node_id"]
            if nid == source_node_id:
                intensities[nid] = 1.0
                arrival_times[nid] = 0.0
                continue
                
            tgt_coords = node.get("coordinates", {"x": 0.0, "y": 0.0, "z": 0.0})
            dx = tgt_coords.get("x", 0.0) - src_x
            dy = tgt_coords.get("y", 0.0) - src_y
            dz = tgt_coords.get("z", 0.0) - src_z
            r = math.sqrt(dx**2 + dy**2 + dz**2)
            
            if r <= 0:
                continue
                
            Z = r / (E**(1/3))
            
            if Z < 0.5:
                overpressure = 1.0
            elif Z <= 1.0:
                overpressure = 0.7
            elif Z <= 3.0:
                overpressure = 0.35
            else:
                overpressure = 0.1
                
            reduction = barrier_reduction.get(nid, 1.0)
            intensity = min(1.0, overpressure * reduction)
            
            if intensity > 0.01:
                intensities[nid] = intensity
                arrival_times[nid] = r / 343.0  # Speed of sound proxy in seconds
                
        peak = max(intensities.values()) if intensities else 0.0
        
        return PropagationResult(
            affected_nodes=intensities,
            arrival_times_minutes={k: v / 60.0 for k, v in arrival_times.items()},
            peak_intensity=peak,
            confidence=0.8,
            model_type=self.model_type(),
        )

    def model_type(self) -> str:
        return "PHYSICS_ODES"

    def applicable_hazard_types(self) -> list[str]:
        return ["EXPLOSION", "HIGH_PRESSURE"]

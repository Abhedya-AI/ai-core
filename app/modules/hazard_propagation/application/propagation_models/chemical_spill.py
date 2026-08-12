from __future__ import annotations
import math
import numpy as np
from typing import Any
from app.core.logging import get_logger
from app.modules.hazard_propagation.application.propagation_models.base import PropagationResult

log = get_logger(__name__)

class ChemicalSpillModel:
    """Chemical spill radial spread model."""
    
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
        log.debug(f"ChemicalSpillModel.propagate: source={source_node_id}")
        
        if not graph_nodes:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
            
        source_node = next((n for n in graph_nodes if n["node_id"] == source_node_id), None)
        if not source_node:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
            
        Volume = initial_intensity * 1000.0  # liters proxy
        height = 0.05  # 5 cm pool height
        radius = math.sqrt(Volume / (math.pi * height))
        
        Volume_flow = Volume / max(1, time_steps)
        spreading_rate = Volume_flow / (math.pi * max(0.1, radius) * height)
        
        src_coords = source_node.get("coordinates", {"x": 0.0, "y": 0.0})
        src_x, src_y = src_coords.get("x", 0.0), src_coords.get("y", 0.0)
        
        intensities = {}
        arrival_times = {}
        
        for node in graph_nodes:
            nid = node["node_id"]
            if nid == source_node_id:
                intensities[nid] = initial_intensity
                arrival_times[nid] = 0.0
                continue
                
            tgt_coords = node.get("coordinates", {"x": 0.0, "y": 0.0})
            dx = tgt_coords.get("x", 0.0) - src_x
            dy = tgt_coords.get("y", 0.0) - src_y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist <= radius:
                # Intensity decreases with distance from source
                intensity = min(1.0, initial_intensity * (1.0 - dist / radius))
                if intensity > 0.01:
                    intensities[nid] = intensity
                    arrival_times[nid] = dist / max(0.01, spreading_rate)
                    
        peak = max(intensities.values()) if intensities else 0.0
        
        return PropagationResult(
            affected_nodes=intensities,
            arrival_times_minutes=arrival_times,
            peak_intensity=peak,
            confidence=0.8,
            model_type=self.model_type(),
        )

    def model_type(self) -> str:
        return "PHYSICS_ODES"

    def applicable_hazard_types(self) -> list[str]:
        return ["CHEMICAL_SPILL"]

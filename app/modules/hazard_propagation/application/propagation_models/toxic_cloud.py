from __future__ import annotations
import math
import numpy as np
from typing import Any
from app.core.logging import get_logger
from app.modules.hazard_propagation.application.propagation_models.base import PropagationResult

log = get_logger(__name__)

class ToxicCloudModel:
    """Toxic cloud dispersion and dose accumulation model."""
    
    def __init__(self, idlh_ppm: float = 500.0) -> None:
        self.idlh_ppm = idlh_ppm

    async def propagate(
        self,
        source_node_id: str,
        initial_intensity: float,
        graph_nodes: list[dict],
        graph_edges: list[dict],
        context: dict[str, Any],
        time_steps: int,
    ) -> PropagationResult:
        log.debug(f"ToxicCloudModel.propagate: source={source_node_id}")
        
        if not graph_nodes:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
            
        source_node = next((n for n in graph_nodes if n["node_id"] == source_node_id), None)
        if not source_node:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
            
        u = max(0.1, float(context.get("wind_speed_ms", 1.0)))
        wind_dir = float(context.get("wind_direction_deg", 0.0))
        Q = initial_intensity * 1000.0
        
        src_coords = source_node.get("coordinates", {"x": 0.0, "y": 0.0})
        src_x, src_y = src_coords.get("x", 0.0), src_coords.get("y", 0.0)
        
        intensities = {}
        arrival_times = {}
        dt = 1.0
        
        for node in graph_nodes:
            nid = node["node_id"]
            if nid == source_node_id:
                intensities[nid] = 1.0
                arrival_times[nid] = 0.0
                continue
                
            tgt_coords = node.get("coordinates", {"x": 0.0, "y": 0.0})
            dx = tgt_coords.get("x", 0.0) - src_x
            dy = tgt_coords.get("y", 0.0) - src_y
            
            wind_rad = math.radians(wind_dir)
            
            x_downwind = dx * math.cos(wind_rad) + dy * math.sin(wind_rad)
            y_crosswind = -dx * math.sin(wind_rad) + dy * math.cos(wind_rad)
            
            if x_downwind <= 0:
                continue
                
            x_val = max(1.0, x_downwind)
            sigma_y = 0.22 * (x_val ** 0.89)
            sigma_z = 0.16 * (x_val ** 0.82)
            
            C = (Q / (2 * math.pi * sigma_y * sigma_z * u)) * math.exp(-(y_crosswind**2) / (2 * sigma_y**2))
            
            # Dose accumulation
            dose = C * dt * time_steps
            if dose > 1e-9:
                Pr = max(0.0, min(1.0, -8.3 + 1.0 * math.log(dose + 1e-9)))
                intensity = min(1.0, dose / (self.idlh_ppm * 30))
                
                if intensity > 0.01:
                    intensities[nid] = intensity
                    concentration_rate = C * dt
                    time_to_unsafe = self.idlh_ppm / max(1e-9, concentration_rate)
                    arrival_times[nid] = time_to_unsafe
                
        peak = max(intensities.values()) if intensities else 0.0
        
        return PropagationResult(
            affected_nodes=intensities,
            arrival_times_minutes=arrival_times,
            peak_intensity=peak,
            confidence=0.75,
            model_type=self.model_type(),
        )

    def model_type(self) -> str:
        return "GAUSSIAN_PLUME"

    def applicable_hazard_types(self) -> list[str]:
        return ["TOXIC_GAS", "CHEMICAL_SPILL"]

from __future__ import annotations
import math
from app.core.logging import get_logger

log = get_logger(__name__)

class ArrivalTimeEstimator:
    """Estimates arrival time of hazards."""

    def __init__(self) -> None:
        pass

    def estimate_arrival_time(self, source_id: str, target_id: str, propagation_speed_ms: float, path_distance_meters: float, edge_resistance: float) -> float:
        """Estimate arrival time in minutes."""
        if target_id == source_id:
            return 0.0
            
        speed = max(0.01, propagation_speed_ms)
        t_seconds = (path_distance_meters / speed) * (1.0 + edge_resistance)
        return t_seconds / 60.0

    def compute_all_arrival_times(self, source_id: str, nodes: list[str], distances: dict[str, float], propagation_speed: float, resistances: dict[str, float]) -> dict[str, float]:
        """Compute arrival time for all given nodes."""
        arrival_times = {}
        for node in nodes:
            dist = distances.get(node, 0.0)
            res = resistances.get(node, 0.0)
            arrival_times[node] = self.estimate_arrival_time(source_id, node, propagation_speed, dist, res)
        return arrival_times

    def estimate_time_to_critical(self, initial_intensity: float, growth_rate: float, critical_threshold: float = 0.8) -> float:
        """Estimate time to reach critical threshold."""
        if initial_intensity >= critical_threshold:
            return 0.0
            
        i0 = max(1e-9, initial_intensity)
        thresh = max(1e-9, critical_threshold)
        gr = max(1e-9, growth_rate)
        
        t = math.log(thresh / i0) / gr
        return max(0.0, t)

    def compute_arrival_time_confidence(self, distance: float, wind_speed: float, barrier_resistance: float) -> float:
        """Compute confidence in arrival time estimation."""
        conf = 0.9 - (distance / 1000.0) - (barrier_resistance * 0.3) + (wind_speed * 0.05)
        return max(0.1, min(1.0, conf))

    def rank_nodes_by_arrival(self, arrival_times: dict[str, float]) -> list[tuple[str, float]]:
        """Rank nodes by arrival time ascending."""
        return sorted(arrival_times.items(), key=lambda x: x[1])

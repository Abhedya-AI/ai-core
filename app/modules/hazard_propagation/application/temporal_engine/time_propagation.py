from __future__ import annotations
from app.core.logging import get_logger

log = get_logger(__name__)

class TemporalPropagationEngine:
    """Engine for time-based hazard propagation."""

    def __init__(self, dt_minutes: float = 1.0) -> None:
        self._dt_minutes = dt_minutes

    def advance_time_step(self, node_intensities: dict[str, float], graph_edges: list[dict], dt: float) -> dict[str, float]:
        """Advance simulation by one time step."""
        new_intensities = node_intensities.copy()
        
        for edge in graph_edges:
            src = edge.get("source")
            tgt = edge.get("target")
            res = edge.get("resistance", 0.0)
            
            if src in node_intensities and tgt in new_intensities:
                src_i = node_intensities[src]
                if src_i > 0:
                    diff = src_i * (1.0 - res) * 0.1 * dt
                    new_intensities[tgt] += diff
                    
        for k, v in new_intensities.items():
            new_intensities[k] = max(0.0, min(1.0, v))
            
        return new_intensities

    def run_time_series(self, initial_intensities: dict[str, float], graph_edges: list[dict], total_minutes: int) -> list[dict]:
        """Run time series simulation."""
        series = []
        current_i = initial_intensities.copy()
        t = 0.0
        
        while t <= total_minutes:
            series.append({"t_minutes": t, "intensities": current_i.copy()})
            current_i = self.advance_time_step(current_i, graph_edges, self._dt_minutes)
            t += self._dt_minutes
            
        return series

    def find_stabilization_time(self, time_series: list[dict], stability_threshold: float = 0.01) -> float:
        """Find time when max intensity change < threshold."""
        if not time_series or len(time_series) < 2:
            return 0.0
            
        for i in range(1, len(time_series)):
            prev = time_series[i-1]["intensities"]
            curr = time_series[i]["intensities"]
            
            max_change = 0.0
            for k, v in curr.items():
                change = abs(v - prev.get(k, 0.0))
                max_change = max(max_change, change)
                
            if max_change < stability_threshold:
                return time_series[i]["t_minutes"]
                
        return time_series[-1]["t_minutes"]

    def compute_time_to_peak(self, time_series: list[dict], node_id: str) -> float:
        """Compute time to peak intensity for a node."""
        if not time_series:
            return 0.0
            
        max_i = -1.0
        peak_t = 0.0
        
        for step in time_series:
            i = step["intensities"].get(node_id, 0.0)
            if i > max_i:
                max_i = i
                peak_t = step["t_minutes"]
                
        return peak_t

    def compute_duration_above_threshold(self, time_series: list[dict], node_id: str, threshold: float) -> float:
        """Compute duration node intensity is above threshold."""
        if not time_series or len(time_series) < 2:
            return 0.0
            
        duration = 0.0
        for i in range(1, len(time_series)):
            prev = time_series[i-1]
            curr = time_series[i]
            
            i_prev = prev["intensities"].get(node_id, 0.0)
            i_curr = curr["intensities"].get(node_id, 0.0)
            
            if i_prev > threshold or i_curr > threshold:
                duration += (curr["t_minutes"] - prev["t_minutes"])
                
        return duration

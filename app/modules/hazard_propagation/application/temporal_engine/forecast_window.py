from __future__ import annotations
import math
from app.core.logging import get_logger

log = get_logger(__name__)

class PropagationForecastWindow:
    """Forecasting windows for propagation prediction."""

    def __init__(self, horizons_minutes: list[int] | None = None) -> None:
        self.horizons = horizons_minutes or [5, 15, 30, 60, 360]

    def generate_forecast_windows(self, current_intensities: dict[str, float], graph_edges: list[dict], growth_decay: "HazardGrowthDecayModel") -> dict[str, dict]:
        """Generate intensity forecasts for each horizon."""
        forecasts = {}
        current = current_intensities.copy()
        
        # Simple step-wise forward pass
        max_horizon = max(self.horizons) if self.horizons else 0
        dt = 1.0
        t = 0.0
        
        while t <= max_horizon:
            # Check if this time is a horizon
            for h in self.horizons:
                if abs(t - float(h)) < (dt / 2.0):
                    forecasts[f"{h}m"] = current.copy()
                    
            # Step forward
            new_intensities = current.copy()
            for k, v in current.items():
                new_intensities[k] = growth_decay.compute_growth(v, dt)
                
            for edge in graph_edges:
                src = edge.get("source")
                tgt = edge.get("target")
                if src in current and tgt in new_intensities:
                    diff = current[src] * 0.1 * dt
                    new_intensities[tgt] = min(1.0, new_intensities[tgt] + diff)
                    
            current = new_intensities
            t += dt
            
        return forecasts

    def estimate_containment_probability(self, intensity: float, containment_resources: int, time_minutes: float) -> float:
        """Estimate probability of containing hazard."""
        p = (containment_resources / max(1.0, intensity * 10.0)) * math.exp(-intensity * time_minutes / 60.0)
        return max(0.0, min(1.0, p))

    def predict_peak_affected_zones(self, forecasts: dict[str, dict], threshold: float = 0.1) -> dict[str, int]:
        """Count nodes above threshold for each horizon."""
        peaks = {}
        for horizon, intensities in forecasts.items():
            count = sum(1 for v in intensities.values() if v >= threshold)
            peaks[horizon] = count
        return peaks

    def compute_forecast_confidence(self, horizon_minutes: int, data_quality: float = 0.8) -> float:
        """Compute confidence in forecast based on time horizon."""
        conf = data_quality * math.exp(-0.001 * horizon_minutes)
        return max(0.1, min(1.0, conf))

    def build_forecast_dict(self, propagation_id: str, time_series: list[dict], horizons_minutes: list[int]) -> dict:
        """Extract intensities for specified horizons from time series."""
        forecast_dict = {"propagation_id": propagation_id, "forecasts": {}}
        if not time_series:
            return forecast_dict
            
        for h in horizons_minutes:
            closest_step = min(time_series, key=lambda x: abs(x["t_minutes"] - h))
            forecast_dict["forecasts"][f"{h}m"] = closest_step["intensities"]
            
        return forecast_dict

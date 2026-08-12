from __future__ import annotations
import uuid
from datetime import datetime, timezone
import math
import numpy as np

from app.core.logging import get_logger
log = get_logger(__name__)

class EquipmentUtilizationForecaster:
    """Forecaster for equipment utilization based on health and availability."""

    def __init__(self) -> None:
        pass

    async def forecast_utilization(self, equipment_ids: list[str], current_utilization: dict[str, float], health_scores: dict[str, float], horizon_hours: int) -> dict:
        """Forecast utilization for a list of equipment."""
        log.info(f"Forecasting utilization for {len(equipment_ids)} equipment items over {horizon_hours}h")
        
        utilization_forecast = {}
        availability_probability = {}
        maintenance_impact = {}
        bottleneck_equipment = []
        
        for eq_id in equipment_ids:
            curr_util = current_utilization.get(eq_id, 0.5)
            health = health_scores.get(eq_id, 1.0)
            
            avail_prob = self._compute_availability_probability(health, curr_util)
            availability_probability[eq_id] = avail_prob
            
            m_impact = (1.0 - health) * curr_util * 0.5
            maintenance_impact[eq_id] = m_impact
            
            forecasts = {}
            for h in range(1, horizon_hours + 1):
                # Exponential decay of utilization as health degrades over horizon
                decay_rate = 0.01 * (1.0 - health)
                proj_util = curr_util * math.exp(-decay_rate * h)
                forecasts[f"+{h}h"] = float(np.clip(proj_util, 0.0, 1.0))
                
            utilization_forecast[eq_id] = forecasts
            
            # Bottleneck identified if utilization is high but availability is low
            if curr_util > 0.8 and avail_prob < 0.6:
                bottleneck_equipment.append(eq_id)
                
        return {
            "utilization_forecast": utilization_forecast,
            "bottleneck_equipment": bottleneck_equipment,
            "availability_probability": availability_probability,
            "maintenance_impact": maintenance_impact
        }

    def _compute_availability_probability(self, health_score: float, utilization: float) -> float:
        """Compute the probability that equipment is available given its health and current utilization."""
        # High utilization accelerates the impact of poor health
        base_prob = health_score
        penalty = utilization * (1.0 - health_score) * 0.5
        return float(np.clip(base_prob - penalty, 0.0, 1.0))

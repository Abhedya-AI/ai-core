from __future__ import annotations
import uuid
from datetime import datetime, timezone
import numpy as np

from app.core.logging import get_logger
log = get_logger(__name__)

class ProductionImpactForecaster:
    """Forecaster for predicting production and capacity impacts."""

    def __init__(self, target_capacity_pct: float = 0.9) -> None:
        self.target_capacity_pct = target_capacity_pct

    async def forecast_production_impact(self, equipment_health_scores: dict[str, float], worker_availability: dict[str, int], horizon_hours: int) -> dict:
        """Forecast production capacity based on equipment health and worker availability."""
        log.info(f"Forecasting production impact over {horizon_hours}h")
        
        capacity_pct = {}
        output_loss = {}
        
        # Determine baseline capacities
        base_eq_cap = self._compute_equipment_capacity(equipment_health_scores)
        
        total_loss = 0.0
        min_cap = 1.0
        bottleneck = 'NONE'
        
        for h in range(1, horizon_hours + 1):
            label = f"+{h}h"
            
            # Extract worker availability for this hour if available, else assume last known
            workers = worker_availability.get(label, 10)
            worker_cap = self._compute_worker_capacity(workers, required_workers=10)
            
            # Project combined capacity
            cap = self._project_capacity(base_eq_cap, worker_cap, h)
            capacity_pct[label] = cap
            
            loss = max(0.0, self.target_capacity_pct - cap)
            output_loss[label] = loss
            total_loss += loss
            
            if cap < min_cap:
                min_cap = cap
                if worker_cap < base_eq_cap:
                    bottleneck = 'WORKER'
                elif base_eq_cap < worker_cap:
                    bottleneck = 'EQUIPMENT'
                    
        recovery_time = 0.0
        if min_cap < self.target_capacity_pct:
            recovery_time = float(horizon_hours * 1.5) # Simple heuristic
            
        economic_impact = float(np.clip(total_loss / max(1, horizon_hours), 0.0, 1.0))
        
        return {
            "production_capacity_pct": capacity_pct,
            "output_loss_pct": output_loss,
            "bottleneck_factor": bottleneck,
            "recovery_time_hours": recovery_time,
            "economic_impact_score": economic_impact
        }

    def _compute_equipment_capacity(self, health_scores: dict[str, float]) -> float:
        """Compute aggregate equipment capacity."""
        if not health_scores:
            return 1.0
        # Assume series reliability model (bottleneck is the weakest link)
        return float(min(health_scores.values()))

    def _compute_worker_capacity(self, available_workers: int, required_workers: int = 10) -> float:
        """Compute capacity constrained by worker availability."""
        if required_workers <= 0:
            return 1.0
        return float(np.clip(available_workers / required_workers, 0.0, 1.0))

    def _project_capacity(self, equipment_cap: float, worker_cap: float, t: int) -> float:
        """Project capacity over time (assuming slight degradation)."""
        base = min(equipment_cap, worker_cap)
        # Small decay over horizon
        decay = np.exp(-0.005 * t)
        return float(np.clip(base * decay, 0.0, 1.0))

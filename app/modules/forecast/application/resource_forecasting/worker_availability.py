from __future__ import annotations
import uuid
from datetime import datetime, timezone
import math

from app.core.logging import get_logger
log = get_logger(__name__)

class WorkerAvailabilityForecaster:
    """Forecaster for worker availability considering shifts and fatigue."""

    def __init__(self, shift_duration_hours: float = 8.0, fatigue_factor: float = 0.1) -> None:
        self.shift_duration_hours = shift_duration_hours
        self.fatigue_factor = fatigue_factor

    async def forecast_availability(self, worker_count: int, current_hour: int, horizon_hours: int) -> dict:
        """Forecast available workers over the given horizon."""
        log.info(f"Forecasting availability for {worker_count} workers over {horizon_hours}h")
        
        available_workers = {}
        fatigue_risk_score = {}
        
        shift_changes = self._project_shift_patterns(current_hour, horizon_hours)
        safety_demand = {}
        
        active_workers = worker_count
        
        for h in range(1, horizon_hours + 1):
            target_hour = (current_hour + h) % 24
            label = f"+{h}h"
            
            # Simple simulation: assume some workers drop out due to fatigue or shift end
            hours_on_shift = h % self.shift_duration_hours
            if hours_on_shift == 0:
                hours_on_shift = self.shift_duration_hours
                
            fatigue = self._compute_fatigue_index(hours_on_shift)
            fatigue_risk_score[label] = fatigue
            
            # Adjust workers based on fatigue (mock implementation)
            effective_workers = int(worker_count * (1.0 - (fatigue * 0.2)))
            available_workers[label] = effective_workers
            
            safety_demand[label] = max(1, int(effective_workers * 0.1))
            
        medical_readiness = float(np.clip(1.0 - (sum(fatigue_risk_score.values()) / max(1, len(fatigue_risk_score))), 0.0, 1.0)) if fatigue_risk_score else 1.0
        
        return {
            "available_workers": available_workers,
            "fatigue_risk_score": fatigue_risk_score,
            "shift_changes": shift_changes,
            "safety_personnel_demand": safety_demand,
            "medical_response_readiness": medical_readiness
        }

    def _compute_fatigue_index(self, hours_on_shift: float) -> float:
        """Compute fatigue index using a sigmoid function."""
        # Sigmoid centered around 6 hours
        midpoint = 6.0
        steepness = self.fatigue_factor * 10
        fatigue = 1 / (1 + math.exp(-steepness * (hours_on_shift - midpoint)))
        return float(fatigue)

    def _project_shift_patterns(self, current_hour: int, horizon_hours: int) -> list[dict]:
        """Project shift changes based on current hour and horizon."""
        shifts = []
        for h in range(1, horizon_hours + 1):
            future_hr = (current_hour + h) % 24
            if future_hr % int(self.shift_duration_hours) == 0:
                shifts.append({
                    "hour": h,
                    "incoming": 10,
                    "outgoing": 10
                })
        return shifts

import numpy as np

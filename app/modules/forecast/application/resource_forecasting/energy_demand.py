from __future__ import annotations
import uuid
from datetime import datetime, timezone
import math
import numpy as np

from app.core.logging import get_logger
log = get_logger(__name__)

class EnergyDemandForecaster:
    """Forecaster for energy demand based on utilization and worker presence."""

    def __init__(self, base_consumption_kw: float = 1000.0) -> None:
        self.base_consumption_kw = base_consumption_kw

    async def forecast_energy(self, equipment_utilization: dict[str, float], worker_count: int, horizon_hours: int) -> dict:
        """Forecast energy, water, and fuel demand."""
        log.info(f"Forecasting energy demand over {horizon_hours}h")
        
        power_consumption_kwh = {}
        water_usage_liters = {}
        fuel_demand_liters = {}
        
        current_hour = datetime.now(timezone.utc).hour
        # Assume today is a generic weekday
        day_of_week = datetime.now(timezone.utc).weekday()
        
        total_utilization = sum(equipment_utilization.values())
        eq_count = len(equipment_utilization)
        
        peak_demand_hours = []
        peak_threshold = self.base_consumption_kw * 1.5
        
        for h in range(1, horizon_hours + 1):
            hr = (current_hour + h) % 24
            label = f"+{h}h"
            
            # Simple regression for power based on utilization + workers
            eq_power = self._estimate_equipment_power(total_utilization / max(1, eq_count), eq_count)
            worker_power = worker_count * 2.0  # 2 kW per worker approx
            
            base_power = self.base_consumption_kw + eq_power + worker_power
            
            # Apply seasonality
            power = self._add_operational_seasonality(base_power, hr, day_of_week)
            power_consumption_kwh[label] = float(power)
            
            if power > peak_threshold:
                peak_demand_hours.append(h)
                
            # Water and fuel correlated with power
            water_usage_liters[label] = float(power * 10.0)
            fuel_demand_liters[label] = float(power * 2.5)
            
        efficiency_score = float(np.clip(1.0 - (len(peak_demand_hours) / max(1, horizon_hours)), 0.0, 1.0))
        
        return {
            "power_consumption_kwh": power_consumption_kwh,
            "water_usage_liters": water_usage_liters,
            "fuel_demand_liters": fuel_demand_liters,
            "peak_demand_hours": peak_demand_hours,
            "efficiency_score": efficiency_score
        }

    def _estimate_equipment_power(self, utilization: float, count: int) -> float:
        """Estimate power consumption from equipment."""
        return utilization * count * 50.0  # Assumed 50kW max per eq

    def _add_operational_seasonality(self, base: float, hour_of_day: int, day_of_week: int) -> float:
        """Add time-of-day and day-of-week seasonality to demand."""
        # Weekend reduction
        weekend_factor = 0.6 if day_of_week >= 5 else 1.0
        
        # Diurnal pattern
        if 8 <= hour_of_day <= 18:
            hour_factor = 1.2 # peak hours
        elif 0 <= hour_of_day <= 5:
            hour_factor = 0.5 # night shift
        else:
            hour_factor = 1.0 # shoulder hours
            
        return base * weekend_factor * hour_factor

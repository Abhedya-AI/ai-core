from __future__ import annotations
import uuid
from datetime import datetime, timezone
import math
import numpy as np

from app.core.logging import get_logger
log = get_logger(__name__)

class TemperatureForecaster:
    """Forecaster for zone temperature based on heat sources and ambient conditions."""

    def __init__(self, thermal_mass: float = 1.0) -> None:
        self.thermal_mass = thermal_mass

    async def forecast_temperature(self, zone_id: str, current_temp: float, equipment_heat_watts: float, ambient_temp: float, horizon_hours: int) -> dict:
        """Forecast temperature changes."""
        log.info(f"Forecasting temperature for {zone_id} over {horizon_hours}h")
        
        forecast = {}
        risk = {}
        
        # Simple heat stress threshold
        stress_threshold = 35.0
        
        max_temp = current_temp
        
        for h in range(1, horizon_hours + 1):
            t_val = self._newton_cooling(current_temp, ambient_temp, equipment_heat_watts, self.thermal_mass, h)
            label = f"+{h}h"
            forecast[label] = t_val
            
            if t_val > stress_threshold:
                risk[label] = min(1.0, (t_val - stress_threshold) / 10.0)
            else:
                risk[label] = 0.0
                
            max_temp = max(max_temp, t_val)
            
        cooling_kw = max(0.0, (max_temp - ambient_temp) * self.thermal_mass * 0.5) / 1000.0
        overheating_prob = float(np.clip((max_temp - stress_threshold) / 15.0, 0.0, 1.0)) if max_temp > stress_threshold else 0.0
        
        return {
            "temperature_forecast": forecast,
            "heat_stress_risk": risk,
            "cooling_requirement_kw": float(cooling_kw),
            "overheating_probability": overheating_prob
        }

    def _newton_cooling(self, T0: float, T_ambient: float, heat_watts: float, thermal_mass: float, t: float) -> float:
        """
        Newton's law of cooling with a constant heat source.
        dT/dt = k*(T_ambient - T) + Q/C
        T(t) = T_ambient + Q/(k*C) + (T0 - T_ambient - Q/(k*C)) * exp(-k*t)
        """
        k = 0.1 / max(0.1, thermal_mass)
        Q_C = (heat_watts / 1000.0) / max(0.1, thermal_mass)
        
        T_eq = T_ambient + (Q_C / k)
        T_t = T_eq + (T0 - T_eq) * math.exp(-k * t)
        
        return float(T_t)

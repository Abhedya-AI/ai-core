from __future__ import annotations
import uuid
from datetime import datetime, timezone
import math

from app.core.logging import get_logger
log = get_logger(__name__)

class GasAccumulationForecaster:
    """Forecaster for gas accumulation in physical zones."""

    def __init__(self, ventilation_rate: float = 0.1, diffusion_coef: float = 0.05) -> None:
        self.ventilation_rate = ventilation_rate
        self.diffusion_coef = diffusion_coef

    async def forecast_gas(self, zone_id: str, current_concentration: float, source_rate: float, horizon_hours: int) -> dict:
        """Forecast gas concentration over time."""
        log.info(f"Forecasting gas accumulation in {zone_id} over {horizon_hours}h")
        
        concentration_forecast = {}
        threshold_exceedance_risk = {}
        
        hazard_threshold = 100.0 # ppm generic
        evac_threshold = 200.0 # ppm
        
        evacuation_time = None
        safe_duration = float(horizon_hours)
        
        for h in range(1, horizon_hours + 1):
            c_val = self._solve_ode(current_concentration, source_rate, self.ventilation_rate, h)
            label = f"+{h}h"
            concentration_forecast[label] = c_val
            
            risk = 0.0
            if c_val >= hazard_threshold:
                risk = min(1.0, (c_val - hazard_threshold) / 50.0)
            threshold_exceedance_risk[label] = risk
            
            if evacuation_time is None and c_val >= evac_threshold:
                evacuation_time = float(h)
                safe_duration = float(h - 1)
                
        rec = "NORMAL"
        if evacuation_time is not None:
            rec = "IMMEDIATE_EVACUATION"
        elif source_rate > self.ventilation_rate * current_concentration:
            rec = "INCREASE_VENTILATION"
            
        return {
            "concentration_forecast": concentration_forecast,
            "threshold_exceedance_risk": threshold_exceedance_risk,
            "estimated_safe_duration_hours": safe_duration,
            "ventilation_recommendation": rec,
            "evacuation_threshold_hours": evacuation_time
        }

    def _solve_ode(self, c0: float, source_rate: float, ventilation: float, t: float) -> float:
        """
        Solve dC/dt = source_rate - ventilation * C
        C(t) = (C0 - Ceq)*exp(-v*t) + Ceq
        where Ceq = source_rate / ventilation
        """
        if ventilation <= 0:
            return c0 + source_rate * t
            
        c_eq = source_rate / ventilation
        c_t = (c0 - c_eq) * math.exp(-ventilation * t) + c_eq
        return max(0.0, float(c_t))

from __future__ import annotations
import uuid
from datetime import datetime, timezone
import numpy as np

from app.core.logging import get_logger
log = get_logger(__name__)

class AirQualityForecaster:
    """Forecaster for Air Quality Index (AQI), dust, and smoke."""

    def __init__(self) -> None:
        self.decay_factor = 0.05
        self.accumulation_factor = 0.02

    async def forecast_air_quality(self, zone_id: str, current_aqi: float, dust_ppm: float, smoke_ppm: float, horizon_hours: int) -> dict:
        """Forecast AQI and particulates."""
        log.info(f"Forecasting air quality for {zone_id} over {horizon_hours}h")
        
        aqi_forecast = {}
        dust_forecast = {}
        smoke_forecast = {}
        risk_level = {}
        
        max_aqi = current_aqi
        
        for h in range(1, horizon_hours + 1):
            label = f"+{h}h"
            
            # Simple exponential smoothing/decay model
            # Assuming without source, it decays. If high dust/smoke, it accumulates.
            source_term = (dust_ppm + smoke_ppm) * self.accumulation_factor
            
            new_aqi = current_aqi * np.exp(-self.decay_factor * h) + source_term * h
            new_dust = dust_ppm * np.exp(-self.decay_factor * h * 1.5)
            new_smoke = smoke_ppm * np.exp(-self.decay_factor * h * 2.0)
            
            aqi_forecast[label] = float(new_aqi)
            dust_forecast[label] = float(new_dust)
            smoke_forecast[label] = float(new_smoke)
            
            risk_level[label] = self._classify_health_risk(new_aqi)
            
            max_aqi = max(max_aqi, new_aqi)
            
        ppe = self._recommend_ppe(max_aqi, dust_ppm, smoke_ppm)
        evac_risk = float(np.clip((max_aqi - 300) / 200.0, 0.0, 1.0)) if max_aqi > 300 else 0.0
        
        return {
            "aqi_forecast": aqi_forecast,
            "dust_forecast": dust_forecast,
            "smoke_forecast": smoke_forecast,
            "health_risk_level": risk_level,
            "ppe_recommendation": ppe,
            "evacuation_risk": evac_risk
        }

    def _classify_health_risk(self, aqi: float) -> str:
        """Classify health risk based on AQI."""
        if aqi <= 50:
            return 'GOOD'
        elif aqi <= 150:
            return 'MODERATE'
        elif aqi <= 300:
            return 'UNHEALTHY'
        else:
            return 'HAZARDOUS'

    def _recommend_ppe(self, aqi: float, dust: float, smoke: float) -> str:
        """Recommend Personal Protective Equipment."""
        if aqi > 300 or smoke > 50.0:
            return "SCBA or Full-Face Respirator"
        elif aqi > 150 or dust > 100.0:
            return "N95 / P100 Mask"
        elif aqi > 100:
            return "Surgical Mask (Optional)"
        return "None required"

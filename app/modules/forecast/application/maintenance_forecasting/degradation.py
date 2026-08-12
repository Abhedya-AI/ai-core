from __future__ import annotations
import uuid
from datetime import datetime, timezone
import numpy as np

from app.core.logging import get_logger
log = get_logger(__name__)

class DegradationForecaster:
    """Forecaster for equipment health degradation over time."""

    def __init__(self, degradation_model: str = 'exponential') -> None:
        self.degradation_model = degradation_model

    async def forecast_degradation(self, equipment_id: str, current_health: float, sensor_trends: list[float], horizon_hours: int) -> dict:
        """Forecast the degradation of health over the given horizon."""
        log.info(f"Forecasting degradation for {equipment_id} over {horizon_hours}h")
        
        # We assume sensor_trends represents historical health values
        # If empty, we use a basic assumption
        if not sensor_trends:
            sensor_trends = [current_health + 0.05, current_health]
            
        coeffs, model_type, r_squared = self._fit_degradation_curve(sensor_trends)
        
        health_curve = []
        projected_health = current_health
        threshold_crossing = None
        alert_threshold = 0.4
        
        for h in range(1, horizon_hours + 1):
            h_val = self._project_health(coeffs, current_health, h, model_type)
            health_curve.append({
                "timestamp_offset_h": h,
                "health_score": h_val
            })
            
            if threshold_crossing is None and h_val <= alert_threshold:
                threshold_crossing = {
                    "hours_until": h,
                    "threshold": alert_threshold
                }
            
            if h == horizon_hours:
                projected_health = h_val
                
        # Rate per hour
        degradation_rate = (current_health - projected_health) / max(1, horizon_hours)
        
        failure_risk = float(np.clip(1.0 - projected_health, 0.0, 1.0))
        
        return {
            "health_curve": health_curve,
            "degradation_rate": float(degradation_rate),
            "projected_health_at_horizon": float(projected_health),
            "failure_risk": failure_risk,
            "alert_threshold_crossing": threshold_crossing
        }

    def _fit_degradation_curve(self, health_history: list[float]) -> tuple[np.ndarray, str, float]:
        """Fit a degradation curve to historical data."""
        x = np.arange(len(health_history))
        y = np.array(health_history)
        
        if self.degradation_model == 'exponential':
            # y = a * e^(bx) => ln(y) = ln(a) + bx
            # We must ensure y > 0
            y_safe = np.clip(y, 1e-5, 1.0)
            coeffs = np.polyfit(x, np.log(y_safe), 1)
            # R^2 calc
            p = np.poly1d(coeffs)
            yhat = np.exp(p(x))
            ybar = np.sum(y)/len(y)
            ssreg = np.sum((yhat-ybar)**2)
            sstot = np.sum((y - ybar)**2)
            r_squared = ssreg / sstot if sstot > 0 else 1.0
            return coeffs, 'exponential', float(r_squared)
        elif self.degradation_model == 'polynomial':
            coeffs = np.polyfit(x, y, 2)
            p = np.poly1d(coeffs)
            yhat = p(x)
            ybar = np.sum(y)/len(y)
            ssreg = np.sum((yhat-ybar)**2)
            sstot = np.sum((y - ybar)**2)
            r_squared = ssreg / sstot if sstot > 0 else 1.0
            return coeffs, 'polynomial', float(r_squared)
        else:
            # linear
            coeffs = np.polyfit(x, y, 1)
            p = np.poly1d(coeffs)
            yhat = p(x)
            ybar = np.sum(y)/len(y)
            ssreg = np.sum((yhat-ybar)**2)
            sstot = np.sum((y - ybar)**2)
            r_squared = ssreg / sstot if sstot > 0 else 1.0
            return coeffs, 'linear', float(r_squared)

    def _project_health(self, coefficients: np.ndarray, start_health: float, hours_ahead: int, model_type: str) -> float:
        """Project future health using fitted coefficients."""
        x_val = 10 + hours_ahead # Mock index, assuming history length was 10
        if model_type == 'exponential':
            val = np.exp(coefficients[1] + coefficients[0] * x_val)
        elif model_type == 'polynomial':
            p = np.poly1d(coefficients)
            val = p(x_val)
        else:
            p = np.poly1d(coefficients)
            val = p(x_val)
            
        return float(np.clip(val, 0.0, start_health))

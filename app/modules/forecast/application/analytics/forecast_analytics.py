from __future__ import annotations
import uuid
from datetime import datetime, timezone
import numpy as np

from app.core.logging import get_logger
log = get_logger(__name__)

class ForecastAnalyticsService:
    """Service for computing forecast accuracy, drift, and trends."""

    def __init__(self) -> None:
        pass

    async def compute_accuracy_metrics(self, actual_values: list[float], predicted_values: list[float]) -> dict:
        """Compute standard forecast accuracy metrics."""
        log.info("Computing accuracy metrics")
        
        if not actual_values or not predicted_values or len(actual_values) != len(predicted_values):
            return {"mae": 0.0, "mse": 0.0, "rmse": 0.0, "mape": 0.0, "r_squared": 0.0}
            
        y_true = np.array(actual_values)
        y_pred = np.array(predicted_values)
        
        mae = np.mean(np.abs(y_true - y_pred))
        mse = np.mean((y_true - y_pred) ** 2)
        rmse = np.sqrt(mse)
        
        # Avoid division by zero in MAPE
        mask = y_true != 0
        if np.any(mask):
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        else:
            mape = 0.0
            
        # R-squared
        y_bar = np.mean(y_true)
        ss_tot = np.sum((y_true - y_bar) ** 2)
        ss_res = np.sum((y_true - y_pred) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 1.0
        
        return {
            "mae": float(mae),
            "mse": float(mse),
            "rmse": float(rmse),
            "mape": float(mape),
            "r_squared": float(r_squared)
        }

    async def compute_forecast_drift(self, historical_forecasts: list[dict], entity_id: str) -> dict:
        """Compute drift in forecasts over time."""
        log.info(f"Computing forecast drift for {entity_id}")
        
        if len(historical_forecasts) < 2:
            return {"drift_score": 0.0, "drift_direction": "NONE", "drift_magnitude": 0.0}
            
        # Mock logic: compare average of recent half to older half
        vals = [f.get('value', 0.0) for f in historical_forecasts]
        mid = len(vals) // 2
        older_mean = np.mean(vals[:mid])
        newer_mean = np.mean(vals[mid:])
        
        drift_mag = abs(newer_mean - older_mean)
        direction = "UP" if newer_mean > older_mean else "DOWN" if newer_mean < older_mean else "NONE"
        score = float(np.clip(drift_mag / max(1e-5, older_mean), 0.0, 1.0))
        
        return {
            "drift_score": float(score),
            "drift_direction": direction,
            "drift_magnitude": float(drift_mag)
        }

    async def compute_confidence_trends(self, confidence_history: list[float]) -> dict:
        """Compute trends in forecast confidence."""
        if not confidence_history:
            return {"trend": 0.0, "mean_confidence": 0.0, "std_confidence": 0.0, "improving": False}
            
        mean_conf = np.mean(confidence_history)
        std_conf = np.std(confidence_history)
        
        if len(confidence_history) > 1:
            x = np.arange(len(confidence_history))
            coeffs = np.polyfit(x, confidence_history, 1)
            trend = coeffs[0]
        else:
            trend = 0.0
            
        return {
            "trend": float(trend),
            "mean_confidence": float(mean_conf),
            "std_confidence": float(std_conf),
            "improving": trend > 0
        }

    async def compute_equipment_health_trends(self, health_history: list[dict]) -> dict:
        """Compute trends in equipment health."""
        if not health_history:
            return {"trend_direction": "STABLE", "degradation_rate": 0.0, "projected_health_30d": 1.0, "anomaly_count": 0}
            
        scores = [h.get("health_score", 1.0) for h in health_history]
        
        if len(scores) > 1:
            x = np.arange(len(scores))
            coeffs = np.polyfit(x, scores, 1)
            rate = coeffs[0]
        else:
            rate = 0.0
            
        direction = "DEGRADING" if rate < -0.01 else "IMPROVING" if rate > 0.01 else "STABLE"
        proj = scores[-1] + (rate * 30.0)  # Assuming 1 step = 1 day for this metric
        
        # Simple anomaly detection: points outside 2 std devs
        mean_s = np.mean(scores)
        std_s = np.std(scores)
        anomalies = sum(1 for s in scores if abs(s - mean_s) > 2 * std_s)
        
        return {
            "trend_direction": direction,
            "degradation_rate": float(rate),
            "projected_health_30d": float(np.clip(proj, 0.0, 1.0)),
            "anomaly_count": anomalies
        }

    async def compute_zone_health_evolution(self, zone_forecasts: list[dict]) -> dict:
        """Analyze how zone health is evolving."""
        improving = 0
        degrading = 0
        stable = 0
        
        for f in zone_forecasts:
            trend = f.get("trend", 0.0)
            if trend > 0.05:
                improving += 1
            elif trend < -0.05:
                degrading += 1
            else:
                stable += 1
                
        total = improving + degrading + stable
        if total == 0:
            overall = "STABLE"
        elif degrading > total * 0.3:
            overall = "DEGRADING"
        elif improving > total * 0.5:
            overall = "IMPROVING"
        else:
            overall = "STABLE"
            
        return {
            "zones_improving": improving,
            "zones_degrading": degrading,
            "zones_stable": stable,
            "overall_trend": overall
        }

    async def compute_plant_health_summary(self, plant_forecast: dict) -> dict:
        """Compute an overall summary of plant health."""
        health_score = plant_forecast.get("aggregate_health", 0.8)
        stability = plant_forecast.get("stability_index", 0.9)
        alerts = plant_forecast.get("critical_alerts_projected", 0)
        
        trend = "STABLE"
        if health_score < 0.6 or alerts > 5:
            trend = "CRITICAL"
        elif health_score < 0.8 or alerts > 2:
            trend = "DEGRADING"
            
        return {
            "health_score": float(health_score),
            "stability_index": float(stability),
            "critical_alerts": int(alerts),
            "trend": trend
        }

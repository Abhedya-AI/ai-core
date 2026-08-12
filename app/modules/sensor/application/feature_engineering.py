"""
sensor/application/feature_engineering.py — Sensor Feature Engineering.

Generates ML-ready feature vectors from raw sensor readings.
These features are consumed by:
  - Risk Prediction module (failure classification)
  - Forecast Intelligence (time-series forecasting)
  - Anomaly detection engines (contextual features)
  - Dashboard (human-readable health scores)

All features are scalar floats in [0,1] or unbounded depending on type.
No numpy. Pure Python math.
"""
from __future__ import annotations
import math
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorHealthState

try:
    from app.modules.sensor.domain.analytics_models import TrendDirection
except ImportError:
    from enum import Enum
    class TrendDirection(str, Enum):
        RISING = "RISING"
        FALLING = "FALLING"
        STABLE = "STABLE"
        VOLATILE = "VOLATILE"

log = get_logger("sensor.feature_engineering")

class SensorFeatureVector(BaseModel):
    """Aggregated feature vector for a sensor."""
    sensor_id: str
    timestamp: str
    
    # Raw features
    current_value: float
    value_normalized: float
    
    # Moving average features
    sma_5: float
    sma_20: float
    ema_5: float
    ema_20: float
    
    # Rate of change features
    delta_1: float
    delta_pct_1: float
    rate_of_change: float
    acceleration: float
    
    # Statistical features
    rolling_std_20: float
    rolling_mean_20: float
    z_score: float
    iqr: float
    
    # Pattern features
    spike_score: float
    drift_score: float
    stuck_score: float
    oscillation_score: float
    
    # Health features (from SensorHealthState)
    consecutive_anomalies: int
    consecutive_healthy: int
    uptime_pct: float
    anomaly_rate_pct: float
    health_score: float
    reliability_score: float
    trend_score: float


class FeatureEngineeringService:
    """Service for computing sensor feature vectors."""
    
    def compute(self, sensor_id: str, readings: list[SensorReading], health: SensorHealthState | None, trend_direction: TrendDirection | None = None) -> SensorFeatureVector:
        """Compute a comprehensive feature vector from recent readings and health."""
        if not readings:
            now = datetime.now(timezone.utc).isoformat()
            return SensorFeatureVector(
                sensor_id=sensor_id, timestamp=now, current_value=0.0, value_normalized=0.0,
                sma_5=0.0, sma_20=0.0, ema_5=0.0, ema_20=0.0, delta_1=0.0, delta_pct_1=0.0,
                rate_of_change=0.0, acceleration=0.0, rolling_std_20=0.0, rolling_mean_20=0.0,
                z_score=0.0, iqr=0.0, spike_score=0.0, drift_score=0.0, stuck_score=0.0,
                oscillation_score=0.0, consecutive_anomalies=0, consecutive_healthy=0,
                uptime_pct=100.0, anomaly_rate_pct=0.0, health_score=1.0, reliability_score=1.0,
                trend_score=0.5
            )
            
        values = [float(r.value) for r in readings]
        current_value = values[-1]
        timestamp = str(readings[-1].timestamp)
        
        val_min = min(values)
        val_max = max(values)
        range_val = val_max - val_min
        value_normalized = (current_value - val_min) / range_val if range_val > 0 else 0.0
        
        sma_5 = self._sma(values, 5)
        sma_20 = self._sma(values, 20)
        ema_5 = self._ema(values, 5)
        ema_20 = self._ema(values, 20)
        
        delta_1 = current_value - values[-2] if len(values) >= 2 else 0.0
        prev_val = values[-2] if len(values) >= 2 else 0.0
        delta_pct_1 = (delta_1 / prev_val) * 100.0 if prev_val != 0 else 0.0
        
        rate_of_change = 0.0
        if len(readings) >= 2:
            try:
                dt1 = datetime.fromisoformat(str(readings[-2].timestamp).replace("Z", "+00:00"))
                dt2 = datetime.fromisoformat(str(readings[-1].timestamp).replace("Z", "+00:00"))
                td = (dt2 - dt1).total_seconds()
                td = td if td > 0 else 1.0
                rate_of_change = abs(delta_1) / td
            except Exception:
                rate_of_change = abs(delta_1)
                
        acceleration = 0.0
        if len(values) >= 3:
            prev_delta = values[-2] - values[-3]
            acceleration = delta_1 - prev_delta
            
        last_20 = values[-20:] if len(values) >= 20 else values
        rolling_mean_20 = sum(last_20) / len(last_20) if last_20 else 0.0
        
        var = sum((x - rolling_mean_20) ** 2 for x in last_20) / len(last_20) if last_20 else 0.0
        rolling_std_20 = math.sqrt(var)
        
        z_score = (current_value - rolling_mean_20) / rolling_std_20 if rolling_std_20 > 0 else 0.0
        
        sorted_20 = sorted(last_20)
        q1 = sorted_20[int(len(sorted_20) * 0.25)] if sorted_20 else 0.0
        q3 = sorted_20[int(len(sorted_20) * 0.75)] if sorted_20 else 0.0
        iqr = q3 - q1
        
        abs_z = abs(z_score)
        spike_score = 1.0 if abs_z > 3.0 else (0.5 if abs_z > 2.0 else 0.0)
        
        last_10 = values[-10:]
        stuck_score = 1.0 if len(last_10) == 10 and len(set(last_10)) == 1 else 0.0
        
        slope = self._slope(last_20)
        drift_score = max(0.0, min(1.0, abs(slope) / 10.0))
        
        sign_changes = 0
        if len(last_10) > 1:
            for i in range(1, len(last_10)):
                prev1 = last_10[i-1]
                prev2 = last_10[i-2] if i > 1 else 0
                if (last_10[i] - prev1) * (prev1 - prev2) < 0:
                    sign_changes += 1
        oscillation_score = max(0.0, min(1.0, sign_changes / 9.0))
        
        consecutive_anomalies = getattr(health, 'consecutive_anomalies', 0) if health else 0
        consecutive_healthy = getattr(health, 'consecutive_healthy', 0) if health else 0
        uptime_pct = getattr(health, 'uptime_pct', 100.0) if health else 100.0
        anomaly_rate_pct = getattr(health, 'anomaly_rate_pct', 0.0) if health else 0.0
        
        health_score = max(0.0, min(1.0, (1.0 - anomaly_rate_pct / 100.0) * (uptime_pct / 100.0))) if health else 1.0
        reliability_score = max(0.0, min(1.0, (uptime_pct / 100.0) * (1.0 - consecutive_anomalies * 0.05)))
        
        trend_score = 0.5
        if trend_direction:
            td_val = trend_direction.value if hasattr(trend_direction, "value") else str(trend_direction)
            if td_val == "RISING":
                trend_score = 1.0
            elif td_val == "FALLING":
                trend_score = 0.0
            elif td_val == "VOLATILE":
                trend_score = 0.3
        
        return SensorFeatureVector(
            sensor_id=sensor_id,
            timestamp=timestamp,
            current_value=current_value,
            value_normalized=value_normalized,
            sma_5=sma_5,
            sma_20=sma_20,
            ema_5=ema_5,
            ema_20=ema_20,
            delta_1=delta_1,
            delta_pct_1=delta_pct_1,
            rate_of_change=rate_of_change,
            acceleration=acceleration,
            rolling_std_20=rolling_std_20,
            rolling_mean_20=rolling_mean_20,
            z_score=z_score,
            iqr=iqr,
            spike_score=spike_score,
            drift_score=drift_score,
            stuck_score=stuck_score,
            oscillation_score=oscillation_score,
            consecutive_anomalies=consecutive_anomalies,
            consecutive_healthy=consecutive_healthy,
            uptime_pct=uptime_pct,
            anomaly_rate_pct=anomaly_rate_pct,
            health_score=health_score,
            reliability_score=reliability_score,
            trend_score=trend_score
        )
        
    def compute_batch(self, sensor_readings_map: dict[str, list[SensorReading]], health_map: dict[str, SensorHealthState]) -> list[SensorFeatureVector]:
        """Compute feature vectors for a batch of sensors."""
        features = []
        for sensor_id, readings in sensor_readings_map.items():
            health = health_map.get(sensor_id)
            features.append(self.compute(sensor_id, readings, health))
        return features

    def _sma(self, values: list[float], n: int) -> float:
        """Compute simple moving average over last n values."""
        slice_vals = values[-n:] if len(values) >= n else values
        return sum(slice_vals) / len(slice_vals) if slice_vals else 0.0
        
    def _ema(self, values: list[float], n: int) -> float:
        """Compute exponential moving average over last n values."""
        slice_vals = values[-n:] if len(values) >= n else values
        if not slice_vals:
            return 0.0
        alpha = 2 / (n + 1)
        ema = slice_vals[0]
        for val in slice_vals[1:]:
            ema = (val * alpha) + (ema * (1 - alpha))
        return ema
        
    def _slope(self, values: list[float]) -> float:
        """Compute least squares slope of values."""
        n = len(values)
        if n < 2:
            return 0.0
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * v for i, v in enumerate(values))
        sum_xx = sum(i * i for i in range(n))
        
        denominator = (n * sum_xx - sum_x ** 2)
        if denominator == 0:
            return 0.0
        return (n * sum_xy - sum_x * sum_y) / denominator

"""
sensor/application/time_series_service.py — Sensor Time Series Engine.

Provides efficient time-series analytics on sensor reading streams:
  - Rolling window aggregation (min, max, mean, std, sum, count)
  - Downsampling / resampling by time bucket
  - Linear interpolation for missing values
  - Seasonal decomposition (trend + residual, no external deps)
  - Trend analysis with confidence interval
  - Forecast data preparation for downstream Forecast Intelligence

All calculations are numpy-free using pure Python math.
Feeds: Forecast Intelligence module, Dashboard, GraphRAG context.
"""
from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta
from typing import Any
from pydantic import BaseModel, Field
from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading

log = get_logger("sensor.time_series_service")

class TimeWindow(BaseModel):
    """Aggregated statistics for a specific time window."""
    model_config = {"frozen": True}
    
    sensor_id: str
    start_ts: str
    end_ts: str
    values: list[float]
    count: int
    mean: float
    std: float
    min: float
    max: float
    sum: float
    p50: float
    p95: float

class ResampledSeries(BaseModel):
    """A series resampled into constant time buckets."""
    model_config = {"frozen": True}
    
    sensor_id: str
    bucket_seconds: int
    buckets: list[dict]

class DecomposedSeries(BaseModel):
    """A series decomposed into trend, residual, and optional seasonal components."""
    model_config = {"frozen": True}
    
    sensor_id: str
    trend: list[float]
    residual: list[float]
    seasonal: list[float] | None
    window_size: int

class ForecastInput(BaseModel):
    """Features extracted and prepared for time-series forecasting."""
    model_config = {"frozen": True}
    
    sensor_id: str
    values: list[float]
    timestamps: list[str]
    features: dict[str, list[float]]

class TimeSeriesService:
    """Service for computing efficient time-series analytics on sensor data."""

    def rolling_window(self, sensor_id: str, values: list[float], window: int) -> TimeWindow:
        """
        Compute rolling window aggregations over the last `window` values.
        Includes count, mean, std, min, max, sum, p50, p95.
        """
        slice_vals = values[-window:] if len(values) >= window else values
        count = len(slice_vals)
        if count == 0:
            return TimeWindow(
                sensor_id=sensor_id, start_ts="", end_ts="", values=[],
                count=0, mean=0.0, std=0.0, min=0.0, max=0.0, sum=0.0, p50=0.0, p95=0.0
            )
        
        val_sum = sum(slice_vals)
        mean = val_sum / count
        
        # Standard variance calculation
        var_sum = sum((x - mean) ** 2 for x in slice_vals)
        std = math.sqrt(var_sum / count) if count > 0 else 0.0
        
        min_val = min(slice_vals)
        max_val = max(slice_vals)
        
        sorted_vals = sorted(slice_vals)
        p50 = sorted_vals[int(count * 0.50)] if count > 0 else 0.0
        p95 = sorted_vals[int(count * 0.95)] if count > 0 else 0.0
        
        now = datetime.now(timezone.utc)
        start_ts = (now - timedelta(seconds=count)).isoformat()
        end_ts = now.isoformat()
        
        return TimeWindow(
            sensor_id=sensor_id,
            start_ts=start_ts,
            end_ts=end_ts,
            values=slice_vals,
            count=count,
            mean=mean,
            std=std,
            min=min_val,
            max=max_val,
            sum=val_sum,
            p50=p50,
            p95=p95
        )

    def resample(self, sensor_id: str, readings: list[SensorReading], bucket_seconds: int = 60) -> ResampledSeries:
        """
        Resample readings into time buckets of bucket_seconds width.
        Computes mean, min, max, count per bucket.
        """
        if not readings:
            return ResampledSeries(sensor_id=sensor_id, bucket_seconds=bucket_seconds, buckets=[])
        
        buckets_map = {}
        for r in readings:
            try:
                # Handle basic ISO format replacing Z with +00:00 for python fromisoformat
                ts_str = str(r.timestamp).replace("Z", "+00:00")
                dt = datetime.fromisoformat(ts_str)
                ts = dt.timestamp()
            except Exception:
                continue
            
            bucket_ts = (ts // bucket_seconds) * bucket_seconds
            if bucket_ts not in buckets_map:
                buckets_map[bucket_ts] = []
            buckets_map[bucket_ts].append(r.value)
            
        sorted_buckets = []
        for b_ts in sorted(buckets_map.keys()):
            vals = buckets_map[b_ts]
            sorted_buckets.append({
                "ts": datetime.fromtimestamp(b_ts, tz=timezone.utc).isoformat(),
                "mean": sum(vals) / len(vals),
                "min": min(vals),
                "max": max(vals),
                "count": len(vals)
            })
            
        return ResampledSeries(
            sensor_id=sensor_id,
            bucket_seconds=bucket_seconds,
            buckets=sorted_buckets
        )

    def interpolate_missing(self, values: list[float | None], timestamps: list[float]) -> list[float]:
        """
        Linear interpolation for None gaps in time series.
        If leading/trailing None, fills with nearest valid value.
        """
        if not values:
            return []
            
        result = list(values)
        n = len(result)
        
        # Fill leading Nones
        first_valid = None
        for v in result:
            if v is not None:
                first_valid = v
                break
        if first_valid is None:
            return [0.0] * n
            
        for i in range(n):
            if result[i] is None:
                result[i] = first_valid
            else:
                break
                
        # Fill trailing Nones
        last_valid = None
        for i in range(n - 1, -1, -1):
            if result[i] is not None:
                last_valid = result[i]
                break
        for i in range(n - 1, -1, -1):
            if result[i] is None:
                result[i] = last_valid
            else:
                break
                
        # Interpolate middle Nones
        for i in range(n):
            if result[i] is None:
                next_idx = i + 1
                while next_idx < n and result[next_idx] is None:
                    next_idx += 1
                
                if next_idx < n:
                    prev_val = result[i - 1]
                    next_val = result[next_idx]
                    prev_ts = timestamps[i - 1]
                    next_ts = timestamps[next_idx]
                    
                    if next_ts > prev_ts:
                        slope = (next_val - prev_val) / (next_ts - prev_ts)
                        result[i] = prev_val + slope * (timestamps[i] - prev_ts)
                    else:
                        result[i] = prev_val
        
        return result

    def decompose(self, sensor_id: str, values: list[float], window: int = 12, window_size: int | None = None) -> DecomposedSeries:
        """
        Seasonal decomposition into trend and residual components.
        Trend is computed with a centered moving average.
        """
        if window_size is not None:
            window = window_size
        n = len(values)
        if n < window:
            return DecomposedSeries(
                sensor_id=sensor_id,
                trend=[0.0] * n,
                residual=values,
                seasonal=None,
                window_size=window
            )
            
        trend = [0.0] * n
        half_window = window // 2
        
        for i in range(n):
            start_idx = max(0, i - half_window)
            end_idx = min(n, i + half_window + 1)
            window_vals = values[start_idx:end_idx]
            trend[i] = sum(window_vals) / len(window_vals) if window_vals else 0.0
            
        residual = [values[i] - trend[i] for i in range(n)]
        
        return DecomposedSeries(
            sensor_id=sensor_id,
            trend=trend,
            residual=residual,
            seasonal=None,
            window_size=window
        )

    def prepare_forecast_input(self, sensor_id: str, readings: list[SensorReading], feature_window: int = 20) -> ForecastInput:
        """
        Prepare forecast input with named feature vectors ready for ML.
        Computes sma, ema, delta, rolling_std, rate_of_change, min_max_norm.
        """
        values = [float(r.value) for r in readings]
        timestamps = [str(r.timestamp) for r in readings]
        
        if not values:
            return ForecastInput(sensor_id=sensor_id, values=[], timestamps=[], features={})
            
        slice_vals = values[-feature_window:] if len(values) >= feature_window else values
        slice_ts = timestamps[-feature_window:] if len(timestamps) >= feature_window else timestamps
        
        sma = []
        ema = []
        delta = []
        rolling_std = []
        rate_of_change = []
        min_max_norm = []
        
        alpha = 2 / (feature_window + 1)
        current_ema = slice_vals[0] if slice_vals else 0.0
        
        val_min = min(slice_vals) if slice_vals else 0.0
        val_max = max(slice_vals) if slice_vals else 0.0
        range_val = val_max - val_min if val_max > val_min else 1.0
        
        for i, v in enumerate(slice_vals):
            window_vals = slice_vals[max(0, i - feature_window + 1):i + 1]
            
            sma.append(sum(window_vals) / len(window_vals))
            
            if i == 0:
                current_ema = v
            else:
                current_ema = (v * alpha) + (current_ema * (1 - alpha))
            ema.append(current_ema)
            
            diff = v - slice_vals[i - 1] if i > 0 else 0.0
            delta.append(diff)
            
            mean = sum(window_vals) / len(window_vals)
            var = sum((x - mean) ** 2 for x in window_vals) / len(window_vals)
            rolling_std.append(math.sqrt(var))
            
            if i > 0:
                try:
                    dt1 = datetime.fromisoformat(slice_ts[i - 1].replace("Z", "+00:00"))
                    dt2 = datetime.fromisoformat(slice_ts[i].replace("Z", "+00:00"))
                    td = (dt2 - dt1).total_seconds()
                    td = td if td > 0 else 1.0
                    rate_of_change.append(abs(diff) / td)
                except Exception:
                    rate_of_change.append(abs(diff))
            else:
                rate_of_change.append(0.0)
                
            min_max_norm.append((v - val_min) / range_val)
            
        features = {
            "sma": sma,
            "ema": ema,
            "delta": delta,
            "rolling_std": rolling_std,
            "rate_of_change": rate_of_change,
            "min_max_norm": min_max_norm
        }
        
        return ForecastInput(
            sensor_id=sensor_id,
            values=slice_vals,
            timestamps=slice_ts,
            features=features
        )

    def detect_seasonality(self, values: list[float], period: int = 24) -> dict:
        """
        Detect seasonality using a simple periodicity check.
        Checks if mean of values[0::period] approximates mean of values[period//2::period].
        """
        if len(values) < period * 2:
            return {"detected": False, "period": period, "confidence": 0.0}
            
        group1 = values[0::period]
        group2 = values[period//2::period]
        
        mean1 = sum(group1) / len(group1) if group1 else 0.0
        mean2 = sum(group2) / len(group2) if group2 else 0.0
        
        diff = abs(mean1 - mean2)
        avg = (abs(mean1) + abs(mean2)) / 2
        
        confidence = max(0.0, min(1.0, diff / avg)) if avg > 0 else 0.0
        detected = confidence > 0.3
        
        return {
            "detected": detected,
            "period": period,
            "confidence": confidence
        }

import numpy as np
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from app.core.logging import get_logger

log = get_logger(__name__)

class TimeSeriesEngine:
    """Engine for computing statistical and temporal features from time series data."""
    
    def compute_rolling_stats(self, values: list[float], window: int) -> dict:
        """Compute rolling statistics over a specified window."""
        if not values:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "variance": 0.0}
        
        arr = np.array(values)
        if len(arr) < window:
            window = len(arr)
            
        recent = arr[-window:]
        return {
            "mean": float(np.mean(recent)),
            "std": float(np.std(recent)),
            "min": float(np.min(recent)),
            "max": float(np.max(recent)),
            "variance": float(np.var(recent))
        }

    def compute_rate_of_change(self, values: list[float], timestamps: list[str]) -> float:
        """Compute the rate of change between the last two points."""
        if len(values) < 2 or len(timestamps) < 2:
            return 0.0
        
        try:
            t1 = datetime.fromisoformat(timestamps[-2].replace('Z', '+00:00')).timestamp()
            t2 = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00')).timestamp()
            dt = t2 - t1
            if dt == 0:
                return 0.0
            return (values[-1] - values[-2]) / dt
        except Exception as e:
            log.warning(f"Error computing rate of change: {e}")
            return 0.0

    def compute_trend_slope(self, values: list[float]) -> tuple[float, float]:
        """Compute linear trend slope and R-squared fit."""
        if len(values) < 2:
            return 0.0, 0.0
            
        x = np.arange(len(values))
        y = np.array(values)
        
        A = np.vstack([x, np.ones(len(x))]).T
        try:
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            
            y_pred = m * x + c
            ss_res = np.sum((y - y_pred)**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r_squared = 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
            
            return float(m), float(r_squared)
        except Exception as e:
            log.warning(f"Error computing trend slope: {e}")
            return 0.0, 0.0

    def detect_drift(self, values: list[float], baseline_mean: float, baseline_std: float) -> float:
        """Compute distribution drift score from a baseline."""
        if not values or baseline_std == 0:
            return 0.0
            
        current_mean = float(np.mean(values))
        drift = abs(current_mean - baseline_mean) / baseline_std
        
        return float(min(drift / 3.0, 1.0))

    def compute_temporal_score(self, timestamps: list[str]) -> dict:
        """Compute metadata scores about the temporal distribution of events."""
        if not timestamps:
            return {"recency_score": 0.0, "frequency_score": 0.0, "gap_score": 0.0}
            
        try:
            times = [datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp() for ts in timestamps]
            now = datetime.utcnow().timestamp()
            
            age = now - times[-1]
            recency_score = max(0.0, 1.0 - (age / 86400))
            
            if len(times) > 1:
                gaps = np.diff(times)
                mean_gap = float(np.mean(gaps))
                frequency_score = min(1.0, 3600 / mean_gap) if mean_gap > 0 else 1.0
                gap_score = float(np.max(gaps)) / mean_gap if mean_gap > 0 else 1.0
            else:
                frequency_score = 0.0
                gap_score = 1.0
                
            return {
                "recency_score": recency_score,
                "frequency_score": frequency_score,
                "gap_score": gap_score
            }
        except Exception as e:
            log.warning(f"Error computing temporal score: {e}")
            return {"recency_score": 0.0, "frequency_score": 0.0, "gap_score": 0.0}

    def interpolate_missing(self, values: list[float | None]) -> list[float]:
        """Perform linear interpolation for missing values."""
        if not values:
            return []
            
        arr = np.array([np.nan if v is None else v for v in values])
        nans = np.isnan(arr)
        
        if not np.any(nans):
            return list(arr)
            
        if np.all(nans):
            return [0.0] * len(values)
            
        arr[nans] = np.interp(np.flatnonzero(nans), np.flatnonzero(~nans), arr[~nans])
        return list(arr)

    def resample(self, values: list[float], timestamps: list[str], target_interval_sec: int) -> tuple[list[float], list[str]]:
        """Resample time series at a uniform interval."""
        if not values or not timestamps:
            return [], []
            
        try:
            times = [datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp() for ts in timestamps]
            start_t = times[0]
            end_t = times[-1]
            
            new_times = np.arange(start_t, end_t + target_interval_sec, target_interval_sec)
            new_values = np.interp(new_times, times, values)
            
            new_timestamps = [datetime.fromtimestamp(t).isoformat() for t in new_times]
            return list(new_values), new_timestamps
        except Exception as e:
            log.warning(f"Error resampling: {e}")
            return values, timestamps

    def decompose_seasonality(self, values: list[float]) -> dict:
        """Simple moving average decomposition for trend and seasonal components."""
        period = 7
        if len(values) < period * 2:
            return {"trend": values, "seasonal": [0.0]*len(values)}
            
        try:
            arr = np.array(values)
            kernel = np.ones(period) / period
            trend = np.convolve(arr, kernel, mode='same')
            
            detrended = arr - trend
            seasonal = np.array([np.mean(detrended[i::period]) for i in range(period)])
            seasonal = np.tile(seasonal, len(arr) // period + 1)[:len(arr)]
            
            return {
                "trend": list(trend),
                "seasonal": list(seasonal)
            }
        except Exception as e:
            log.warning(f"Error decomposing seasonality: {e}")
            return {"trend": values, "seasonal": [0.0]*len(values)}

    def compute_ewma(self, values: list[float], alpha: float = 0.3) -> list[float]:
        """Compute Exponentially Weighted Moving Average."""
        if not values:
            return []
            
        ewma = [values[0]]
        for val in values[1:]:
            ewma.append(alpha * val + (1 - alpha) * ewma[-1])
            
        return ewma

    def compute_zscore(self, value: float, mean: float, std: float) -> float:
        """Compute Z-score."""
        if std == 0:
            return 0.0
        return (value - mean) / std

    def compute_event_window_features(self, values: list[float], event_indices: list[int], window: int = 5) -> dict:
        """Extract features around specific event indices."""
        if not values or not event_indices:
            return {"pre_event_mean": 0.0, "post_event_mean": 0.0, "event_impact": 0.0}
            
        arr = np.array(values)
        pre_means = []
        post_means = []
        
        for idx in event_indices:
            start_pre = max(0, idx - window)
            end_post = min(len(arr), idx + window + 1)
            
            pre_window = arr[start_pre:idx]
            post_window = arr[idx+1:end_post]
            
            if len(pre_window) > 0:
                pre_means.append(np.mean(pre_window))
            if len(post_window) > 0:
                post_means.append(np.mean(post_window))
                
        avg_pre = float(np.mean(pre_means)) if pre_means else 0.0
        avg_post = float(np.mean(post_means)) if post_means else 0.0
        impact = avg_post - avg_pre
        
        return {
            "pre_event_mean": avg_pre,
            "post_event_mean": avg_post,
            "event_impact": impact
        }

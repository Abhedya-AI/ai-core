from __future__ import annotations

import numpy as np
from dataclasses import dataclass

@dataclass
class DecompositionResult:
    trend: list[float]
    seasonal: list[float]
    residual: list[float]
    strength_trend: float
    strength_seasonal: float

class TimeSeriesDecomposer:
    @staticmethod
    def compute_autocorrelation(series: list[float], max_lag: int = 50) -> list[float]:
        y = np.array(series, dtype=float)
        n = len(y)
        if n < 2:
            return []
        
        mean = np.mean(y)
        var = np.var(y)
        if var == 0:
            return [0.0] * min(n, max_lag)
            
        acf = []
        for lag in range(min(n, max_lag)):
            cov = np.sum((y[:n-lag] - mean) * (y[lag:] - mean)) / n
            acf.append(float(cov / var))
        return acf

    @staticmethod
    def detect_seasonality_period(series: list[float]) -> int:
        acf = TimeSeriesDecomposer.compute_autocorrelation(series, max_lag=100)
        if len(acf) < 3:
            return 1
            
        # Find first peak after lag 0
        peaks = []
        for i in range(1, len(acf) - 1):
            if acf[i] > acf[i-1] and acf[i] > acf[i+1] and acf[i] > 0.2:
                peaks.append(i)
                
        if peaks:
            return peaks[0]
        return 1

    @staticmethod
    def decompose(series: list[float], period: int = 24) -> DecompositionResult:
        y = np.array(series, dtype=float)
        n = len(y)
        
        if n < period * 2:
            return DecompositionResult(
                trend=y.tolist(), seasonal=[0.0]*n, residual=[0.0]*n,
                strength_trend=0.0, strength_seasonal=0.0
            )

        # 1. Trend: Centered Moving Average
        trend = np.full(n, np.nan)
        if period % 2 == 0:
            window = np.ones(period) / period
            ma = np.convolve(y, window, mode='valid')
            ma_centered = np.convolve(ma, np.ones(2)/2, mode='valid')
            pad_start = period // 2
            trend[pad_start:pad_start+len(ma_centered)] = ma_centered
        else:
            window = np.ones(period) / period
            ma = np.convolve(y, window, mode='valid')
            pad_start = period // 2
            trend[pad_start:pad_start+len(ma)] = ma
            
        # Fill NaNs in trend with nearest valid
        valid_idx = np.where(~np.isnan(trend))[0]
        if len(valid_idx) > 0:
            trend[:valid_idx[0]] = trend[valid_idx[0]]
            trend[valid_idx[-1]+1:] = trend[valid_idx[-1]]
        else:
            trend = y.copy()

        # 2. Detrend
        detrended = y - trend

        # 3. Seasonal: Average by phase
        seasonal_pattern = np.zeros(period)
        for i in range(period):
            phase_vals = detrended[i::period]
            seasonal_pattern[i] = np.nanmean(phase_vals) if len(phase_vals) > 0 else 0.0
            
        seasonal_pattern -= np.mean(seasonal_pattern)
        
        seasonal = np.array([seasonal_pattern[i % period] for i in range(n)])

        # 4. Residual
        residual = y - trend - seasonal
        
        # Strengths
        var_resid = np.var(residual)
        var_trend_resid = np.var(trend + residual)
        var_seas_resid = np.var(seasonal + residual)
        
        str_trend = float(max(0, 1 - var_resid / var_trend_resid)) if var_trend_resid > 0 else 0.0
        str_seas = float(max(0, 1 - var_resid / var_seas_resid)) if var_seas_resid > 0 else 0.0

        return DecompositionResult(
            trend=trend.tolist(),
            seasonal=seasonal.tolist(),
            residual=residual.tolist(),
            strength_trend=str_trend,
            strength_seasonal=str_seas
        )

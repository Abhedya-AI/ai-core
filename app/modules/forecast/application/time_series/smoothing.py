from __future__ import annotations

import numpy as np
from typing import Any

class ExponentialSmoother:
    @staticmethod
    def smooth(series: list[float], alpha: float = 0.3) -> list[float]:
        if not series:
            return []
        y = np.array(series, dtype=float)
        smoothed = np.zeros_like(y)
        smoothed[0] = y[0]
        for i in range(1, len(y)):
            smoothed[i] = alpha * y[i] + (1 - alpha) * smoothed[i-1]
        return smoothed.tolist()

    @staticmethod
    def double_smooth(series: list[float], alpha: float = 0.3, beta: float = 0.1) -> list[float]:
        if not series:
            return []
        y = np.array(series, dtype=float)
        n = len(y)
        smoothed = np.zeros(n)
        trend = np.zeros(n)
        
        smoothed[0] = y[0]
        trend[0] = y[1] - y[0] if n > 1 else 0.0
        
        for i in range(1, n):
            smoothed[i] = alpha * y[i] + (1 - alpha) * (smoothed[i-1] + trend[i-1])
            trend[i] = beta * (smoothed[i] - smoothed[i-1]) + (1 - beta) * trend[i-1]
            
        return smoothed.tolist()

class MovingAverageCalculator:
    @staticmethod
    def simple_ma(series: list[float], window: int) -> list[float]:
        y = np.array(series, dtype=float)
        if len(y) < window:
            return y.tolist()
        weights = np.ones(window) / window
        ma = np.convolve(y, weights, mode='valid')
        # Pad beginning
        pad = np.full(window - 1, np.nan)
        return np.concatenate([pad, ma]).tolist()

    @staticmethod
    def weighted_ma(series: list[float], window: int) -> list[float]:
        y = np.array(series, dtype=float)
        if len(y) < window:
            return y.tolist()
        weights = np.arange(1, window + 1)
        weights = weights / weights.sum()
        ma = np.convolve(y, weights[::-1], mode='valid')
        pad = np.full(window - 1, np.nan)
        return np.concatenate([pad, ma]).tolist()

    @staticmethod
    def exponential_ma(series: list[float], span: int) -> list[float]:
        alpha = 2 / (span + 1)
        return ExponentialSmoother.smooth(series, alpha)

    @staticmethod
    def rolling_stats(series: list[float], window: int) -> list[dict[str, float]]:
        y = np.array(series, dtype=float)
        stats = []
        for i in range(len(y)):
            start = max(0, i - window + 1)
            window_slice = y[start:i+1]
            stats.append({
                "mean": float(np.mean(window_slice)),
                "std": float(np.std(window_slice)),
                "min": float(np.min(window_slice)),
                "max": float(np.max(window_slice)),
                "q25": float(np.percentile(window_slice, 25)),
                "q75": float(np.percentile(window_slice, 75))
            })
        return stats

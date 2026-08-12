from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from .decomposition import TimeSeriesDecomposer

@dataclass
class AdaptiveWindowRecommendation:
    horizon: str
    model_family: str
    reasoning: str

class AdaptiveForecastWindow:
    @staticmethod
    def compute_volatility(series: list[float]) -> float:
        y = np.array(series, dtype=float)
        mean = np.mean(y)
        if mean == 0:
            return float(np.std(y))
        return float(np.std(y) / abs(mean))

    @staticmethod
    def compute_trend_strength(series: list[float]) -> float:
        y = np.array(series, dtype=float)
        x = np.arange(len(y))
        coeffs = np.polyfit(x, y, 1)
        p = np.poly1d(coeffs)
        y_pred = p(x)
        
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        
        if ss_tot == 0:
            return 0.0
        return float(1 - (ss_res / ss_tot))

    @staticmethod
    def recommend_model_family(series: list[float]) -> str:
        volatility = AdaptiveForecastWindow.compute_volatility(series)
        trend = AdaptiveForecastWindow.compute_trend_strength(series)
        
        acf = TimeSeriesDecomposer.compute_autocorrelation(series, 24)
        has_seasonality = any(a > 0.4 for a in acf[1:])
        
        if volatility > 0.8:
            return "Bayesian"
        elif has_seasonality and trend > 0.5:
            return "Prophet-Style"
        elif has_seasonality:
            return "Exponential Smoothing"
        elif trend > 0.8:
            return "ARIMA"
        else:
            return "LSTM-Proxy"

    @staticmethod
    def select_horizon(series: list[float], default_horizon: str = '24h') -> AdaptiveWindowRecommendation:
        volatility = AdaptiveForecastWindow.compute_volatility(series)
        trend = AdaptiveForecastWindow.compute_trend_strength(series)
        family = AdaptiveForecastWindow.recommend_model_family(series)
        
        if volatility > 1.0:
            horizon = '6h'
            reason = "High volatility detected, short horizon recommended."
        elif trend > 0.8:
            horizon = '7d'
            reason = "Strong trend detected, longer horizon is safe."
        else:
            horizon = default_horizon
            reason = "Standard dynamics, default horizon maintained."
            
        return AdaptiveWindowRecommendation(
            horizon=horizon,
            model_family=family,
            reasoning=reason
        )

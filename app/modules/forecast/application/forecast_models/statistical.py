from __future__ import annotations

import math
import numpy as np
from typing import Any
try:
    from app.core.logging import get_logger
    log = get_logger(__name__)
except ImportError:
    import logging
    log = logging.getLogger(__name__)

from .base import ForecastModelResult, AbstractForecastModel

class ARIMAForecastModel:
    def __init__(self, p: int = 2, d: int = 1, q: int = 1) -> None:
        self.p = p
        self.d = d
        self.q = q
        self.ar_coeffs: np.ndarray | None = None
        self.intercept: float = 0.0
        self.last_values: list[float] = []
        self.residual_std: float = 0.0
        self.sample_size: int = 0
        self.differenced_series: list[float] = []
        
    async def train(self, time_series: list[float], timestamps: list[str]) -> None:
        series = np.array(time_series, dtype=float)
        self.sample_size = len(series)
        self.last_values = series.tolist()
        
        # Differencing
        diff_series = series
        for _ in range(self.d):
            diff_series = np.diff(diff_series)
        self.differenced_series = diff_series.tolist()
        
        if len(diff_series) <= self.p:
            self.ar_coeffs = np.zeros(self.p)
            self.residual_std = np.std(series) if len(series) > 0 else 1.0
            return
            
        # Fit AR via OLS
        X = np.column_stack([diff_series[i : -(self.p - i)] for i in range(self.p)])
        Y = diff_series[self.p:]
        
        # Add intercept
        X_with_intercept = np.column_stack([np.ones(len(X)), X])
        
        try:
            coeffs, residuals, _, _ = np.linalg.lstsq(X_with_intercept, Y, rcond=None)
            self.intercept = float(coeffs[0])
            self.ar_coeffs = coeffs[1:]
            
            if len(residuals) > 0:
                self.residual_std = float(np.sqrt(residuals[0] / max(1, len(Y) - self.p - 1)))
            else:
                preds = X_with_intercept @ coeffs
                self.residual_std = float(np.std(Y - preds))
        except np.linalg.LinAlgError:
            self.intercept = 0.0
            self.ar_coeffs = np.zeros(self.p)
            self.residual_std = float(np.std(Y))
            
    async def forecast(self, steps: int, context: dict[str, Any]) -> ForecastModelResult:
        if self.ar_coeffs is None:
            raise ValueError("Model not trained.")
            
        preds = []
        current_history = list(self.differenced_series[-self.p:])
        
        for _ in range(steps):
            if len(current_history) < self.p:
                pred_diff = self.intercept
            else:
                pred_diff = self.intercept + np.dot(self.ar_coeffs, current_history[-self.p:])
            current_history.append(float(pred_diff))
            preds.append(float(pred_diff))
            
        # Undifference
        final_preds = []
        last_val = self.last_values[-1] if self.last_values else 0.0
        
        # Simplistic undifferencing (handles d=1 well, needs extra state for d>1)
        if self.d == 1:
            for p_diff in preds:
                last_val += p_diff
                final_preds.append(last_val)
        else:
            final_preds = [self.last_values[-1]] * steps
            
        conf_lower = []
        conf_upper = []
        for i, pred in enumerate(final_preds):
            margin = 1.96 * self.residual_std * math.sqrt(i + 1)
            conf_lower.append(pred - margin)
            conf_upper.append(pred + margin)
            
        return ForecastModelResult(
            predicted_values=final_preds,
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            confidence_score=self.confidence(),
            feature_importance={f"AR_lag_{i+1}": float(v) for i, v in enumerate(self.ar_coeffs)},
            model_family="ARIMA",
            methodology="OLS AR with differencing",
            uncertainty_score=float(min(1.0, self.residual_std / (np.mean(self.last_values) + 1e-9))),
            metadata={"d": self.d, "p": self.p, "q": self.q}
        )
        
    def confidence(self) -> float:
        if self.sample_size < self.p * 3:
            return 0.3
        cv = self.residual_std / (np.mean(self.last_values) + 1e-9)
        return float(max(0.0, min(1.0, 1.0 - cv)))
        
    def explain(self) -> dict[str, Any]:
        return {
            "ar_coefficients": self.ar_coeffs.tolist() if self.ar_coeffs is not None else [],
            "intercept": self.intercept,
            "differencing_order": self.d,
            "residual_std": self.residual_std
        }
        
    def serialize(self) -> dict[str, Any]:
        return {
            "p": self.p, "d": self.d, "q": self.q,
            "ar_coeffs": self.ar_coeffs.tolist() if self.ar_coeffs is not None else [],
            "intercept": self.intercept,
            "residual_std": self.residual_std,
            "last_values": self.last_values
        }

class ExponentialSmoothingModel:
    def __init__(self, alpha: float = 0.3, beta: float = 0.1, gamma: float = 0.1, seasonal_periods: int = 24) -> None:
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.L = seasonal_periods
        self.level: float = 0.0
        self.trend: float = 0.0
        self.seasonals: list[float] = []
        self.residual_std: float = 0.0
        self.history: list[float] = []
        
    async def train(self, time_series: list[float], timestamps: list[str]) -> None:
        if not time_series:
            return
            
        self.history = time_series.copy()
        series = np.array(time_series, dtype=float)
        
        # Initialize
        self.level = series[0]
        self.trend = (series[min(self.L, len(series)-1)] - series[0]) / max(1, min(self.L, len(series)-1))
        
        if len(series) >= self.L * 2:
            s_init = []
            for i in range(self.L):
                s_init.append(float(np.mean(series[i::self.L]) / (np.mean(series) + 1e-9)))
            self.seasonals = s_init
        else:
            self.seasonals = [1.0] * self.L
            
        residuals = []
        for i, y in enumerate(series):
            s_idx = i % self.L
            s_val = self.seasonals[s_idx]
            
            y_pred = (self.level + self.trend) * s_val
            residuals.append(y - y_pred)
            
            last_level = self.level
            self.level = self.alpha * (y / s_val) + (1 - self.alpha) * (self.level + self.trend)
            self.trend = self.beta * (self.level - last_level) + (1 - self.beta) * self.trend
            self.seasonals[s_idx] = self.gamma * (y / self.level) + (1 - self.gamma) * s_val
            
        self.residual_std = float(np.std(residuals))
        
    async def forecast(self, steps: int, context: dict[str, Any]) -> ForecastModelResult:
        preds = []
        conf_lower = []
        conf_upper = []
        
        for m in range(1, steps + 1):
            s_idx = (len(self.history) + m - 1) % self.L
            s_val = self.seasonals[s_idx] if self.seasonals else 1.0
            
            pred = (self.level + m * self.trend) * s_val
            preds.append(float(pred))
            
            margin = 1.96 * self.residual_std * math.sqrt(m)
            conf_lower.append(float(pred - margin))
            conf_upper.append(float(pred + margin))
            
        return ForecastModelResult(
            predicted_values=preds,
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            confidence_score=self.confidence(),
            feature_importance={"level": self.level, "trend": self.trend},
            model_family="Exponential Smoothing",
            methodology="Holt-Winters Triple Exponential Smoothing",
            uncertainty_score=self.residual_std / (abs(self.level) + 1e-9),
            metadata={"alpha": self.alpha, "beta": self.beta, "gamma": self.gamma}
        )
        
    def confidence(self) -> float:
        cv = self.residual_std / (abs(self.level) + 1e-9)
        return float(max(0.0, min(1.0, 1.0 - cv)))
        
    def explain(self) -> dict[str, Any]:
        return {
            "level_component": self.level,
            "trend_component": self.trend,
            "seasonal_components": self.seasonals,
            "residual_std": self.residual_std
        }
        
    def serialize(self) -> dict[str, Any]:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "L": self.L,
            "level": self.level,
            "trend": self.trend,
            "seasonals": self.seasonals,
            "history_len": len(self.history)
        }

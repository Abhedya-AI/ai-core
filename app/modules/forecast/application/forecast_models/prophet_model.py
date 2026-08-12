from __future__ import annotations

import math
import numpy as np
from typing import Any
from .base import ForecastModelResult

class ProphetForecastAbstraction:
    def __init__(self, seasonality_period: int = 24, fourier_order: int = 3) -> None:
        self.period = seasonality_period
        self.fourier_order = fourier_order
        self.trend_slope: float = 0.0
        self.trend_intercept: float = 0.0
        self.seasonality_coeffs: np.ndarray | None = None
        self.residual_std: float = 0.0
        self.history_len: int = 0
        self.r2_score: float = 0.0
        
    def _create_fourier_features(self, t: np.ndarray) -> np.ndarray:
        features = []
        for i in range(1, self.fourier_order + 1):
            features.append(np.sin(2 * np.pi * i * t / self.period))
            features.append(np.cos(2 * np.pi * i * t / self.period))
        return np.column_stack(features)

    async def train(self, time_series: list[float], timestamps: list[str]) -> None:
        y = np.array(time_series, dtype=float)
        self.history_len = len(y)
        t = np.arange(self.history_len)
        
        # Design matrix: [intercept, trend, fourier_1_sin, fourier_1_cos, ...]
        fourier_features = self._create_fourier_features(t)
        X = np.column_stack([np.ones(self.history_len), t, fourier_features])
        
        try:
            coeffs, residuals, _, _ = np.linalg.lstsq(X, y, rcond=None)
            self.trend_intercept = float(coeffs[0])
            self.trend_slope = float(coeffs[1])
            self.seasonality_coeffs = coeffs[2:]
            
            y_pred = X @ coeffs
            ss_res = np.sum((y - y_pred)**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            self.r2_score = float(1 - (ss_res / max(ss_tot, 1e-9)))
            self.residual_std = float(np.std(y - y_pred))
        except np.linalg.LinAlgError:
            self.trend_intercept = float(np.mean(y))
            self.trend_slope = 0.0
            self.seasonality_coeffs = np.zeros(2 * self.fourier_order)
            self.r2_score = 0.0
            self.residual_std = float(np.std(y))

    async def forecast(self, steps: int, context: dict[str, Any]) -> ForecastModelResult:
        if self.seasonality_coeffs is None:
            raise ValueError("Model not trained")
            
        t_future = np.arange(self.history_len, self.history_len + steps)
        fourier_features = self._create_fourier_features(t_future)
        X_future = np.column_stack([np.ones(steps), t_future, fourier_features])
        
        all_coeffs = np.concatenate([[self.trend_intercept, self.trend_slope], self.seasonality_coeffs])
        preds = X_future @ all_coeffs
        
        conf_lower = []
        conf_upper = []
        for i, p in enumerate(preds):
            margin = 1.96 * self.residual_std * math.sqrt(i + 1)
            conf_lower.append(float(p - margin))
            conf_upper.append(float(p + margin))
            
        return ForecastModelResult(
            predicted_values=preds.tolist(),
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            confidence_score=self.confidence(),
            feature_importance={"trend": abs(self.trend_slope), "seasonality": np.linalg.norm(self.seasonality_coeffs)},
            model_family="Prophet-Style",
            methodology="Linear Trend + Fourier Seasonality",
            uncertainty_score=self.residual_std / (abs(self.trend_intercept) + 1e-9),
            metadata={"period": self.period, "r2_score": self.r2_score}
        )

    def confidence(self) -> float:
        return max(0.0, min(1.0, self.r2_score))

    def explain(self) -> dict[str, Any]:
        return {
            "trend_slope": self.trend_slope,
            "trend_intercept": self.trend_intercept,
            "seasonality_amplitudes": self.seasonality_coeffs.tolist() if self.seasonality_coeffs is not None else [],
            "r2_fit": self.r2_score
        }

    def serialize(self) -> dict[str, Any]:
        return {
            "period": self.period,
            "fourier_order": self.fourier_order,
            "trend_slope": self.trend_slope,
            "trend_intercept": self.trend_intercept,
            "seasonality_coeffs": self.seasonality_coeffs.tolist() if self.seasonality_coeffs is not None else [],
            "history_len": self.history_len
        }

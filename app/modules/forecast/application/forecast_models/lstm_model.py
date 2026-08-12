from __future__ import annotations

import math
import numpy as np
from typing import Any
from .base import ForecastModelResult

class LSTMForecastAbstraction:
    def __init__(self, window_size: int = 24, hidden_size: int = 16) -> None:
        self.window_size = window_size
        self.hidden_size = hidden_size
        self.weights: np.ndarray | None = None
        self.bias: float = 0.0
        self.last_window: list[float] = []
        self.residual_std: float = 0.0
        self.r2_score: float = 0.0
        
    async def train(self, time_series: list[float], timestamps: list[str]) -> None:
        series = np.array(time_series, dtype=float)
        if len(series) <= self.window_size:
            self.weights = np.ones(self.window_size) / self.window_size
            self.bias = 0.0
            self.last_window = series.tolist() if len(series) > 0 else [0.0] * self.window_size
            return
            
        X, y = [], []
        for i in range(len(series) - self.window_size):
            X.append(series[i:i+self.window_size])
            y.append(series[i+self.window_size])
            
        X = np.array(X)
        y = np.array(y)
        
        X_design = np.column_stack([np.ones(len(X)), X])
        try:
            coeffs, residuals, _, _ = np.linalg.lstsq(X_design, y, rcond=None)
            self.bias = float(coeffs[0])
            self.weights = coeffs[1:]
            
            y_pred = X_design @ coeffs
            ss_res = np.sum((y - y_pred)**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            self.r2_score = float(1 - (ss_res / max(ss_tot, 1e-9)))
            self.residual_std = float(np.std(y - y_pred))
        except np.linalg.LinAlgError:
            self.weights = np.ones(self.window_size) / self.window_size
            self.bias = 0.0
            self.r2_score = 0.0
            self.residual_std = float(np.std(y))
            
        self.last_window = series[-self.window_size:].tolist()

    async def forecast(self, steps: int, context: dict[str, Any]) -> ForecastModelResult:
        if self.weights is None:
            raise ValueError("Model not trained")
            
        preds = []
        current_window = self.last_window.copy()
        
        for _ in range(steps):
            if len(current_window) < self.window_size:
                pad = [current_window[-1]] * (self.window_size - len(current_window)) if current_window else [0.0] * self.window_size
                current_window = pad + current_window
                
            x_input = np.array(current_window[-self.window_size:])
            pred = self.bias + np.dot(self.weights, x_input)
            preds.append(float(pred))
            current_window.append(float(pred))
            
        conf_lower = []
        conf_upper = []
        for i, p in enumerate(preds):
            margin = 1.96 * self.residual_std * math.sqrt(i + 1)
            conf_lower.append(float(p - margin))
            conf_upper.append(float(p + margin))
            
        importance = {f"lag_{self.window_size - i}": float(w) for i, w in enumerate(self.weights)}
        
        return ForecastModelResult(
            predicted_values=preds,
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            confidence_score=self.confidence(),
            feature_importance=importance,
            model_family="LSTM-Proxy",
            methodology="Windowed Linear Regression (Memory Proxy)",
            uncertainty_score=self.residual_std / (abs(np.mean(self.last_window)) + 1e-9),
            metadata={"window_size": self.window_size, "r2_score": self.r2_score}
        )

    def confidence(self) -> float:
        return max(0.1, min(1.0, self.r2_score))

    def explain(self) -> dict[str, Any]:
        return {
            "weights": self.weights.tolist() if self.weights is not None else [],
            "bias": self.bias,
            "window_size": self.window_size,
            "r2_score": self.r2_score
        }

    def serialize(self) -> dict[str, Any]:
        return {
            "window_size": self.window_size,
            "hidden_size": self.hidden_size,
            "weights": self.weights.tolist() if self.weights is not None else [],
            "bias": self.bias,
            "last_window": self.last_window
        }

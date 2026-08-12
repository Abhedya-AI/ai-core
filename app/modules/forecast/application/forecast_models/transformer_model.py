from __future__ import annotations

import math
import numpy as np
from typing import Any
from .base import ForecastModelResult

class TransformerForecastAbstraction:
    def __init__(self, window_size: int = 24, num_heads: int = 4) -> None:
        self.window_size = window_size
        self.num_heads = num_heads
        self.attention_weights: np.ndarray | None = None
        self.value_matrix: np.ndarray | None = None
        self.last_window: list[float] = []
        self.residual_std: float = 0.0
        
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / np.sum(e_x, axis=-1, keepdims=True)

    async def train(self, time_series: list[float], timestamps: list[str]) -> None:
        series = np.array(time_series, dtype=float)
        if len(series) <= self.window_size:
            self.last_window = series.tolist() if len(series) > 0 else [0.0]*self.window_size
            self.attention_weights = np.ones(self.window_size) / self.window_size
            return

        # Simple self-attention simulation
        windows = []
        for i in range(len(series) - self.window_size):
            windows.append(series[i:i+self.window_size])
        
        X = np.array(windows)
        
        # Simulate Q, K, V mechanism: Use the latest window as Query, history as Keys
        Q = X[-1]
        K = X[:-1]
        V = series[self.window_size:]
        
        # Dot product attention
        scores = K @ Q / np.sqrt(self.window_size)
        attn = self._softmax(scores)
        
        # Aggregate attention back to window positions for explainability
        avg_attn = np.mean(K * attn[:, np.newaxis], axis=0)
        self.attention_weights = self._softmax(avg_attn)
        self.value_matrix = X
        self.last_window = series[-self.window_size:].tolist()
        self.residual_std = float(np.std(series))
        
    async def forecast(self, steps: int, context: dict[str, Any]) -> ForecastModelResult:
        preds = []
        current_window = np.array(self.last_window)
        
        if self.attention_weights is None:
            self.attention_weights = np.ones(self.window_size) / self.window_size
            
        for _ in range(steps):
            if len(current_window) < self.window_size:
                current_window = np.pad(current_window, (self.window_size - len(current_window), 0), mode='edge')
            
            # Forecast is weighted sum of recent window based on learned attention
            pred = np.dot(current_window[-self.window_size:], self.attention_weights)
            preds.append(float(pred))
            current_window = np.append(current_window, pred)
            
        conf_lower = []
        conf_upper = []
        for i, p in enumerate(preds):
            margin = 1.96 * self.residual_std * math.sqrt(i + 1)
            conf_lower.append(float(p - margin))
            conf_upper.append(float(p + margin))
            
        importance = {f"pos_{i}": float(w) for i, w in enumerate(self.attention_weights)}
        
        return ForecastModelResult(
            predicted_values=preds,
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            confidence_score=self.confidence(),
            feature_importance=importance,
            model_family="Transformer-Proxy",
            methodology="Self-Attention Proxy",
            uncertainty_score=self.residual_std / (abs(np.mean(self.last_window)) + 1e-9),
            metadata={"window_size": self.window_size}
        )

    def confidence(self) -> float:
        return 0.6  # Fixed proxy confidence for heuristic attention

    def explain(self) -> dict[str, Any]:
        return {
            "attention_weights": self.attention_weights.tolist() if self.attention_weights is not None else []
        }

    def serialize(self) -> dict[str, Any]:
        return {
            "window_size": self.window_size,
            "attention_weights": self.attention_weights.tolist() if self.attention_weights is not None else [],
            "last_window": self.last_window
        }

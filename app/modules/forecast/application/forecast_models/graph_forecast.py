from __future__ import annotations

import math
import numpy as np
from typing import Any
from .base import ForecastModelResult

class GraphNeuralForecastAbstraction:
    def __init__(self, graph_context: dict[str, Any] | None = None) -> None:
        self.graph_context = graph_context or {}
        self.node_embeddings: dict[str, float] = {}
        self.global_mean: float = 0.0
        self.residual_std: float = 0.0
        self.history: list[float] = []

    async def train(self, time_series: list[float], timestamps: list[str]) -> None:
        self.history = time_series.copy()
        if not time_series:
            return
            
        series = np.array(time_series, dtype=float)
        self.global_mean = float(np.mean(series))
        self.residual_std = float(np.std(series))
        
        neighbors = self.graph_context.get("neighbors", {})
        for node_id, n_series in neighbors.items():
            if n_series and len(n_series) > 0:
                self.node_embeddings[node_id] = float(np.mean(n_series))

    async def forecast(self, steps: int, context: dict[str, Any]) -> ForecastModelResult:
        if not self.history:
            raise ValueError("Model not trained")
            
        # Graph aggregation heuristic: average recent history and neighbor means
        base_pred = float(np.mean(self.history[-min(10, len(self.history)):]))
        
        neighbor_influence = 0.0
        weights = {}
        if self.node_embeddings:
            n_vals = list(self.node_embeddings.values())
            neighbor_influence = float(np.mean(n_vals))
            weights = {k: v / (sum(n_vals) + 1e-9) for k, v in self.node_embeddings.items()}
            pred_val = 0.7 * base_pred + 0.3 * neighbor_influence
        else:
            pred_val = base_pred
            
        preds = [pred_val] * steps
        
        conf_lower = []
        conf_upper = []
        for i, p in enumerate(preds):
            margin = 1.96 * self.residual_std * math.sqrt(i + 1)
            conf_lower.append(float(p - margin))
            conf_upper.append(float(p + margin))

        return ForecastModelResult(
            predicted_values=preds,
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            confidence_score=self.confidence(),
            feature_importance=weights,
            model_family="GraphNeural-Proxy",
            methodology="Neighbor Mean Aggregation",
            uncertainty_score=self.residual_std / (abs(pred_val) + 1e-9),
            metadata={"num_neighbors": len(self.node_embeddings)}
        )

    def confidence(self) -> float:
        return 0.5 + (0.1 * min(5, len(self.node_embeddings)))

    def explain(self) -> dict[str, Any]:
        return {
            "node_embeddings": self.node_embeddings,
            "global_mean": self.global_mean,
            "neighbor_influence_scores": self.node_embeddings
        }

    def serialize(self) -> dict[str, Any]:
        return {
            "node_embeddings": self.node_embeddings,
            "global_mean": self.global_mean,
            "residual_std": self.residual_std,
            "history_len": len(self.history)
        }

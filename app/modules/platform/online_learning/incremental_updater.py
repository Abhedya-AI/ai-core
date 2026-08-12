from __future__ import annotations

import time
from typing import Any
import numpy as np
import asyncio

from app.core.logging import get_logger

log = get_logger(__name__)

class IncrementalModelUpdater:
    def __init__(self) -> None:
        self._weights: dict[str, np.ndarray] = {}
        self._learning_rate: dict[str, float] = {}
        self._update_count: dict[str, int] = {}
        self._default_lr = 0.01

    async def initialize(self, model_id: str, n_features: int) -> None:
        t0 = time.perf_counter()
        # Initialize with small random weights
        self._weights[model_id] = np.random.randn(n_features) * 0.01
        self._learning_rate[model_id] = self._default_lr
        self._update_count[model_id] = 0
        log.info(f"Initialized IncrementalModelUpdater for {model_id} with {n_features} features in {time.perf_counter()-t0:.4f}s")

    async def update(self, model_id: str, features: list[float], target: float) -> dict[str, Any]:
        t0 = time.perf_counter()
        if model_id not in self._weights:
            await self.initialize(model_id, len(features))
            
        w = self._weights[model_id]
        x = np.array(features, dtype=float)
        lr = self._learning_rate[model_id]
        
        if len(x) != len(w):
            raise ValueError(f"Feature dimension mismatch: expected {len(w)}, got {len(x)}")
            
        # Linear prediction
        prediction = float(np.dot(w, x))
        error = target - prediction
        
        # SGD update step: w = w + lr * error * x
        self._weights[model_id] += lr * error * x
        self._update_count[model_id] += 1
        
        latency = time.perf_counter() - t0
        return {
            "model_id": model_id,
            "update_index": self._update_count[model_id],
            "error": error,
            "prediction": prediction,
            "learning_rate": lr
        }

    async def batch_update(self, model_id: str, feature_matrix: list[list[float]], targets: list[float]) -> dict[str, Any]:
        t0 = time.perf_counter()
        if not feature_matrix or not targets:
            return {"updates": 0, "final_error": 0.0, "mean_error": 0.0, "improvement": 0.0}
            
        if model_id not in self._weights:
            await self.initialize(model_id, len(feature_matrix[0]))
            
        w = self._weights[model_id]
        X = np.array(feature_matrix, dtype=float)
        y = np.array(targets, dtype=float)
        lr = self._learning_rate[model_id]
        
        # Compute loss before
        preds_before = X.dot(w)
        loss_before = float(np.mean((y - preds_before)**2))
        
        errors = []
        updates = 0
        
        # Iterative update
        for i in range(len(X)):
            xi = X[i]
            yi = y[i]
            pred = np.dot(w, xi)
            err = yi - pred
            w += lr * err * xi
            errors.append(abs(err))
            updates += 1
            
        self._weights[model_id] = w
        self._update_count[model_id] += updates
        
        # Compute loss after
        preds_after = X.dot(w)
        loss_after = float(np.mean((y - preds_after)**2))
        
        improvement = max(0.0, loss_before - loss_after)
        
        latency = time.perf_counter() - t0
        log.info(f"Batch updated {model_id} ({updates} steps) in {latency:.4f}s. Loss improved by {improvement:.6f}")
        
        return {
            "updates": updates,
            "final_error": float(np.mean(np.abs(y - preds_after))),
            "mean_error": float(np.mean(errors)),
            "improvement": improvement
        }

    async def predict(self, model_id: str, features: list[float]) -> float:
        t0 = time.perf_counter()
        if model_id not in self._weights:
            await self.initialize(model_id, len(features))
            
        w = self._weights[model_id]
        x = np.array(features, dtype=float)
        
        pred = float(np.dot(w, x))
        log.debug(f"Prediction for {model_id} in {time.perf_counter()-t0:.4f}s")
        return pred

    async def get_weights(self, model_id: str) -> list[float] | None:
        if model_id in self._weights:
            return self._weights[model_id].tolist()
        return None

    async def decay_learning_rate(self, model_id: str, factor: float = 0.99) -> float:
        if model_id in self._learning_rate:
            self._learning_rate[model_id] *= factor
            return self._learning_rate[model_id]
        return self._default_lr

    async def get_update_stats(self, model_id: str) -> dict[str, Any]:
        if model_id not in self._weights:
            return {"update_count": 0, "weight_norm": 0.0, "learning_rate": self._default_lr, "initialized": False}
            
        w = self._weights[model_id]
        norm = float(np.linalg.norm(w))
        
        return {
            "update_count": self._update_count[model_id],
            "weight_norm": norm,
            "learning_rate": self._learning_rate[model_id],
            "initialized": True
        }

_incremental_updater_instance = None

def get_incremental_updater() -> IncrementalModelUpdater:
    global _incremental_updater_instance
    if _incremental_updater_instance is None:
        _incremental_updater_instance = IncrementalModelUpdater()
    return _incremental_updater_instance

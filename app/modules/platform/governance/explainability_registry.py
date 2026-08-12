from __future__ import annotations
import time
import numpy as np
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class ExplainabilityRegistry:
    def __init__(self) -> None:
        # (model_id, prediction_id) -> explanation dict
        self._explanations: dict[tuple[str, str], dict[str, Any]] = {}

    async def register(self, model_id: str, prediction_id: str, feature_importance: dict[str, float], methodology: str) -> str:
        start_t = time.perf_counter()
        
        record = {
            "model_id": model_id,
            "prediction_id": prediction_id,
            "feature_importance": feature_importance,
            "methodology": methodology,
            "recorded_at": time.time()
        }
        self._explanations[(model_id, prediction_id)] = record
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Registered explanation for {model_id}/{prediction_id} in {latency:.2f}ms")
        return prediction_id

    async def get_explanation(self, model_id: str, prediction_id: str) -> dict[str, Any] | None:
        start_t = time.perf_counter()
        res = self._explanations.get((model_id, prediction_id))
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched explanation for {model_id}/{prediction_id} in {latency:.2f}ms")
        return res

    async def get_aggregate_importance(self, model_id: str) -> dict[str, float]:
        start_t = time.perf_counter()
        
        feature_scores: dict[str, list[float]] = {}
        
        for (m_id, _), record in self._explanations.items():
            if m_id == model_id:
                for feature, score in record["feature_importance"].items():
                    if feature not in feature_scores:
                        feature_scores[feature] = []
                    feature_scores[feature].append(score)
        
        aggregate: dict[str, float] = {}
        for feature, scores in feature_scores.items():
            aggregate[feature] = float(np.mean(scores))
            
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Computed aggregate importance for {model_id} in {latency:.2f}ms")
        return aggregate

    async def list_explained_predictions(self, model_id: str, limit: int = 100) -> list[dict[str, Any]]:
        start_t = time.perf_counter()
        results = [r for (m_id, _), r in self._explanations.items() if m_id == model_id]
        results.sort(key=lambda x: x["recorded_at"], reverse=True)
        results = results[:limit]
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Listed {len(results)} explanations for {model_id} in {latency:.2f}ms")
        return results

_service_instance = None

def get_explainability_registry() -> ExplainabilityRegistry:
    global _service_instance
    if _service_instance is None:
        _service_instance = ExplainabilityRegistry()
    return _service_instance

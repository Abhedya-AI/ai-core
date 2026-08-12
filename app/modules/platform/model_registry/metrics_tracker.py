from __future__ import annotations
import time
import numpy as np
from typing import Any
from app.core.logging import get_logger
from ..domain.models import ModelMetrics

log = get_logger(__name__)

class ModelMetricsTracker:
    def __init__(self) -> None:
        self._history: dict[str, list[ModelMetrics]] = {}

    async def record(self, model_id: str, metrics: ModelMetrics) -> None:
        start_t = time.perf_counter()
        
        if model_id not in self._history:
            self._history[model_id] = []
            
        self._history[model_id].append(metrics)
        
        # cap at 1000
        if len(self._history[model_id]) > 1000:
            self._history[model_id] = self._history[model_id][-1000:]
            
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Recorded metrics for {model_id} in {latency:.2f}ms")

    async def get_history(self, model_id: str, limit: int = 100) -> list[ModelMetrics]:
        start_t = time.perf_counter()
        history = self._history.get(model_id, [])
        res = history[-limit:] if limit else history
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched {len(res)} metrics history for {model_id} in {latency:.2f}ms")
        return res

    async def get_latest(self, model_id: str) -> ModelMetrics | None:
        start_t = time.perf_counter()
        history = self._history.get(model_id, [])
        res = history[-1] if history else None
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched latest metrics for {model_id} in {latency:.2f}ms")
        return res

    async def compute_trend(self, model_id: str, metric_name: str) -> dict[str, Any]:
        start_t = time.perf_counter()
        
        history = self._history.get(model_id, [])
        if not history:
            return {"error": "No history available"}
            
        recent = history[-20:]
        values = []
        for m in recent:
            val = getattr(m, metric_name, None)
            if val is not None:
                values.append(float(val))
                
        if len(values) < 2:
            return {"error": "Not enough data for trend"}
            
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        
        direction = "stable"
        if slope > 0.01:
            direction = "improving"
        elif slope < -0.01:
            direction = "degrading"
            
        trend = {
            "direction": direction,
            "slope": float(slope),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "last_value": values[-1]
        }
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Computed trend for {model_id} metric {metric_name} in {latency:.2f}ms")
        return trend

    async def detect_regression(self, model_id: str, baseline_metrics: ModelMetrics, current_metrics: ModelMetrics, threshold: float = 0.05) -> dict[str, Any]:
        start_t = time.perf_counter()
        
        regressed_metrics = []
        details = {}
        
        base_dict = baseline_metrics.model_dump()
        curr_dict = current_metrics.model_dump()
        
        # higher is better for these
        positive_metrics = ["accuracy", "precision", "recall", "f1_score", "auc_roc", "throughput_rps"]
        # lower is better for these
        negative_metrics = ["mae", "rmse", "mape", "inference_latency_ms", "memory_mb"]
        
        for k in positive_metrics:
            if base_dict.get(k) is not None and curr_dict.get(k) is not None:
                drop = (base_dict[k] - curr_dict[k]) / (base_dict[k] or 1.0)
                if drop > threshold:
                    regressed_metrics.append(k)
                    details[k] = {"baseline": base_dict[k], "current": curr_dict[k], "drop_pct": drop}
                    
        for k in negative_metrics:
            if base_dict.get(k) is not None and curr_dict.get(k) is not None:
                increase = (curr_dict[k] - base_dict[k]) / (base_dict[k] or 1.0)
                if increase > threshold:
                    regressed_metrics.append(k)
                    details[k] = {"baseline": base_dict[k], "current": curr_dict[k], "increase_pct": increase}
                    
        result = {
            "has_regression": len(regressed_metrics) > 0,
            "regressed_metrics": regressed_metrics,
            "details": details
        }
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Detected regressions for {model_id} in {latency:.2f}ms")
        return result

    async def compare_models(self, model_id_a: str, model_id_b: str) -> dict[str, Any]:
        start_t = time.perf_counter()
        
        a = await self.get_latest(model_id_a)
        b = await self.get_latest(model_id_b)
        
        if not a or not b:
            return {"error": "Missing metrics for one or both models"}
            
        a_dict = a.model_dump()
        b_dict = b.model_dump()
        
        comparison = {}
        a_wins = 0
        b_wins = 0
        
        for k in ["f1_score", "auc_roc", "accuracy"]:
            if a_dict.get(k) is not None and b_dict.get(k) is not None:
                if a_dict[k] > b_dict[k]:
                    a_wins += 1
                elif b_dict[k] > a_dict[k]:
                    b_wins += 1
                comparison[k] = {"a": a_dict[k], "b": b_dict[k], "diff": a_dict[k] - b_dict[k]}
                
        for k in ["inference_latency_ms"]:
            if a_dict.get(k) is not None and b_dict.get(k) is not None:
                if a_dict[k] < b_dict[k]:
                    a_wins += 1
                elif b_dict[k] < a_dict[k]:
                    b_wins += 1
                comparison[k] = {"a": a_dict[k], "b": b_dict[k], "diff": a_dict[k] - b_dict[k]}

        winner = model_id_a if a_wins >= b_wins else model_id_b
        
        res = {
            "winner": winner,
            "metric_comparison": comparison
        }
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Compared metrics for {model_id_a} vs {model_id_b} in {latency:.2f}ms")
        return res

_service_instance = None

def get_metrics_tracker() -> ModelMetricsTracker:
    global _service_instance
    if _service_instance is None:
        _service_instance = ModelMetricsTracker()
    return _service_instance

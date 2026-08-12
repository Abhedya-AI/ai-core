from __future__ import annotations

import time
from typing import Any
import numpy as np

from app.core.logging import get_logger

try:
    from .drift_types import DriftReport, DriftSeverity
except ImportError:
    pass

log = get_logger(__name__)

class PerformanceDriftDetector:
    def __init__(self) -> None:
        # model_id -> dict metrics
        self._baselines: dict[str, dict[str, Any]] = {}
        # model_id -> list of float
        self._rolling_windows: dict[str, list[float]] = {}
        # Track metric type: 'accuracy' or 'mae'
        self._metric_types: dict[str, str] = {}

    async def set_baseline(
        self, 
        model_id: str, 
        accuracy: float, 
        f1: float = 0.0, 
        mae: float = 0.0, 
        window_size: int = 50
    ) -> None:
        self._baselines[model_id] = {
            "accuracy": accuracy,
            "f1": f1,
            "mae": mae,
            "window_size": window_size
        }
        self._rolling_windows[model_id] = []
        if mae > 0 and accuracy == 0:
            self._metric_types[model_id] = "mae"
        else:
            self._metric_types[model_id] = "accuracy"
            
        log.info(f"Set performance baseline for {model_id}")

    async def update(self, model_id: str, correct: bool | None = None, error: float | None = None) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        if model_id not in self._baselines:
            await self.set_baseline(model_id, 0.8) # dummy
            
        base = self._baselines[model_id]
        window = self._rolling_windows[model_id]
        mtype = self._metric_types[model_id]
        
        if mtype == "accuracy" and correct is not None:
            window.append(1.0 if correct else 0.0)
        elif mtype == "mae" and error is not None:
            window.append(error)
            
        if len(window) > base["window_size"]:
            window.pop(0)
            
        rolling_metric = float(np.mean(window)) if window else 0.0
        
        drift_detected = False
        drop = 0.0
        
        if len(window) >= base["window_size"] * 0.5: # have enough data
            if mtype == "accuracy":
                drop = base["accuracy"] - rolling_metric
                drift_detected = drop > 0.05
            else: # mae
                drop = rolling_metric - base["mae"]
                drift_detected = drop > (base["mae"] * 0.1) # 10% degradation
                
        latency = time.perf_counter() - t0
        return {
            "model_id": model_id,
            "rolling_metric": rolling_metric,
            "baseline_metric": base[mtype],
            "drift_detected": drift_detected,
            "drop": drop
        }

    async def detect(self, model_id: str, recent_metrics: dict[str, float]) -> DriftReport:
        t0 = time.perf_counter()
        
        if model_id not in self._baselines:
            return DriftReport(
                model_id=model_id, drift_type="PERFORMANCE", statistical_test="ROLLING_WINDOW",
                drift_score=0.0, severity=DriftSeverity.LOW.value, drift_detected=False,
                description="No baseline set"
            )
            
        base = self._baselines[model_id]
        mtype = self._metric_types[model_id]
        
        drop = 0.0
        drift_detected = False
        
        if mtype == "accuracy" and "accuracy" in recent_metrics:
            drop = base["accuracy"] - recent_metrics["accuracy"]
            drift_detected = drop > 0.05
        elif mtype == "mae" and "mae" in recent_metrics:
            drop = recent_metrics["mae"] - base["mae"]
            # For MAE, drop means increase in error
            # Normalize to percentage of baseline
            if base["mae"] > 0:
                drop_pct = drop / base["mae"]
                drift_detected = drop_pct > 0.1
                drop = drop_pct # use percentage as drop value
                
        # Calculate score (0-1) based on drop severity
        if mtype == "accuracy":
            drift_score = min(1.0, max(0.0, drop / 0.2)) # max score at 20% drop
        else:
            drift_score = min(1.0, max(0.0, drop / 0.5)) # max score at 50% error increase
            
        if drift_score < 0.2: severity = DriftSeverity.LOW.value
        elif drift_score < 0.5: severity = DriftSeverity.MEDIUM.value
        elif drift_score < 0.8: severity = DriftSeverity.HIGH.value
        else: severity = DriftSeverity.CRITICAL.value
        
        latency = time.perf_counter() - t0
        log.info(f"Performance drift check for {model_id} in {latency:.4f}s: Detected={drift_detected}")
        
        return DriftReport(
            model_id=model_id,
            drift_type="PERFORMANCE",
            statistical_test="ROLLING_WINDOW",
            drift_score=drift_score,
            severity=severity,
            drift_detected=drift_detected,
            description=f"Performance drop: {drop:.4f}",
            metrics={"drop": drop, "baseline": base[mtype], "recent": recent_metrics.get(mtype, 0.0)}
        )

    async def get_rolling_stats(self, model_id: str) -> dict[str, Any]:
        if model_id not in self._rolling_windows or not self._rolling_windows[model_id]:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "trend": 0.0}
            
        arr = np.array(self._rolling_windows[model_id])
        
        trend = 0.0
        if len(arr) > 10:
            # Simple linear fit slope for trend
            x = np.arange(len(arr))
            z = np.polyfit(x, arr, 1)
            trend = float(z[0])
            
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "trend": trend
        }

    async def should_retrain(self, model_id: str, threshold: float = 0.05) -> bool:
        if model_id not in self._baselines or model_id not in self._rolling_windows:
            return False
            
        base = self._baselines[model_id]
        window = self._rolling_windows[model_id]
        mtype = self._metric_types[model_id]
        
        if len(window) < base["window_size"] * 0.5:
            return False
            
        rolling_metric = float(np.mean(window))
        
        if mtype == "accuracy":
            return (base["accuracy"] - rolling_metric) > threshold
        else:
            if base["mae"] > 0:
                return (rolling_metric - base["mae"]) / base["mae"] > threshold
            return False

_performance_drift_detector = None

def get_performance_drift_detector() -> PerformanceDriftDetector:
    global _performance_drift_detector
    if _performance_drift_detector is None:
        _performance_drift_detector = PerformanceDriftDetector()
    return _performance_drift_detector

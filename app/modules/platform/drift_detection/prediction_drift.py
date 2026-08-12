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

class PredictionDriftDetector:
    def _normalize_shift(self, shift: float, baseline_std: float) -> float:
        val = shift / (baseline_std + 1e-8)
        # Cap at 3 std devs
        return min(1.0, val / 3.0)

    async def detect(
        self, 
        baseline_predictions: list[float], 
        current_predictions: list[float], 
        model_id: str
    ) -> DriftReport:
        t0 = time.perf_counter()
        
        if not baseline_predictions or not current_predictions:
            return DriftReport(
                model_id=model_id, drift_type="PREDICTION", statistical_test="MEAN_SHIFT",
                drift_score=0.0, severity=DriftSeverity.LOW.value, drift_detected=False,
                description="Insufficient data"
            )
            
        b_arr = np.array(baseline_predictions, dtype=float)
        c_arr = np.array(current_predictions, dtype=float)
        
        b_mean = float(np.mean(b_arr))
        c_mean = float(np.mean(c_arr))
        b_std = float(np.std(b_arr))
        c_std = float(np.std(c_arr))
        
        mean_shift = abs(c_mean - b_mean)
        norm_shift = self._normalize_shift(mean_shift, b_std)
        
        b_var = b_std ** 2
        c_var = c_std ** 2
        
        # Avoid division by zero
        variance_ratio = c_var / (b_var + 1e-8)
        var_expansion = 0.0
        if variance_ratio > 1.5:
            var_expansion = min(1.0, (variance_ratio - 1.5) / 2.0)
            
        drift_score = min(1.0, norm_shift * 0.7 + var_expansion * 0.3)
        
        if drift_score < 0.1: severity = DriftSeverity.LOW.value
        elif drift_score < 0.2: severity = DriftSeverity.MEDIUM.value
        elif drift_score < 0.3: severity = DriftSeverity.HIGH.value
        else: severity = DriftSeverity.CRITICAL.value
        
        drift_detected = drift_score >= 0.2
        
        latency = time.perf_counter() - t0
        log.debug(f"Prediction drift for {model_id} in {latency:.4f}s: Score={drift_score:.4f}")
        
        return DriftReport(
            model_id=model_id,
            drift_type="PREDICTION",
            statistical_test="MEAN_SHIFT",
            drift_score=drift_score,
            severity=severity,
            drift_detected=drift_detected,
            description=f"Mean shift: {mean_shift:.4f}, Variance ratio: {variance_ratio:.2f}",
            metrics={
                "baseline_mean": b_mean, "current_mean": c_mean,
                "baseline_std": b_std, "current_std": c_std,
                "mean_shift": mean_shift, "variance_ratio": variance_ratio
            }
        )

    async def detect_class_imbalance(self, baseline_labels: list[int], current_labels: list[int]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        if not baseline_labels or not current_labels:
            return {"baseline_pos_rate": 0.0, "current_pos_rate": 0.0, "imbalance_delta": 0.0, "drift_detected": False}
            
        b_pos = sum(1 for x in baseline_labels if x > 0) / len(baseline_labels)
        c_pos = sum(1 for x in current_labels if x > 0) / len(current_labels)
        
        delta = abs(c_pos - b_pos)
        
        latency = time.perf_counter() - t0
        return {
            "baseline_pos_rate": b_pos,
            "current_pos_rate": c_pos,
            "imbalance_delta": delta,
            "drift_detected": delta > 0.1
        }

    async def compute_output_statistics(self, predictions: list[float]) -> dict[str, float]:
        t0 = time.perf_counter()
        if not predictions:
            return {}
            
        arr = np.array(predictions, dtype=float)
        mean = float(np.mean(arr))
        std = float(np.std(arr))
        
        # Manual skewness and kurtosis
        diffs = arr - mean
        skewness = 0.0
        kurtosis = 0.0
        if std > 1e-6:
            skewness = float(np.mean(diffs**3) / (std**3))
            kurtosis = float(np.mean(diffs**4) / (std**4) - 3.0)
            
        latency = time.perf_counter() - t0
        return {
            "mean": mean,
            "std": std,
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "p5": float(np.percentile(arr, 5)),
            "p95": float(np.percentile(arr, 95)),
            "skewness": skewness,
            "kurtosis": kurtosis
        }

_prediction_drift_detector = None

def get_prediction_drift_detector() -> PredictionDriftDetector:
    global _prediction_drift_detector
    if _prediction_drift_detector is None:
        _prediction_drift_detector = PredictionDriftDetector()
    return _prediction_drift_detector

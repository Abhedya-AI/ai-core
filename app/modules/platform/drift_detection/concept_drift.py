from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger

try:
    from .drift_types import DriftReport, DriftSeverity
except ImportError:
    pass

log = get_logger(__name__)

class ConceptDriftDetector:
    def __init__(self) -> None:
        # stream_id -> state dict
        self._state: dict[str, dict[str, Any]] = {}

    async def initialize(self, stream_id: str, delta: float = 0.005, lambda_: float = 50.0) -> None:
        t0 = time.perf_counter()
        self._state[stream_id] = {
            "sum": 0.0,
            "min_sum": 0.0,
            "count": 0,
            "mean_error": 0.0,
            "delta": delta,
            "lambda_": lambda_
        }
        log.debug(f"Initialized Page-Hinkley for {stream_id} in {time.perf_counter()-t0:.4f}s")

    async def update(self, stream_id: str, error: float) -> dict[str, Any]:
        t0 = time.perf_counter()
        if stream_id not in self._state:
            await self.initialize(stream_id)
            
        st = self._state[stream_id]
        
        st["count"] += 1
        n = st["count"]
        
        # Welford's running mean
        old_mean = st["mean_error"]
        st["mean_error"] = old_mean + (error - old_mean) / n
        
        # Update sum
        st["sum"] += error - st["mean_error"] - st["delta"]
        
        # Update min_sum
        if st["sum"] < st["min_sum"]:
            st["min_sum"] = st["sum"]
            
        ph_t = st["sum"] - st["min_sum"]
        drift_detected = ph_t > st["lambda_"]
        
        latency = time.perf_counter() - t0
        return {
            "stream_id": stream_id,
            "ph_statistic": ph_t,
            "drift_detected": drift_detected,
            "count": n,
            "mean_error": st["mean_error"]
        }

    async def update_batch(self, stream_id: str, errors: list[float]) -> dict[str, Any]:
        t0 = time.perf_counter()
        if stream_id not in self._state:
            await self.initialize(stream_id)
            
        drift_detected = False
        drift_point = None
        ph_values = []
        
        for i, err in enumerate(errors):
            res = await self.update(stream_id, err)
            ph_values.append(res["ph_statistic"])
            if res["drift_detected"] and not drift_detected:
                drift_detected = True
                drift_point = i
                
        latency = time.perf_counter() - t0
        log.info(f"Page-Hinkley batch update ({len(errors)} items) in {latency:.4f}s. Drift={drift_detected}")
        
        return {
            "drift_detected": drift_detected,
            "drift_point": drift_point,
            "ph_values": ph_values
        }

    async def reset(self, stream_id: str) -> None:
        if stream_id in self._state:
            st = self._state[stream_id]
            st["sum"] = 0.0
            st["min_sum"] = 0.0
            st["count"] = 0
            st["mean_error"] = 0.0

    async def get_state(self, stream_id: str) -> dict[str, Any] | None:
        return self._state.get(stream_id)

    async def check_drift(self, stream_id: str, recent_errors: list[float]) -> DriftReport:
        t0 = time.perf_counter()
        
        res = await self.update_batch(stream_id, recent_errors)
        
        ph_max = max(res["ph_values"]) if res["ph_values"] else 0.0
        st = self._state.get(stream_id, {})
        lambda_val = st.get("lambda_", 50.0)
        
        # normalize score relative to lambda
        drift_score = min(1.0, ph_max / (lambda_val * 1.5))
        
        if drift_score < 0.3: severity = DriftSeverity.LOW.value
        elif drift_score < 0.6: severity = DriftSeverity.MEDIUM.value
        elif drift_score < 0.9: severity = DriftSeverity.HIGH.value
        else: severity = DriftSeverity.CRITICAL.value
        
        latency = time.perf_counter() - t0
        
        return DriftReport(
            model_id=stream_id,
            drift_type="CONCEPT",
            statistical_test="PAGE_HINKLEY",
            drift_score=drift_score,
            severity=severity,
            drift_detected=res["drift_detected"],
            description=f"Page-Hinkley statistic reached {ph_max:.2f} (lambda={lambda_val})",
            metrics={"max_ph_stat": ph_max, "mean_error": st.get("mean_error", 0.0)}
        )

_concept_drift_detector = None

def get_concept_drift_detector() -> ConceptDriftDetector:
    global _concept_drift_detector
    if _concept_drift_detector is None:
        _concept_drift_detector = ConceptDriftDetector()
    return _concept_drift_detector

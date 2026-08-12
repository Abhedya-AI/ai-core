from __future__ import annotations

import time
from typing import Any
import asyncio
from datetime import datetime, timezone

from app.core.logging import get_logger

try:
    from .drift_types import DriftReport, DriftSeverity
    from .data_drift import DataDriftDetector, get_data_drift_detector
    from .concept_drift import ConceptDriftDetector, get_concept_drift_detector
    from .prediction_drift import PredictionDriftDetector, get_prediction_drift_detector
    from .feature_drift import FeatureDriftDetector, get_feature_drift_detector
    from .performance_drift import PerformanceDriftDetector, get_performance_drift_detector
except ImportError:
    pass

log = get_logger(__name__)

class DriftOrchestrator:
    def __init__(
        self,
        data_detector: Any = None,
        concept_detector: Any = None,
        prediction_detector: Any = None,
        feature_detector: Any = None,
        performance_detector: Any = None
    ) -> None:
        self.data_detector = data_detector or get_data_drift_detector()
        self.concept_detector = concept_detector or get_concept_drift_detector()
        self.prediction_detector = prediction_detector or get_prediction_drift_detector()
        self.feature_detector = feature_detector or get_feature_drift_detector()
        self.performance_detector = performance_detector or get_performance_drift_detector()
        self._history: dict[str, list[dict[str, Any]]] = {}

    def _aggregate_severity(self, reports: list[DriftReport | None]) -> DriftSeverity:
        valid_reps = [r for r in reports if r is not None]
        if not valid_reps:
            return DriftSeverity.LOW
            
        levels = {
            DriftSeverity.LOW.value: 1,
            DriftSeverity.MEDIUM.value: 2,
            DriftSeverity.HIGH.value: 3,
            DriftSeverity.CRITICAL.value: 4
        }
        
        max_level = 1
        for r in valid_reps:
            level = levels.get(r.severity, 1)
            if level > max_level:
                max_level = level
                
        reverse_map = {1: DriftSeverity.LOW, 2: DriftSeverity.MEDIUM, 3: DriftSeverity.HIGH, 4: DriftSeverity.CRITICAL}
        return reverse_map[max_level]

    async def run_full_check(self, model_id: str, context: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        log.info(f"Starting full drift check for model {model_id}")
        
        tasks = []
        task_names = []
        
        if "baseline_data" in context and "current_data" in context and "feature_name" in context:
            tasks.append(self.data_detector.detect(
                context["baseline_data"], context["current_data"], context["feature_name"]
            ))
            task_names.append("data")
            
        if "recent_errors" in context:
            tasks.append(self.concept_detector.check_drift(model_id, context["recent_errors"]))
            task_names.append("concept")
            
        if "baseline_predictions" in context and "current_predictions" in context:
            tasks.append(self.prediction_detector.detect(
                context["baseline_predictions"], context["current_predictions"], model_id
            ))
            task_names.append("prediction")
            
        if "baseline_features" in context and "current_features" in context:
            # Wrap to return overall score/drift as a report for uniform handling, or custom handling
            # For simplicity, we just run the feature drift and use overall_score
            async def run_f():
                res = await self.feature_detector.detect_all_features(model_id, context["baseline_features"], context["current_features"])
                is_drift = len(res["most_drifted"]) > 0
                score = res["overall_score"]
                sev = DriftSeverity.MEDIUM.value if is_drift else DriftSeverity.LOW.value
                if score > 0.3: sev = DriftSeverity.HIGH.value
                return DriftReport(
                    model_id=model_id, drift_type="FEATURE_ALL", statistical_test="MULTIPLE",
                    drift_score=score, severity=sev, drift_detected=is_drift,
                    description=f"{len(res['most_drifted'])} features drifted"
                )
            tasks.append(run_f())
            task_names.append("feature")
            
        if "recent_metrics" in context:
            tasks.append(self.performance_detector.detect(model_id, context["recent_metrics"]))
            task_names.append("performance")
            
        results = await asyncio.gather(*tasks)
        
        reports_dict = {name: res for name, res in zip(task_names, results)}
        
        overall_score = 0.0
        weights = {"data": 0.1, "concept": 0.3, "prediction": 0.2, "feature": 0.1, "performance": 0.4}
        total_weight = 0.0
        
        for name, rep in reports_dict.items():
            w = weights.get(name, 0.2)
            overall_score += rep.drift_score * w
            total_weight += w
            
        if total_weight > 0:
            overall_score /= total_weight
            
        overall_severity = self._aggregate_severity(list(reports_dict.values()))
        retraining_rec = overall_severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL] or overall_score > 0.6
        
        result_dict = {
            "model_id": model_id,
            "overall_drift_score": overall_score,
            "overall_severity": overall_severity.value,
            "reports": reports_dict,
            "retraining_recommended": retraining_rec,
            "detected_at": datetime.now(timezone.utc).isoformat()
        }
        
        if model_id not in self._history:
            self._history[model_id] = []
        self._history[model_id].append(result_dict)
        
        # Publish event
        try:
            from app.infrastructure.kafka.producer import EventBus
            if EventBus and any(r.drift_detected for r in reports_dict.values()):
                # mock publish
                pass
        except ImportError:
            pass
            
        latency = time.perf_counter() - t0
        log.info(f"Full drift check for {model_id} completed in {latency:.4f}s. Score={overall_score:.4f}, Retrain={retraining_rec}")
        
        return result_dict

    async def run_data_drift(self, model_id: str, baseline: list[float], current: list[float], feature_name: str) -> DriftReport:
        return await self.data_detector.detect(baseline, current, feature_name)

    async def run_concept_drift(self, model_id: str, stream_id: str, errors: list[float]) -> DriftReport:
        return await self.concept_detector.check_drift(stream_id, errors)

    async def run_performance_drift(self, model_id: str, recent_metrics: dict[str, float]) -> DriftReport:
        return await self.performance_detector.detect(model_id, recent_metrics)

    async def get_drift_history(self, model_id: str) -> list[dict[str, Any]]:
        return self._history.get(model_id, [])

_orchestrator_instance = None

def get_drift_orchestrator() -> DriftOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = DriftOrchestrator()
    return _orchestrator_instance

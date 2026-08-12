from __future__ import annotations

import time
from typing import Any
import asyncio
import numpy as np

from app.core.logging import get_logger

try:
    from .drift_types import DriftReport, DriftSeverity
except ImportError:
    pass

log = get_logger(__name__)

class FeatureDriftDetector:
    async def detect_single(
        self, 
        feature_name: str, 
        model_id: str, 
        baseline: list[float], 
        current: list[float]
    ) -> DriftReport:
        t0 = time.perf_counter()
        
        if not baseline or not current:
            return DriftReport(
                model_id=model_id, feature_name=feature_name, drift_type="FEATURE",
                statistical_test="WASSERSTEIN", drift_score=0.0, severity=DriftSeverity.LOW.value,
                drift_detected=False, description="Insufficient data"
            )
            
        b_arr = np.sort(np.array([v for v in baseline if v is not None], dtype=float))
        c_arr = np.sort(np.array([v for v in current if v is not None], dtype=float))
        
        if len(b_arr) == 0 or len(c_arr) == 0:
            return DriftReport(
                model_id=model_id, feature_name=feature_name, drift_type="FEATURE",
                statistical_test="WASSERSTEIN", drift_score=0.0, severity=DriftSeverity.LOW.value,
                drift_detected=False, description="No valid data"
            )
            
        n = max(len(b_arr), len(c_arr))
        
        x_base = np.linspace(0, 1, len(b_arr))
        x_cur = np.linspace(0, 1, len(c_arr))
        x_target = np.linspace(0, 1, n)
        
        base_interp = np.interp(x_target, x_base, b_arr)
        cur_interp = np.interp(x_target, x_cur, c_arr)
        
        wasserstein = float(np.mean(np.abs(base_interp - cur_interp)))
        
        b_std = float(np.std(b_arr))
        if b_std < 1e-6:
            norm_w = 0.0 if wasserstein < 1e-6 else 1.0
        else:
            norm_w = min(1.0, wasserstein / b_std)
            
        drift_score = norm_w
        
        if drift_score < 0.1: severity = DriftSeverity.LOW.value
        elif drift_score < 0.2: severity = DriftSeverity.MEDIUM.value
        elif drift_score < 0.3: severity = DriftSeverity.HIGH.value
        else: severity = DriftSeverity.CRITICAL.value
        
        drift_detected = drift_score >= 0.2
        
        latency = time.perf_counter() - t0
        
        return DriftReport(
            model_id=model_id,
            feature_name=feature_name,
            drift_type="FEATURE",
            statistical_test="WASSERSTEIN",
            drift_score=drift_score,
            severity=severity,
            drift_detected=drift_detected,
            description=f"Wasserstein dist: {wasserstein:.4f}",
            metrics={"wasserstein_distance": wasserstein, "normalized_distance": norm_w}
        )

    async def detect_all_features(
        self, 
        model_id: str, 
        baseline_df: dict[str, list[float]], 
        current_df: dict[str, list[float]]
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        tasks = []
        fnames = []
        for fname in baseline_df.keys():
            if fname in current_df:
                tasks.append(self.detect_single(fname, model_id, baseline_df[fname], current_df[fname]))
                fnames.append(fname)
                
        results = await asyncio.gather(*tasks)
        
        reports = {}
        drifted = []
        scores = []
        
        for rep in results:
            reports[rep.feature_name] = rep
            scores.append(rep.drift_score)
            if rep.drift_detected:
                drifted.append(rep.feature_name)
                
        # Sort drifted by score descending
        drifted.sort(key=lambda x: reports[x].drift_score, reverse=True)
        
        overall = float(np.mean(scores)) if scores else 0.0
        
        latency = time.perf_counter() - t0
        log.info(f"Feature drift check for {model_id} completed in {latency:.4f}s. {len(drifted)} drifted.")
        
        return {
            "feature_reports": reports,
            "most_drifted": drifted,
            "overall_score": overall
        }

    async def compute_feature_importance_drift(
        self, 
        baseline_importance: dict[str, float], 
        current_importance: dict[str, float]
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        common_features = set(baseline_importance.keys()).intersection(current_importance.keys())
        if not common_features:
            return {"correlation": 0.0, "drifted_features": [], "importance_shifts": {}}
            
        # Compute ranks
        b_sorted = sorted(common_features, key=lambda x: baseline_importance[x], reverse=True)
        c_sorted = sorted(common_features, key=lambda x: current_importance[x], reverse=True)
        
        b_ranks = {f: i for i, f in enumerate(b_sorted)}
        c_ranks = {f: i for i, f in enumerate(c_sorted)}
        
        n = len(common_features)
        
        # Spearman rank correlation
        d_sq = sum((b_ranks[f] - c_ranks[f])**2 for f in common_features)
        correlation = 1 - (6 * d_sq) / (n * (n**2 - 1)) if n > 1 else 1.0
        
        shifts = {}
        drifted = []
        for f in common_features:
            shift = abs(baseline_importance[f] - current_importance[f])
            shifts[f] = shift
            if shift > 0.1: # threshold
                drifted.append(f)
                
        latency = time.perf_counter() - t0
        return {
            "correlation": correlation,
            "drifted_features": drifted,
            "importance_shifts": shifts
        }

_feature_drift_detector = None

def get_feature_drift_detector() -> FeatureDriftDetector:
    global _feature_drift_detector
    if _feature_drift_detector is None:
        _feature_drift_detector = FeatureDriftDetector()
    return _feature_drift_detector

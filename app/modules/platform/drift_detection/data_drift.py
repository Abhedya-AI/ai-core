from __future__ import annotations

import time
import math
from typing import Any
import asyncio
import numpy as np

from app.core.logging import get_logger

try:
    from .drift_types import DriftReport, DriftSeverity
except ImportError:
    pass

log = get_logger(__name__)

class DataDriftDetector:
    def _compute_psi(self, baseline: np.ndarray, current: np.ndarray, n_bins: int = 10) -> float:
        min_val = min(np.min(baseline), np.min(current))
        max_val = max(np.max(baseline), np.max(current))
        
        if max_val - min_val < 1e-6:
            return 0.0
            
        bins = np.linspace(min_val, max_val, n_bins + 1)
        base_hist, _ = np.histogram(baseline, bins=bins)
        cur_hist, _ = np.histogram(current, bins=bins)
        
        base_pct = base_hist / len(baseline)
        cur_pct = cur_hist / len(current)
        
        epsilon = 1e-6
        base_pct = np.maximum(base_pct, epsilon)
        cur_pct = np.maximum(cur_pct, epsilon)
        
        base_pct = base_pct / np.sum(base_pct)
        cur_pct = cur_pct / np.sum(cur_pct)
        
        return float(np.sum((cur_pct - base_pct) * np.log(cur_pct / base_pct)))

    def _compute_ks(self, baseline: np.ndarray, current: np.ndarray) -> tuple[float, float]:
        base_sorted = np.sort(baseline)
        cur_sorted = np.sort(current)
        
        n1 = len(cur_sorted)
        n2 = len(base_sorted)
        
        if n1 == 0 or n2 == 0:
            return 0.0, 1.0
            
        data_all = np.concatenate([cur_sorted, base_sorted])
        cdf1 = np.searchsorted(cur_sorted, data_all, side='right') / n1
        cdf2 = np.searchsorted(base_sorted, data_all, side='right') / n2
        
        d_stat = float(np.max(np.abs(cdf1 - cdf2)))
        
        en = np.sqrt((n1 * n2) / (n1 + n2))
        p_val = math.exp(-2.0 * (en * d_stat) ** 2) if en * d_stat > 0 else 1.0
        
        return d_stat, min(1.0, float(p_val))

    async def detect(
        self, 
        baseline_data: list[float], 
        current_data: list[float], 
        feature_name: str, 
        threshold: float = 0.2
    ) -> DriftReport:
        t0 = time.perf_counter()
        
        if not baseline_data or not current_data:
            return DriftReport(
                feature_name=feature_name, drift_type="DATA", statistical_test="PSI+KS",
                drift_score=0.0, severity=DriftSeverity.LOW.value, drift_detected=False,
                description="Insufficient data"
            )
            
        b_arr = np.array([x for x in baseline_data if x is not None], dtype=float)
        c_arr = np.array([x for x in current_data if x is not None], dtype=float)
        
        psi = self._compute_psi(b_arr, c_arr)
        ks_stat, p_val = self._compute_ks(b_arr, c_arr)
        
        # normalize PSI roughly (often >0.2 is severe)
        norm_psi = min(1.0, psi / 0.5)
        drift_score = max(norm_psi, ks_stat)
        
        if drift_score < 0.1:
            severity = DriftSeverity.LOW.value
        elif drift_score < 0.2:
            severity = DriftSeverity.MEDIUM.value
        elif drift_score < 0.3:
            severity = DriftSeverity.HIGH.value
        else:
            severity = DriftSeverity.CRITICAL.value
            
        drift_detected = drift_score >= threshold
        
        latency = time.perf_counter() - t0
        log.debug(f"Data drift for {feature_name} in {latency:.4f}s: Score={drift_score:.4f}")
        
        return DriftReport(
            feature_name=feature_name,
            drift_type="DATA",
            statistical_test="PSI+KS",
            drift_score=drift_score,
            severity=severity,
            drift_detected=drift_detected,
            description=f"PSI={psi:.4f}, KS={ks_stat:.4f}",
            metrics={"psi": psi, "ks_stat": ks_stat, "p_value": p_val}
        )

    async def detect_categorical(self, baseline: list[str], current: list[str], feature_name: str) -> DriftReport:
        t0 = time.perf_counter()
        
        if not baseline or not current:
            return DriftReport(
                feature_name=feature_name, drift_type="DATA", statistical_test="CHI_SQ_LIKE",
                drift_score=0.0, severity=DriftSeverity.LOW.value, drift_detected=False,
                description="Insufficient data"
            )
            
        b_arr = np.array([x for x in baseline if x is not None])
        c_arr = np.array([x for x in current if x is not None])
        
        all_cats = np.unique(np.concatenate([b_arr, c_arr]))
        
        drift_score = 0.0
        n_b = len(b_arr)
        n_c = len(c_arr)
        
        for cat in all_cats:
            p_b = np.sum(b_arr == cat) / n_b
            p_c = np.sum(c_arr == cat) / n_c
            drift_score += abs(p_b - p_c)
            
        # drift_score is total variation distance (max 2.0, divide by 2 for 0-1)
        drift_score = drift_score / 2.0
        
        if drift_score < 0.1: severity = DriftSeverity.LOW.value
        elif drift_score < 0.2: severity = DriftSeverity.MEDIUM.value
        elif drift_score < 0.3: severity = DriftSeverity.HIGH.value
        else: severity = DriftSeverity.CRITICAL.value
        
        latency = time.perf_counter() - t0
        return DriftReport(
            feature_name=feature_name,
            drift_type="DATA",
            statistical_test="CATEGORICAL_DIST",
            drift_score=drift_score,
            severity=severity,
            drift_detected=drift_score >= 0.2,
            description=f"Total Variation Distance = {drift_score:.4f}",
            metrics={"tvd": drift_score}
        )

    async def detect_multivariate(
        self, 
        baseline_matrix: list[list[float]], 
        current_matrix: list[list[float]], 
        feature_names: list[str]
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        b_arr = np.array(baseline_matrix)
        c_arr = np.array(current_matrix)
        
        tasks = []
        for i, fname in enumerate(feature_names):
            if i < b_arr.shape[1] and i < c_arr.shape[1]:
                b_col = b_arr[:, i].tolist()
                c_col = c_arr[:, i].tolist()
                tasks.append(self.detect(b_col, c_col, fname))
                
        results = await asyncio.gather(*tasks)
        
        feature_reports = {}
        drifted_features = []
        scores = []
        
        for rep in results:
            feature_reports[rep.feature_name] = rep
            scores.append(rep.drift_score)
            if rep.drift_detected:
                drifted_features.append(rep.feature_name)
                
        overall_score = float(np.mean(scores)) if scores else 0.0
        
        latency = time.perf_counter() - t0
        log.info(f"Multivariate drift check completed in {latency:.4f}s. {len(drifted_features)} features drifted.")
        
        return {
            "feature_reports": feature_reports,
            "overall_drift_score": overall_score,
            "drifted_features": drifted_features
        }

_data_drift_detector = None

def get_data_drift_detector() -> DataDriftDetector:
    global _data_drift_detector
    if _data_drift_detector is None:
        _data_drift_detector = DataDriftDetector()
    return _data_drift_detector

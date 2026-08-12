from __future__ import annotations

import time
import math
from typing import Any
import numpy as np

from app.core.logging import get_logger

log = get_logger(__name__)

class FeatureStatisticsComputer:
    async def compute(self, values: list[float]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        total = len(values)
        valid_vals = [v for v in values if v is not None and not np.isnan(v)]
        null_count = total - len(valid_vals)
        null_rate = null_count / total if total > 0 else 0.0
        
        if not valid_vals:
            return {
                "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0,
                "p5": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p95": 0.0,
                "null_count": null_count, "total_count": total,
                "null_rate": null_rate, "is_constant": True
            }
            
        arr = np.array(valid_vals, dtype=float)
        
        mean = float(np.mean(arr))
        std = float(np.std(arr))
        
        stats = {
            "mean": mean,
            "std": std,
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "p5": float(np.percentile(arr, 5)),
            "p25": float(np.percentile(arr, 25)),
            "p50": float(np.percentile(arr, 50)),
            "p75": float(np.percentile(arr, 75)),
            "p95": float(np.percentile(arr, 95)),
            "null_count": null_count,
            "total_count": total,
            "null_rate": null_rate,
            "is_constant": std < 1e-6
        }
        
        latency = time.perf_counter() - t0
        log.debug(f"Computed numerical stats for {len(valid_vals)} values in {latency:.4f}s")
        return stats

    async def compute_categorical(self, values: list[str]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        valid_vals = [v for v in values if v is not None]
        total = len(valid_vals)
        
        if not valid_vals:
            return {
                "unique_count": 0, "mode": None, "mode_frequency": 0,
                "distribution": {}, "entropy": 0.0
            }
            
        counts = {}
        for v in valid_vals:
            counts[v] = counts.get(v, 0) + 1
            
        unique_count = len(counts)
        mode = max(counts.items(), key=lambda x: x[1])
        
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
                
        stats = {
            "unique_count": unique_count,
            "mode": mode[0],
            "mode_frequency": mode[1],
            "distribution": counts,
            "entropy": entropy
        }
        
        latency = time.perf_counter() - t0
        log.debug(f"Computed categorical stats for {total} values in {latency:.4f}s")
        return stats

    async def compute_embedding_stats(self, embeddings: list[list[float]]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        valid_embs = [e for e in embeddings if e is not None and len(e) > 0]
        
        if not valid_embs:
            return {
                "dimensions": 0, "mean_norm": 0.0, "std_norm": 0.0,
                "mean_vector": [], "sparsity": 0.0
            }
            
        arr = np.array(valid_embs)
        dimensions = arr.shape[1]
        
        norms = np.linalg.norm(arr, axis=1)
        mean_norm = float(np.mean(norms))
        std_norm = float(np.std(norms))
        
        mean_vector = arr.mean(axis=0).tolist()
        
        zeros = np.sum(np.abs(arr) < 1e-6)
        sparsity = float(zeros / arr.size)
        
        stats = {
            "dimensions": dimensions,
            "mean_norm": mean_norm,
            "std_norm": std_norm,
            "mean_vector": mean_vector,
            "sparsity": sparsity
        }
        
        latency = time.perf_counter() - t0
        log.debug(f"Computed embedding stats for {len(valid_embs)} vectors in {latency:.4f}s")
        return stats

    async def compute_psi(self, baseline: list[float], current: list[float], n_bins: int = 10) -> float:
        t0 = time.perf_counter()
        
        if not baseline or not current:
            return 0.0
            
        base_arr = np.array([v for v in baseline if v is not None], dtype=float)
        cur_arr = np.array([v for v in current if v is not None], dtype=float)
        
        if len(base_arr) == 0 or len(cur_arr) == 0:
            return 0.0
            
        # Define bins based on baseline quantiles to ensure equal representation if possible
        # Or simple uniform bins if min == max
        min_val = min(np.min(base_arr), np.min(cur_arr))
        max_val = max(np.max(base_arr), np.max(cur_arr))
        
        if max_val - min_val < 1e-6:
            return 0.0
            
        bins = np.linspace(min_val, max_val, n_bins + 1)
        
        base_hist, _ = np.histogram(base_arr, bins=bins)
        cur_hist, _ = np.histogram(cur_arr, bins=bins)
        
        base_pct = base_hist / len(base_arr)
        cur_pct = cur_hist / len(cur_arr)
        
        # Replace 0 with small epsilon to avoid div by zero or log(0)
        epsilon = 1e-6
        base_pct = np.maximum(base_pct, epsilon)
        cur_pct = np.maximum(cur_pct, epsilon)
        
        # Normalize again
        base_pct = base_pct / np.sum(base_pct)
        cur_pct = cur_pct / np.sum(cur_pct)
        
        psi = np.sum((cur_pct - base_pct) * np.log(cur_pct / base_pct))
        
        latency = time.perf_counter() - t0
        log.debug(f"Computed PSI: {psi:.4f} in {latency:.4f}s")
        return float(psi)

    async def compute_ks_statistic(self, baseline: list[float], current: list[float]) -> dict[str, float]:
        t0 = time.perf_counter()
        
        if not baseline or not current:
            return {"ks_statistic": 0.0, "p_value_approx": 1.0}
            
        base_arr = np.sort(np.array([v for v in baseline if v is not None], dtype=float))
        cur_arr = np.sort(np.array([v for v in current if v is not None], dtype=float))
        
        n1 = len(cur_arr)
        n2 = len(base_arr)
        
        if n1 == 0 or n2 == 0:
            return {"ks_statistic": 0.0, "p_value_approx": 1.0}
            
        data_all = np.concatenate([cur_arr, base_arr])
        cdf1 = np.searchsorted(cur_arr, data_all, side='right') / n1
        cdf2 = np.searchsorted(base_arr, data_all, side='right') / n2
        
        d_stat = float(np.max(np.abs(cdf1 - cdf2)))
        
        # Approximate p-value
        en = np.sqrt((n1 * n2) / (n1 + n2))
        p_val = math.exp(-2.0 * (en * d_stat) ** 2) if en * d_stat > 0 else 1.0
        
        latency = time.perf_counter() - t0
        return {
            "ks_statistic": d_stat,
            "p_value_approx": min(1.0, float(p_val))
        }

    async def compute_wasserstein(self, baseline: list[float], current: list[float]) -> float:
        t0 = time.perf_counter()
        
        if not baseline or not current:
            return 0.0
            
        base_arr = np.sort(np.array([v for v in baseline if v is not None], dtype=float))
        cur_arr = np.sort(np.array([v for v in current if v is not None], dtype=float))
        
        if len(base_arr) == 0 or len(cur_arr) == 0:
            return 0.0
            
        n = max(len(base_arr), len(cur_arr))
        
        # Interpolate to same length
        x_base = np.linspace(0, 1, len(base_arr))
        x_cur = np.linspace(0, 1, len(cur_arr))
        x_target = np.linspace(0, 1, n)
        
        base_interp = np.interp(x_target, x_base, base_arr)
        cur_interp = np.interp(x_target, x_cur, cur_arr)
        
        wasserstein = np.mean(np.abs(base_interp - cur_interp))
        
        latency = time.perf_counter() - t0
        return float(wasserstein)

_stats_computer_instance = None

def get_feature_statistics_computer() -> FeatureStatisticsComputer:
    global _stats_computer_instance
    if _stats_computer_instance is None:
        _stats_computer_instance = FeatureStatisticsComputer()
    return _stats_computer_instance

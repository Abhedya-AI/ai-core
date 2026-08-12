from __future__ import annotations

import math
import numpy as np

class ConfidenceBandCalculator:
    @staticmethod
    def analytical_bands(predictions: list[float], residual_std: float, n_train: int, level: float = 0.95) -> tuple[list[float], list[float]]:
        # Approximate t-value for 95% is ~1.96
        # A more precise one could use scipy, but using 1.96 as standard Gaussian approximation
        z = 1.96 if level == 0.95 else 2.58
        
        lower, upper = [], []
        for i, p in enumerate(predictions):
            # standard error grows with sqrt(h)
            se = residual_std * math.sqrt(i + 1) * math.sqrt(1 + 1/max(n_train, 1))
            margin = z * se
            lower.append(p - margin)
            upper.append(p + margin)
        return lower, upper

    @staticmethod
    def bootstrap_bands(series: list[float], n_bootstrap: int = 200, level: float = 0.95) -> tuple[list[float], list[float]]:
        # Simulating bands directly from historical empirical distribution
        y = np.array(series, dtype=float)
        samples = np.random.choice(y, size=(n_bootstrap, len(y)), replace=True)
        lower = np.percentile(samples, (1 - level)/2 * 100, axis=0)
        upper = np.percentile(samples, (1 + level)/2 * 100, axis=0)
        return lower.tolist(), upper.tolist()

    @staticmethod
    def propagated_bands(base_lower: list[float], base_upper: list[float], steps_ahead: int) -> tuple[list[float], list[float]]:
        new_lower = []
        new_upper = []
        for i in range(steps_ahead):
            idx = min(i, len(base_lower) - 1)
            margin = (base_upper[idx] - base_lower[idx]) / 2.0
            # Propagate uncertainty
            inflated_margin = margin * math.sqrt((i + 1) / max(idx + 1, 1))
            center = (base_upper[idx] + base_lower[idx]) / 2.0
            new_lower.append(center - inflated_margin)
            new_upper.append(center + inflated_margin)
        return new_lower, new_upper

    @staticmethod
    def combine_bands(bands_list: list[tuple[list[float], list[float]]]) -> tuple[list[float], list[float]]:
        if not bands_list:
            return [], []
            
        length = len(bands_list[0][0])
        combined_lower = []
        combined_upper = []
        
        for i in range(length):
            lows = [b[0][i] for b in bands_list]
            highs = [b[1][i] for b in bands_list]
            combined_lower.append(min(lows))
            combined_upper.append(max(highs))
            
        return combined_lower, combined_upper

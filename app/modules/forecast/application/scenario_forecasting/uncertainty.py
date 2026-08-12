from __future__ import annotations
import uuid
from datetime import datetime, timezone
import math
import numpy as np

from app.core.logging import get_logger
log = get_logger(__name__)

class UncertaintyQuantifier:
    """Quantifies uncertainty in forecasts using Monte Carlo sampling."""

    def __init__(self, n_samples: int = 500) -> None:
        self.n_samples = n_samples

    def quantify(self, base_value: float, model_uncertainty: float, data_uncertainty: float, horizon_days: float) -> dict:
        """Quantify uncertainty and return confidence intervals."""
        log.info(f"Quantifying uncertainty for horizon {horizon_days}d")
        
        combined_std = self._compute_combined_uncertainty(model_uncertainty, data_uncertainty, horizon_days)
        
        # Draw samples
        samples = np.random.normal(base_value, combined_std, self.n_samples)
        
        # Calculate percentiles
        p5, p25, p50, p75, p95 = np.percentile(samples, [5, 25, 50, 75, 95])
        
        # Normalize uncertainty score to [0,1]
        score = float(np.clip(combined_std / max(1e-5, base_value), 0.0, 1.0))
        
        sources = self._classify_uncertainty_sources(model_uncertainty, data_uncertainty, horizon_days)
        
        return {
            "p5": float(p5),
            "p25": float(p25),
            "p50": float(p50),
            "p75": float(p75),
            "p95": float(p95),
            "std": float(combined_std),
            "uncertainty_score": score,
            "uncertainty_sources": sources
        }

    def _compute_combined_uncertainty(self, model_uncertainty: float, data_uncertainty: float, horizon_days: float) -> float:
        """Compute combined uncertainty growing with time."""
        # Uncertainty grows with sqrt of time
        time_factor = math.sqrt(max(1.0, horizon_days))
        base_u = math.sqrt(model_uncertainty**2 + data_uncertainty**2)
        return float(base_u * time_factor)

    def _classify_uncertainty_sources(self, model_u: float, data_u: float, horizon_days: float) -> list[str]:
        """Classify main sources of uncertainty."""
        sources = []
        if model_u > data_u * 1.5:
            sources.append("Model Variance")
        elif data_u > model_u * 1.5:
            sources.append("Data Sparsity/Noise")
        else:
            sources.append("Balanced Model/Data Uncertainty")
            
        if horizon_days > 7.0:
            sources.append("Long Horizon Extrapolation")
            
        return sources

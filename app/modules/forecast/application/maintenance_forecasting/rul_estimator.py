from __future__ import annotations
import uuid
from datetime import datetime, timezone
import numpy as np

from app.core.logging import get_logger
log = get_logger(__name__)

class RULEstimator:
    """Estimator for Remaining Useful Life (RUL) of equipment."""

    def __init__(self, failure_threshold: float = 0.2, safety_margin_pct: float = 0.1) -> None:
        self.failure_threshold = failure_threshold
        self.safety_margin_pct = safety_margin_pct

    async def estimate_rul(self, equipment_id: str, current_health: float, degradation_rate: float, maintenance_history: list[dict]) -> dict:
        """Estimate RUL based on current health and degradation rate."""
        log.info(f"Estimating RUL for {equipment_id}")
        
        base_rul = self._compute_rul_from_curve(current_health, degradation_rate, self.failure_threshold)
        
        rul = self._apply_maintenance_correction(base_rul, maintenance_history)
        
        # Confidence based on amount of history and rate
        confidence = self._calibrate_confidence(degradation_rate, len(maintenance_history), 0.85)
        
        recommended_before = max(0.0, rul * (1.0 - self.safety_margin_pct))
        replacement = current_health < self.failure_threshold
        
        evidence = [
            f"Current health is {current_health:.2f}",
            f"Degradation rate is {degradation_rate:.4f} per hour",
            f"Recent maintenance events: {len(maintenance_history)}"
        ]
        
        return {
            "rul_hours": float(rul),
            "rul_days": float(rul / 24.0),
            "confidence": float(confidence),
            "maintenance_recommended_before_hours": float(recommended_before),
            "replacement_recommended": replacement,
            "supporting_evidence": evidence
        }

    def _compute_rul_from_curve(self, health: float, rate: float, threshold: float) -> float:
        """Compute RUL strictly from linear assumption for now."""
        if health <= threshold:
            return 0.0
        if rate <= 1e-5:
            return 8760.0 # 1 year max assumed
        return (health - threshold) / rate

    def _apply_maintenance_correction(self, rul: float, maintenance_history: list[dict]) -> float:
        """Apply corrections based on recent maintenance."""
        if not maintenance_history:
            return rul
            
        # Example logic: frequent maintenance might mean higher instability, or better upkeep.
        # Let's say recent maintenance increases RUL slightly due to new parts.
        correction_factor = 1.0 + (len(maintenance_history) * 0.05)
        return rul * correction_factor

    def _calibrate_confidence(self, degradation_rate: float, data_points: int, r_squared: float) -> float:
        """Calibrate confidence of the RUL prediction."""
        base = r_squared
        # More data points -> higher confidence
        points_factor = min(data_points / 10.0, 1.0)
        
        # Extremely high degradation rate is harder to predict accurately
        rate_penalty = min(abs(degradation_rate) * 10.0, 0.2)
        
        return float(np.clip((base * 0.7) + (points_factor * 0.3) - rate_penalty, 0.1, 0.99))

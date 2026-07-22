"""
application/calculate_risk.py — Risk engine use-case.

Responsibility: given a HazardType and confidence, calculate the RiskScore.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.domain.enums import HazardType, RiskLevel
from app.modules.vision.domain.value_objects import RiskScore

log = get_logger("vision.risk_engine")

# ── Hazard weights ────────────────────────────────────────────────────────────
_HAZARD_WEIGHTS: dict[HazardType, float] = {
    HazardType.FIRE:           0.90,
    HazardType.CHEMICAL_SPILL: 0.85,
    HazardType.FALL:           0.80,
    HazardType.SMOKE:          0.65,
    HazardType.NO_HELMET:      0.55,
    HazardType.NO_SAFETY_VEST: 0.45,
    HazardType.MACHINERY:      0.30,
    HazardType.PERSON:         0.10,
    HazardType.HELMET:         0.00,
    HazardType.SAFETY_VEST:    0.00,
    HazardType.UNKNOWN:        0.05,
}

# ── RiskLevel thresholds ──────────────────────────────────────────────────────
_LEVEL_THRESHOLDS: list[tuple[float, RiskLevel]] = [
    (0.75, RiskLevel.CRITICAL),
    (0.50, RiskLevel.HIGH),
    (0.25, RiskLevel.MEDIUM),
    (0.00, RiskLevel.LOW),
]


def _score_to_level(score: float) -> RiskLevel:
    """Map a continuous [0, 1] score to a discrete RiskLevel."""
    for threshold, level in _LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return RiskLevel.LOW


# ── Hazard description templates ──────────────────────────────────────────────
_HAZARD_DESCRIPTIONS: dict[HazardType, str] = {
    HazardType.FIRE:           "Active fire detected in frame.",
    HazardType.CHEMICAL_SPILL: "Potential chemical spill detected.",
    HazardType.FALL:           "Worker fall incident detected.",
    HazardType.SMOKE:          "Smoke or fume accumulation detected.",
    HazardType.NO_HELMET:      "Worker without helmet detected — PPE non-compliance.",
    HazardType.NO_SAFETY_VEST: "Worker without high-visibility vest — PPE non-compliance.",
    HazardType.MACHINERY:      "Heavy machinery in proximity to personnel.",
    HazardType.PERSON:         "Person detected in zone.",
    HazardType.HELMET:         "Worker with helmet detected — compliant.",
    HazardType.SAFETY_VEST:    "Worker with safety vest detected — compliant.",
    HazardType.UNKNOWN:        "Unidentified object detected.",
}


class RiskEngine:
    """
    Calculates a RiskScore from a hazard type and confidence level.
    """

    def calculate(self, hazard_type: HazardType, confidence: float) -> RiskScore:
        """
        Compute risk score for a single detection.
        """
        base_weight = _HAZARD_WEIGHTS.get(hazard_type, 0.0)
        score = min(max(base_weight * confidence, 0.0), 1.0)
        level = _score_to_level(score)
        description = _HAZARD_DESCRIPTIONS.get(hazard_type, "Unknown hazard detected.")
        reason = f"{description} (Confidence: {confidence * 100:.1f}%)"

        return RiskScore(
            score=round(score, 4),
            level=level,
            reason=reason,
        )

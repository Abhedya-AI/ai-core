"""
application/calculate_risk.py — Risk engine use-case.

Responsibility: given a list of Detection domain objects, aggregate a
frame-level RiskScore and produce an actionable list of Hazard objects.

Design notes
────────────
• One Hazard is created per unique HazardType (deduped).
• The per-hazard contribution is: weight × max(confidence) across all
  detections of that type.
• Frame risk = min(sum of contributions, 1.0).
• Compliant detections (HELMET, SAFETY_VEST) produce a Hazard with
  weight 0.0 — present in the hazards list for audit but carry no risk.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.domain.entities.hazard import Hazard
from app.modules.vision.domain.enums import HazardType, RiskLevel
from app.modules.vision.domain.value_objects import RiskScore

log = get_logger("vision.risk_engine")

# ── Hazard weights ─────────────────────────────────────────────────────────────
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

# ── RiskLevel thresholds ───────────────────────────────────────────────────────
_LEVEL_THRESHOLDS: list[tuple[float, RiskLevel]] = [
    (0.75, RiskLevel.CRITICAL),
    (0.50, RiskLevel.HIGH),
    (0.25, RiskLevel.MEDIUM),
    (0.00, RiskLevel.LOW),
]

# ── Human-readable hazard descriptions ────────────────────────────────────────
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


def _score_to_level(score: float) -> RiskLevel:
    """Map a continuous [0, 1] score to a discrete RiskLevel."""
    for threshold, level in _LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return RiskLevel.LOW


class RiskEngine:
    """
    Aggregates risk across all detections in a frame.

    Usage
    ─────
        engine = RiskEngine()
        risk_score, hazards = engine.calculate(detections)
    """

    def calculate(
        self,
        detections: list,  # list[Detection] — avoids circular import
    ) -> tuple[RiskScore, list[Hazard]]:
        """
        Compute the frame-level RiskScore and deduplicated Hazard list.

        Parameters
        ──────────
        detections  List of Detection domain objects for a single frame.

        Returns
        ───────
        (RiskScore, list[Hazard])
        """
        if not detections:
            return (
                RiskScore(score=0.0, level=RiskLevel.LOW, reason="No detections in frame."),
                [],
            )

        # ── Aggregate max confidence per hazard type ───────────────────────────
        best_conf: dict[HazardType, float] = {}
        for det in detections:
            ht = det.hazard_type
            best_conf[ht] = max(best_conf.get(ht, 0.0), det.confidence)

        # ── Build Hazard list and sum contributions ────────────────────────────
        hazards: list[Hazard] = []
        total_score: float = 0.0

        for hazard_type, max_conf in best_conf.items():
            weight      = _HAZARD_WEIGHTS.get(hazard_type, 0.0)
            description = _HAZARD_DESCRIPTIONS.get(hazard_type, "Unknown hazard.")
            contribution = weight * max_conf

            hazards.append(
                Hazard(
                    hazard_type=hazard_type,
                    weight=weight,
                    description=description,
                    max_confidence=max_conf,
                )
            )
            total_score += contribution

        # ── Cap and finalise ───────────────────────────────────────────────────
        final_score = min(round(total_score, 4), 1.0)
        level       = _score_to_level(final_score)

        # Build a human-readable reason from the dominant hazards
        active = sorted(
            [h for h in hazards if h.weight > 0.0],
            key=lambda h: h.weight,
            reverse=True,
        )
        if active:
            parts = [f"{h.hazard_type.value}(w={h.weight:.2f})" for h in active[:3]]
            reason = f"Frame risk driven by: {', '.join(parts)}."
        else:
            reason = "All detections are compliant — no risk contribution."

        risk_score = RiskScore(score=final_score, level=level, reason=reason)
        log.debug(
            f"RiskEngine.calculate(): {len(detections)} detections → "
            f"score={final_score} level={level}"
        )
        return risk_score, hazards

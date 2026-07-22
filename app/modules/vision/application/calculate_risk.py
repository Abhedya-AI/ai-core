"""
application/calculate_risk.py — Risk engine use-case.

Responsibility: given a list of domain Detections, produce a RiskScore
and a list of domain Hazards.

Design
──────
• Pure business logic — no I/O, no model calls, no HTTP.
• Hazard weights and level thresholds are centralised here.

Future: Risk Policy Engine
──────────────────────────
In a later milestone these tables will move to:

    domain/policies/risk_policy.py

so the safety team can adjust thresholds without touching use-case code.
For now, keeping them here is the simplest correct design.

Scoring algorithm (v1 — additive, capped at 1.0)
──────────────────────────────────────────────────
  1.  For each Detection, look up its base weight by HazardType.
  2.  Multiply by the detection's confidence score.
  3.  Sum all weighted contributions.
  4.  Cap at 1.0.
  5.  Map the continuous score to a discrete RiskLevel.
  6.  Build a Hazard for each Detection (1-to-1 mapping in Milestone 1).
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.modules.vision.domain.entities import Detection, Hazard
from app.modules.vision.domain.enums import HazardType, RiskLevel
from app.modules.vision.domain.value_objects import RiskScore

log = get_logger("vision.risk_engine")

# ── Hazard weights ────────────────────────────────────────────────────────────
# Values represent the per-detection contribution to the frame risk score.
# Sum of all detections is capped at 1.0 after confidence weighting.

_HAZARD_WEIGHTS: dict[HazardType, float] = {
    # Critical environmental hazards — maximum weight
    HazardType.FIRE:           0.90,
    HazardType.CHEMICAL_SPILL: 0.85,
    HazardType.FALL:           0.80,

    # Smoke — high but slightly lower than direct fire
    HazardType.SMOKE:          0.65,

    # PPE non-compliance — significant but not immediately fatal
    HazardType.NO_HELMET:      0.55,
    HazardType.NO_SAFETY_VEST: 0.45,

    # Machinery presence — contextual, not inherently dangerous
    HazardType.MACHINERY:      0.30,

    # Presence-only detections — informational
    HazardType.PERSON:         0.10,

    # Compliant detections — no risk contribution
    HazardType.HELMET:         0.00,
    HazardType.SAFETY_VEST:    0.00,

    # Unknown — treated as low risk until identified
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


# ── Public interface ──────────────────────────────────────────────────────────

class RiskEngine:
    """
    Calculates a RiskScore and derives Hazards from a list of Detections.

    Usage
    ─────
        engine = RiskEngine()
        risk_score, hazards = engine.calculate(detections)
    """

    def calculate(
        self, detections: list[Detection]
    ) -> tuple[RiskScore, list[Hazard]]:
        """
        Compute frame risk from a list of domain Detections.

        Parameters
        ──────────
        detections  All detections for a single frame.

        Returns
        ───────
        (RiskScore, list[Hazard])
        """
        if not detections:
            log.debug("No detections — returning zero risk score.")
            return (
                RiskScore(score=0.0, level=RiskLevel.LOW, reason="No hazards detected."),
                [],
            )

        contributions: list[tuple[HazardType, float]] = []
        hazards: list[Hazard] = []

        for det in detections:
            base_weight = _HAZARD_WEIGHTS.get(det.hazard_type, 0.0)
            weighted    = base_weight * det.confidence
            contributions.append((det.hazard_type, weighted))

            hazard_level = _score_to_level(weighted)
            description  = _HAZARD_DESCRIPTIONS.get(
                det.hazard_type, "Unknown hazard detected."
            )

            hazards.append(
                Hazard(
                    hazard_type=det.hazard_type,
                    confidence=det.confidence,
                    risk_level=hazard_level,
                    bounding_box=det.bounding_box,
                    source_detection_ids=[det.id],
                    description=description,
                )
            )

        # Aggregate: sum all contributions, cap at 1.0
        raw_score = min(sum(w for _, w in contributions), 1.0)
        level     = _score_to_level(raw_score)

        # Sort contributions descending for explainability
        contributions.sort(key=lambda x: x[1], reverse=True)

        # Build a human-readable reason string from top contributors
        top = contributions[:3]
        reason_parts = [
            f"{h.value}({w:.2f})" for h, w in top if w > 0
        ]
        reason = (
            f"Top contributors: {', '.join(reason_parts)}"
            if reason_parts
            else "No significant risk contributors."
        )

        risk_score = RiskScore(
            score=round(raw_score, 4),
            level=level,
            reason=reason,
        )

        log.debug(
            f"Risk calculated: score={risk_score.score:.3f} "
            f"level={risk_score.level.value} "
            f"hazards={len(hazards)}"
        )

        return risk_score, hazards

"""
intelligence/compliance_engine.py — Overall Safety Compliance Engine.

Aggregates evaluations from PPE, Unsafe Behavior, Restricted Zone, and Interaction
engines into a unified Safety Compliance Index (%) for a Zone or Plant.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

log = get_logger("vision.intelligence.compliance")


class SafetyComplianceEngine:
    """Engine aggregating multi-dimensional vision evaluations into a unified compliance index."""

    def compute_compliance_index(
        self,
        zone_id: str,
        ppe_compliance_pct: float,
        behavior_violation_count: int,
        restricted_zone_breach_count: int,
        unsafe_interaction_count: int,
        total_evaluations: int = 100,
    ) -> dict[str, Any]:
        """
        Compute overall compliance score (0.0 - 100.0%).
        """
        deductions = (
            (behavior_violation_count * 10)
            + (restricted_zone_breach_count * 15)
            + (unsafe_interaction_count * 10)
        )

        overall_index = max(0.0, min(100.0, ppe_compliance_pct - deductions))
        overall_index = round(overall_index, 1)

        grade = "A" if overall_index >= 90 else ("B" if overall_index >= 75 else ("C" if overall_index >= 60 else "D"))

        return {
            "zone_id": zone_id,
            "overall_compliance_index": overall_index,
            "grade": grade,
            "ppe_compliance_pct": ppe_compliance_pct,
            "behavior_violation_count": behavior_violation_count,
            "restricted_zone_breach_count": restricted_zone_breach_count,
            "unsafe_interaction_count": unsafe_interaction_count,
            "total_evaluations": total_evaluations,
            "status": "COMPLIANT" if overall_index >= 75.0 else "NON_COMPLIANT",
        }

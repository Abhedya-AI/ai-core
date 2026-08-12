"""
intelligence/action_generator.py — Actionable Safety Protocol Generator.

Generates immediate, medium-term, and preventive corrective action plans
from vision intelligence assessments.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.entities.vision_assessment import VisionRecommendation

log = get_logger("vision.intelligence.action_generator")


class ActionGenerator:
    """Generator compiling actionable safety recommendations."""

    @staticmethod
    def generate_actions(
        assessment_type: str,
        severity: str,
        zone_id: str,
        worker_id: str | None = None,
        equipment_id: str | None = None,
    ) -> list[VisionRecommendation]:
        """Generate recommendations based on assessment parameters."""
        recs: list[VisionRecommendation] = []
        sev_upper = severity.upper()

        if sev_upper in ("CRITICAL", "EMERGENCY"):
            recs.append(
                VisionRecommendation(
                    title=f"Immediate Halt / Dispatch for {assessment_type} in Zone {zone_id}",
                    description=f"Critical safety breach in Zone {zone_id}. Immediate officer dispatch required.",
                    target_role="Safety Supervisor",
                    priority="CRITICAL",
                    action_type="HALT_WORK_DISPATCH",
                )
            )

        if assessment_type == "PPE":
            recs.append(
                VisionRecommendation(
                    title="Provide Missing PPE Equipment",
                    description=f"Worker {worker_id or 'unidentified'} requires immediate PPE compliance verification in Zone {zone_id}.",
                    target_role="Shift Lead",
                    priority="HIGH" if sev_upper == "HIGH" else "MEDIUM",
                    action_type="SUPPLY_PPE",
                )
            )

        elif assessment_type == "INTERACTION":
            recs.append(
                VisionRecommendation(
                    title="Activate Proximity Audio Alarm",
                    description=f"Worker near equipment {equipment_id or 'machinery'}. Sound local zone alarm.",
                    target_role="Operator",
                    priority="HIGH",
                    action_type="SOUND_ALARM",
                )
            )

        elif assessment_type == "ZONE":
            recs.append(
                VisionRecommendation(
                    title="Escort Unauthorized Person Out of Zone",
                    description=f"Unauthorized access to zone {zone_id}. Security escort required.",
                    target_role="Security",
                    priority="HIGH",
                    action_type="SECURITY_ESCORT",
                )
            )

        if not recs:
            recs.append(
                VisionRecommendation(
                    title="Routine Safety Audit",
                    description=f"Conduct standard safety walkthrough for Zone {zone_id}.",
                    target_role="Inspector",
                    priority="LOW",
                    action_type="AUDIT",
                )
            )

        return recs

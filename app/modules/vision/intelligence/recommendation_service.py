"""
intelligence/recommendation_service.py — Recommendation Service Facade.

Combines PolicyMapper and ActionGenerator into a unified recommendation service facade.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.entities.vision_assessment import VisionRecommendation
from app.modules.vision.intelligence.action_generator import ActionGenerator
from app.modules.vision.intelligence.policy_mapper import PolicyMapper

log = get_logger("vision.intelligence.recommendation")


class RecommendationService:
    """Facade orchestrating policy mapping and recommendation generation."""

    def __init__(
        self,
        policy_mapper: PolicyMapper | None = None,
        action_generator: ActionGenerator | None = None,
    ) -> None:
        self._policy_mapper = policy_mapper or PolicyMapper()
        self._action_generator = action_generator or ActionGenerator()

    def generate_recommendations(
        self,
        assessment_type: str,
        severity: str,
        zone_id: str,
        worker_id: str | None = None,
        equipment_id: str | None = None,
    ) -> list[VisionRecommendation]:
        """Generate structured recommendations attached with applicable regulatory policies."""
        policies = self._policy_mapper.map_policies(assessment_type)
        policy_str = ", ".join(f"{p['code']} ({p['title']})" for p in policies)

        recs = self._action_generator.generate_actions(
            assessment_type=assessment_type,
            severity=severity,
            zone_id=zone_id,
            worker_id=worker_id,
            equipment_id=equipment_id,
        )

        # Attach policy references to recommendations
        for r in recs:
            r.policy_reference = policy_str

        return recs

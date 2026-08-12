"""recommendation_engine.py — Actionable Recommendation Generation Engine."""
from __future__ import annotations

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Investigation, PrimaryCause, ContributingFactor, Evidence,
    Recommendation, CorrectiveAction, PreventiveAction,
    RecommendationType, RecommendationPriority,
)

log = get_logger("root_cause.recommendation")

_PRIORITY_ORDER = {
    RecommendationPriority.CRITICAL: 1,
    RecommendationPriority.HIGH: 2,
    RecommendationPriority.MEDIUM: 3,
    RecommendationPriority.LOW: 4,
}


class RecommendationEngine:
    """Generates prioritized recommendations from investigation results."""

    def generate_recommendations(
        self,
        investigation: Investigation,
        primary_cause: PrimaryCause | None,
        contributing_factors: list[ContributingFactor],
        evidence_list: list[Evidence],
    ) -> list[Recommendation]:
        log.info(f"Generating recommendations for investigation {investigation.id}")
        recs: list[Recommendation] = []
        recs.extend(self.generate_immediate_actions(
            severity="HIGH", zone_id=investigation.zone_id, evidence=evidence_list,
        ))
        if primary_cause:
            recs.extend(self.generate_corrective_actions(primary_cause))
        if contributing_factors:
            recs.extend(self.generate_preventive_actions(contributing_factors))
        equipment_ids = list({e.equipment_id for e in evidence_list if e.equipment_id})
        if equipment_ids:
            recs.extend(self.generate_maintenance_tasks(equipment_ids))
        recs.extend(self.generate_compliance_recommendations(evidence_list))
        return recs

    def generate_immediate_actions(
        self, severity: str, zone_id: str | None, evidence: list[Evidence],
    ) -> list[Recommendation]:
        severe = [e for e in evidence if e.severity in (severity, "CRITICAL")]
        if not severe:
            return []
        return [
            Recommendation(
                recommendation_type=RecommendationType.IMMEDIATE_ACTION,
                priority=RecommendationPriority.CRITICAL,
                title="Immediate Safety Mitigation",
                description=f"Apply immediate mitigation for {len(severe)} high/critical evidence items.",
                target_role="Safety Officer",
                action_deadline_hours=1,
                evidence_ids=[e.id for e in severe[:5]],
                zone_ids=[zone_id] if zone_id else [],
            )
        ]

    def generate_corrective_actions(
        self, primary_cause: PrimaryCause | None,
    ) -> list[CorrectiveAction]:
        if not primary_cause:
            return []
        return [
            CorrectiveAction(
                recommendation_type=RecommendationType.CORRECTIVE_ACTION,
                priority=RecommendationPriority.HIGH,
                title="Resolve Primary Root Cause",
                description=f"Address root cause: {primary_cause.description}",
                target_role="Maintenance Lead",
                action_deadline_hours=24,
                evidence_ids=primary_cause.evidence_ids[:3],
                corrective_measure=f"Investigate and rectify: {primary_cause.description}",
                root_cause_reference=primary_cause.hypothesis_id,
            )
        ]

    def generate_preventive_actions(
        self, contributing_factors: list[ContributingFactor],
    ) -> list[PreventiveAction]:
        actions: list[PreventiveAction] = []
        for cf in contributing_factors:
            priority = (
                RecommendationPriority.MEDIUM if cf.confidence > 0.5
                else RecommendationPriority.LOW
            )
            actions.append(PreventiveAction(
                recommendation_type=RecommendationType.PREVENTIVE_ACTION,
                priority=priority,
                title=f"Prevent recurrence: {cf.description[:50]}",
                description=f"Preventive measure for: {cf.description}",
                target_role="Safety Officer",
                evidence_ids=cf.evidence_ids[:3],
                prevention_strategy=cf.mitigation or f"Implement safeguards for: {cf.description}",
                recurrence_risk="MEDIUM" if cf.confidence > 0.5 else "LOW",
            ))
        return actions

    def generate_maintenance_tasks(
        self, equipment_ids: list[str],
    ) -> list[Recommendation]:
        return [
            Recommendation(
                recommendation_type=RecommendationType.MAINTENANCE_TASK,
                priority=RecommendationPriority.MEDIUM,
                title=f"Inspect equipment {eq_id}",
                description=f"Perform comprehensive inspection and diagnostic on equipment {eq_id}.",
                target_role="Maintenance Technician",
                action_deadline_hours=48,
                equipment_ids=[eq_id],
            )
            for eq_id in equipment_ids
        ]

    def generate_compliance_recommendations(
        self, evidence_list: list[Evidence],
    ) -> list[Recommendation]:
        if len(evidence_list) <= 5:
            return []
        return [
            Recommendation(
                recommendation_type=RecommendationType.COMPLIANCE,
                priority=RecommendationPriority.LOW,
                title="Process Compliance Review",
                description="High volume of evidence detected. Review operational procedures for compliance gaps.",
                target_role="Compliance Officer",
            )
        ]

    def prioritize_recommendations(
        self, recs: list[Recommendation],
    ) -> list[Recommendation]:
        return sorted(recs, key=lambda r: _PRIORITY_ORDER.get(r.priority, 5))

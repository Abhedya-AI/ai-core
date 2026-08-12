"""scenario_builder.py — Build counterfactual intervention scenarios.

Provides factory methods for the 6 standard scenario types:
  1. MAINTENANCE_COMPLETED — what if scheduled maintenance had been done?
  2. PPE_COMPLIANT — what if all workers had correct PPE?
  3. EARLIER_DETECTION — what if emergency was detected N minutes earlier?
  4. SENSOR_AVAILABLE — what if the failed sensor had been operational?
  5. EVACUATION_TRIGGERED — what if evacuation was triggered immediately?
  6. CUSTOM_INTERVENTION — user-defined intervention hypothesis
"""
from __future__ import annotations
from typing import Any

from app.modules.root_cause.domain.models import (
    Investigation, InvestigationReport, CounterfactualScenario, ScenarioType,
)


class ScenarioBuilder:
    """Factory for creating typed counterfactual intervention scenarios."""

    def build_maintenance_scenario(
        self,
        investigation: Investigation,
        report: InvestigationReport,
        days_overdue: int = 30,
    ) -> CounterfactualScenario:
        """Build scenario: maintenance had been completed on schedule."""
        primary_desc = investigation.primary_cause.description if investigation.primary_cause else "Equipment failure"
        equipment_ids = investigation.equipment_ids or ["unspecified equipment"]
        return CounterfactualScenario(
            investigation_id=investigation.id,
            scenario_type=ScenarioType.MAINTENANCE_COMPLETED,
            intervention_description=(
                f"Scheduled maintenance completed {days_overdue} days before incident. "
                f"Equipment: {', '.join(equipment_ids[:3])}."
            ),
            original_root_cause=primary_desc,
            alternative_root_cause="Incident likely prevented by maintained equipment condition.",
            risk_reduction_pct=self._estimate_maintenance_risk_reduction(
                investigation.overall_confidence, days_overdue
            ),
            prevented_incident_types=["EQUIPMENT_FAILURE", "PRESSURE_FAILURE", "GAS_LEAK"],
            alternative_timeline_events=[
                "Maintenance completed on schedule",
                "Equipment operating within rated parameters",
                "No anomalous sensor readings",
                "Incident trigger condition absent",
            ],
            confidence=min(0.90, investigation.overall_confidence * 1.1),
            assumptions=[
                f"Maintenance was {days_overdue} days overdue",
                "Equipment defect was the primary failure mechanism",
                "Standard maintenance would have resolved the defect",
            ],
            impact_summary=(
                f"Completing maintenance could have reduced incident risk by "
                f"{self._estimate_maintenance_risk_reduction(investigation.overall_confidence, days_overdue):.0f}%."
            ),
        )

    def build_ppe_scenario(
        self,
        investigation: Investigation,
        report: InvestigationReport,
    ) -> CounterfactualScenario:
        """Build scenario: all workers had correct PPE."""
        worker_ids = investigation.worker_ids or ["unspecified workers"]
        primary_desc = investigation.primary_cause.description if investigation.primary_cause else "Worker exposure"
        return CounterfactualScenario(
            investigation_id=investigation.id,
            scenario_type=ScenarioType.PPE_COMPLIANT,
            intervention_description=(
                f"All workers ({', '.join(worker_ids[:3])}) fully PPE compliant before incident."
            ),
            original_root_cause=primary_desc,
            alternative_root_cause="Physical harm to workers would have been prevented or significantly reduced.",
            risk_reduction_pct=75.0,
            prevented_incident_types=["WORKER_INJURY", "CHEMICAL_EXPOSURE", "BURN"],
            alternative_timeline_events=[
                "PPE compliance check passed",
                "Workers enter zone with full protection",
                "Hazard exposure mitigated by PPE",
                "No personal injury recorded",
            ],
            confidence=0.80,
            assumptions=[
                "PPE violation was a contributing factor to worker harm",
                "Appropriate PPE for the hazard type was available",
                "PPE compliance enforcement was achievable",
            ],
            impact_summary="Full PPE compliance could have prevented worker injury with high confidence.",
        )

    def build_earlier_detection_scenario(
        self,
        investigation: Investigation,
        report: InvestigationReport,
        minutes_earlier: int = 5,
    ) -> CounterfactualScenario:
        """Build scenario: hazard detected N minutes earlier."""
        primary_desc = investigation.primary_cause.description if investigation.primary_cause else "Undetected hazard"
        return CounterfactualScenario(
            investigation_id=investigation.id,
            scenario_type=ScenarioType.EARLIER_DETECTION,
            intervention_description=(
                f"Hazard detected {minutes_earlier} minutes earlier than actual detection time."
            ),
            original_root_cause=primary_desc,
            alternative_root_cause="Earlier detection allows intervention before incident escalation.",
            risk_reduction_pct=self._estimate_detection_risk_reduction(minutes_earlier),
            prevented_incident_types=["ESCALATION", "SECONDARY_FAILURE", "WORKER_INJURY"],
            alternative_timeline_events=[
                f"Sensor alert raised {minutes_earlier} minutes earlier",
                "Emergency response initiated in pre-incident window",
                "Evacuation and containment before escalation",
                "Incident contained at minor severity",
            ],
            confidence=0.70,
            assumptions=[
                f"Detection delay was {minutes_earlier} minutes",
                "Sensor infrastructure was capable of earlier detection",
                "Response team would have acted immediately on early alert",
            ],
            impact_summary=(
                f"Earlier detection by {minutes_earlier} minutes could reduce incident impact by "
                f"{self._estimate_detection_risk_reduction(minutes_earlier):.0f}%."
            ),
        )

    def build_sensor_available_scenario(
        self,
        investigation: Investigation,
        report: InvestigationReport,
        sensor_ids: list[str] | None = None,
    ) -> CounterfactualScenario:
        """Build scenario: failed sensor(s) had been operational."""
        primary_desc = investigation.primary_cause.description if investigation.primary_cause else "Unmonitored condition"
        sensor_list = sensor_ids or ["primary monitoring sensor"]
        return CounterfactualScenario(
            investigation_id=investigation.id,
            scenario_type=ScenarioType.SENSOR_AVAILABLE,
            intervention_description=(
                f"Sensor(s) {', '.join(sensor_list)} operational during incident window."
            ),
            original_root_cause=primary_desc,
            alternative_root_cause="Continuous monitoring would have triggered alert before threshold breach.",
            risk_reduction_pct=60.0,
            prevented_incident_types=["SENSOR_FAILURE", "UNDETECTED_HAZARD", "DELAYED_RESPONSE"],
            alternative_timeline_events=[
                "Sensor provides continuous monitoring",
                "Anomaly detected at lower threshold",
                "Alert issued before critical condition",
                "Preventive intervention applied",
            ],
            confidence=0.65,
            assumptions=[
                "Sensor failure was a key contributing factor",
                "Operational sensor would have detected the anomaly",
                "Alert response time within emergency protocol",
            ],
            impact_summary="Operational sensors could have enabled timely detection and response.",
        )

    def build_custom_scenario(
        self,
        investigation: Investigation,
        intervention: str,
        risk_reduction_pct: float = 50.0,
        alternative_cause: str = "",
        assumptions: list[str] | None = None,
    ) -> CounterfactualScenario:
        """Build a custom user-defined counterfactual scenario."""
        primary_desc = investigation.primary_cause.description if investigation.primary_cause else "Unidentified cause"
        return CounterfactualScenario(
            investigation_id=investigation.id,
            scenario_type=ScenarioType.CUSTOM_INTERVENTION,
            intervention_description=intervention,
            original_root_cause=primary_desc,
            alternative_root_cause=alternative_cause or f"Outcome altered by: {intervention[:80]}",
            risk_reduction_pct=risk_reduction_pct,
            prevented_incident_types=[],
            alternative_timeline_events=["Custom intervention applied", "Outcome trajectory altered"],
            confidence=0.50,
            assumptions=assumptions or ["Custom intervention is feasible and would be enacted"],
            impact_summary=f"Custom intervention: {intervention[:100]}.",
        )

    @staticmethod
    def _estimate_maintenance_risk_reduction(confidence: float, days_overdue: int) -> float:
        """Estimate risk reduction from timely maintenance (heuristic model)."""
        base = 40.0
        overdue_factor = min(40.0, days_overdue * 1.2)
        confidence_factor = confidence * 20.0
        return min(95.0, base + overdue_factor + confidence_factor)

    @staticmethod
    def _estimate_detection_risk_reduction(minutes_earlier: int) -> float:
        """Estimate risk reduction from earlier detection (heuristic model)."""
        return min(90.0, 10.0 + minutes_earlier * 8.0)

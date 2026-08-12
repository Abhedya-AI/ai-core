"""what_if_analyzer.py — What-If analysis engine for counterfactual reasoning."""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Investigation, InvestigationReport,
    CounterfactualScenario, ScenarioType,
)
from app.modules.root_cause.counterfactual.scenario_builder import ScenarioBuilder

log = get_logger("root_cause.counterfactual.analyzer")


class WhatIfAnalyzer:
    """Orchestrates counterfactual analysis for an investigation."""

    def __init__(self, builder: ScenarioBuilder | None = None) -> None:
        self.builder = builder or ScenarioBuilder()

    def analyze(
        self,
        investigation: Investigation,
        report: InvestigationReport,
        scenario_types: list[ScenarioType] | None = None,
    ) -> list[CounterfactualScenario]:
        """Generate counterfactual scenarios for the investigation."""
        log.info(f"Running what-if analysis for investigation {investigation.id}")
        requested = scenario_types or [
            ScenarioType.MAINTENANCE_COMPLETED,
            ScenarioType.PPE_COMPLIANT,
            ScenarioType.EARLIER_DETECTION,
            ScenarioType.SENSOR_AVAILABLE,
        ]
        scenarios: list[CounterfactualScenario] = []
        for stype in requested:
            try:
                scenario = self._build_scenario(stype, investigation, report)
                if scenario:
                    scenarios.append(scenario)
            except Exception as exc:
                log.warning(f"Scenario {stype} failed: {exc}")
        log.info(f"Generated {len(scenarios)} counterfactual scenarios")
        return scenarios

    def _build_scenario(
        self,
        stype: ScenarioType,
        investigation: Investigation,
        report: InvestigationReport,
    ) -> CounterfactualScenario | None:
        if stype == ScenarioType.MAINTENANCE_COMPLETED:
            return self.builder.build_maintenance_scenario(investigation, report)
        elif stype == ScenarioType.PPE_COMPLIANT:
            return self.builder.build_ppe_scenario(investigation, report)
        elif stype == ScenarioType.EARLIER_DETECTION:
            return self.builder.build_earlier_detection_scenario(investigation, report)
        elif stype == ScenarioType.SENSOR_AVAILABLE:
            return self.builder.build_sensor_available_scenario(investigation, report)
        return None

    def rank_by_impact(
        self, scenarios: list[CounterfactualScenario]
    ) -> list[CounterfactualScenario]:
        """Sort scenarios by risk reduction potential."""
        return sorted(scenarios, key=lambda s: s.risk_reduction_pct, reverse=True)

    def compute_aggregate_risk_reduction(
        self, scenarios: list[CounterfactualScenario]
    ) -> float:
        """Estimate combined risk reduction from all scenarios (additive up to 95%)."""
        if not scenarios:
            return 0.0
        total = sum(s.risk_reduction_pct for s in scenarios)
        return min(95.0, total / len(scenarios) * 1.5)

    def summarize(
        self, scenarios: list[CounterfactualScenario]
    ) -> dict[str, Any]:
        """Generate a summary of all counterfactual analysis results."""
        ranked = self.rank_by_impact(scenarios)
        return {
            "total_scenarios": len(scenarios),
            "aggregate_risk_reduction_pct": self.compute_aggregate_risk_reduction(scenarios),
            "top_intervention": ranked[0].intervention_description if ranked else None,
            "scenario_types": [s.scenario_type.value for s in scenarios],
            "scenarios": [
                {
                    "type": s.scenario_type.value,
                    "intervention": s.intervention_description,
                    "risk_reduction_pct": s.risk_reduction_pct,
                    "confidence": s.confidence,
                    "impact": s.impact_summary,
                }
                for s in ranked
            ],
        }

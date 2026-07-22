"""incident_assessor.py — Phase 1: Multi-Agent Incident Assessment Engine."""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.emergency.models import IncidentState
from app.modules.agents.emergency.providers import (
    ComplianceEmergencyProvider,
    PredictionEmergencyProvider,
    RiskEmergencyProvider,
    VisionEmergencyProvider,
)

log = get_logger("agents.emergency.assessor")


class IncidentAssessor:
    """Phase 1: Aggregates outputs from Vision, Risk, Prediction, Compliance, and Root Cause agents into an IncidentState."""

    @staticmethod
    def assess_incident(context: AgentContext) -> IncidentState:
        target_zone = context.target_entity_id or "ZONE-B"
        log.info(f"Assessing multi-agent incident state for target zone '{target_zone}'")

        risk_ctx = RiskEmergencyProvider.get_risk_context(context.metadata)
        pred_ctx = PredictionEmergencyProvider.get_prediction_context(context.metadata)
        comp_violations = ComplianceEmergencyProvider.get_compliance_violations(context.metadata)
        vision_state = VisionEmergencyProvider.get_vision_state(context.vision_events)

        blocked_exits = [v.get("location", "EXIT-A") for v in comp_violations if "EXIT" in str(v.get("type", ""))]
        if vision_state.get("blocked_exit") and vision_state["blocked_exit"] not in blocked_exits:
            blocked_exits.append(vision_state["blocked_exit"])

        active_hazards = list(risk_ctx.get("hazards", ["GAS_LEAK", "SMOKE"]))

        return IncidentState(
            incident_id=f"INC-{target_zone}",
            severity=risk_ctx.get("risk_level", "CRITICAL"),
            affected_zone=target_zone,
            affected_workers_count=vision_state.get("detected_workers_count", 12),
            active_hazards=active_hazards,
            blocked_exits=blocked_exits,
            risk_level=risk_ctx.get("risk_level", "CRITICAL"),
            prediction_time_horizon_min=pred_ctx.get("predicted_escalation_min", 4.0),
        )

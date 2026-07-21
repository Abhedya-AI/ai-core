"""policies.py — Centralized Risk Policy Business Rules."""

from app.modules.agents.risk.models import PriorityEnum, RiskScore, SeverityEnum


def evaluate_risk_policy(score: RiskScore, hazard_type: str = "GENERAL") -> dict:
    """
    Evaluate business rules based on risk score and hazard type.

    Returns:
        dict containing 'trigger_emergency', 'requires_evacuation', 'event_type', and 'action_mode'.
    """
    trigger_emergency = False
    requires_evacuation = False
    event_type = "RiskDetected"

    if score.severity == SeverityEnum.CRITICAL or score.score_value >= 80.0:
        trigger_emergency = True
        requires_evacuation = True
        event_type = "HighRiskDetected"
    elif score.severity == SeverityEnum.HIGH or score.score_value >= 60.0:
        event_type = "HighRiskDetected"

    if "gas" in hazard_type.lower() and score.severity in (SeverityEnum.HIGH, SeverityEnum.CRITICAL):
        trigger_emergency = True
        requires_evacuation = True

    return {
        "trigger_emergency": trigger_emergency,
        "requires_evacuation": requires_evacuation,
        "event_type": event_type,
        "priority": score.priority.value,
    }

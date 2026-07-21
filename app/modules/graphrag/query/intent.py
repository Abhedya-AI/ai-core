"""intent.py — Query intent classification enum and rules."""

from enum import Enum


class QueryIntent(str, Enum):
    """Classified user intent for GraphRAG routing."""

    RISK_ANALYSIS = "RISK_ANALYSIS"
    INCIDENT_INVESTIGATION = "INCIDENT_INVESTIGATION"
    EQUIPMENT_STATUS = "EQUIPMENT_STATUS"
    COMPLIANCE_CHECK = "COMPLIANCE_CHECK"
    EVACUATION_PLAN = "EVACUATION_PLAN"
    GENERAL_SAFETY = "GENERAL_SAFETY"

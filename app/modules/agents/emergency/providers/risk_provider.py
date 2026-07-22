"""risk_provider.py — Risk Intelligence Context Provider."""

from typing import Any


class RiskEmergencyProvider:
    """Extracts risk scores and hazard levels from Risk Agent outputs."""

    @staticmethod
    def get_risk_context(metadata: dict[str, Any]) -> dict[str, Any]:
        return metadata.get("risk_output", {"risk_level": "CRITICAL", "score": 92.0, "hazards": ["GAS_LEAK", "FIRE_RISK"]})

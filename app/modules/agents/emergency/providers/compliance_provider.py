"""compliance_provider.py — Compliance Context Emergency Provider."""

from typing import Any


class ComplianceEmergencyProvider:
    """Extracts regulatory safety violations (e.g. expired permits, blocked exits)."""

    @staticmethod
    def get_compliance_violations(metadata: dict[str, Any]) -> list[dict[str, Any]]:
        return metadata.get("compliance_violations", [{"type": "BLOCKED_EMERGENCY_EXIT", "location": "EXIT-A"}])

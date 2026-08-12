"""
domain/enums/alert_severity.py — AlertSeverity enum.

Severity levels for VisionAlerts, ordered by urgency.
"""
from enum import Enum


class AlertSeverity(str, Enum):
    """Severity levels for vision system alerts."""

    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def is_actionable(self) -> bool:
        """True if severity requires immediate human action."""
        return self in {AlertSeverity.HIGH, AlertSeverity.CRITICAL}

    @property
    def numeric_weight(self) -> int:
        """Numeric weight for sorting/comparison (higher = more severe)."""
        return {
            AlertSeverity.LOW: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.HIGH: 3,
            AlertSeverity.CRITICAL: 4,
        }[self]

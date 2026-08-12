"""
domain/enums/alert_status.py — AlertStatus enum.

Lifecycle states for VisionAlerts.
"""
from enum import Enum


class AlertStatus(str, Enum):
    """Lifecycle states for vision system alerts."""

    ACTIVE       = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED     = "RESOLVED"
    SUPPRESSED   = "SUPPRESSED"
    EXPIRED      = "EXPIRED"

    @property
    def is_open(self) -> bool:
        """True if the alert still requires attention."""
        return self in {AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED}

    @property
    def is_closed(self) -> bool:
        """True if the alert is no longer active."""
        return self in {AlertStatus.RESOLVED, AlertStatus.SUPPRESSED, AlertStatus.EXPIRED}

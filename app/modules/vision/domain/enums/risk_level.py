"""
domain/enums/risk_level.py — Risk severity ladder shared by all ABHEDYA modules.

Every module that produces or consumes safety assessments uses these
same four levels.  Keeping them in a single canonical file prevents
drift between modules.
"""

from enum import Enum


class RiskLevel(str, Enum):
    """Risk categories used across ABHEDYA."""

    LOW      = "LOW"
    """Informational — no immediate action required."""

    MEDIUM   = "MEDIUM"
    """Warrants monitoring or a non-urgent alert."""

    HIGH     = "HIGH"
    """Requires prompt operator attention."""

    CRITICAL = "CRITICAL"
    """Demands immediate automated or human response."""

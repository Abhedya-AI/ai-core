from enum import Enum


class HazardLevel(str, Enum):
    """Hazard severity classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

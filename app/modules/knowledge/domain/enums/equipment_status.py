from enum import Enum


class EquipmentStatus(str, Enum):
    """Operational status of an industrial asset or equipment."""

    OPERATIONAL = "OPERATIONAL"
    MAINTENANCE = "MAINTENANCE"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    OFFLINE = "OFFLINE"
    RETIRED = "RETIRED"

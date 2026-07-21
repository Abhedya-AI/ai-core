from enum import Enum


class ZoneType(str, Enum):
    """Classification of facility zones and spatial areas."""

    PROCESSING = "PROCESSING"
    STORAGE = "STORAGE"
    MAINTENANCE_BAY = "MAINTENANCE_BAY"
    CONTROL_ROOM = "CONTROL_ROOM"
    HAZARDOUS = "HAZARDOUS"
    OFFICE = "OFFICE"
    OUTDOOR = "OUTDOOR"

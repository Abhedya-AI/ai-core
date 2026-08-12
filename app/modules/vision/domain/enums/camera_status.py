"""
domain/enums/camera_status.py — CameraStatus enum.
"""
from enum import Enum


class CameraStatus(str, Enum):
    ONLINE       = "ONLINE"
    OFFLINE      = "OFFLINE"
    DEGRADED     = "DEGRADED"
    RECONNECTING = "RECONNECTING"
    MAINTENANCE  = "MAINTENANCE"

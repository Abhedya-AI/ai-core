"""
domain/enums/camera_type.py — CameraType enum.
"""
from enum import Enum


class CameraType(str, Enum):
    RTSP   = "RTSP"
    USB    = "USB"
    IP     = "IP"
    FILE   = "FILE"
    UPLOAD = "UPLOAD"

from app.modules.vision.domain.entities.camera import Camera
from app.modules.vision.domain.entities.camera_group import CameraGroup
from app.modules.vision.domain.entities.camera_health import CameraHealth
from app.modules.vision.domain.entities.camera_zone import CameraZone
from app.modules.vision.domain.entities.detection import Detection
from app.modules.vision.domain.entities.detection_class import DetectionClass, DETECTION_CLASS_REGISTRY, resolve_detection_class
from app.modules.vision.domain.entities.detection_event import DetectionEvent, AlertSeverity
from app.modules.vision.domain.entities.frame import Frame, FrameFormat
from app.modules.vision.domain.entities.frame_metadata import FrameMetadata
from app.modules.vision.domain.entities.tracking_history import TrackingHistory
from app.modules.vision.domain.entities.tracking_object import TrackingObject, ZoneCrossing
from app.modules.vision.domain.entities.video_stream import VideoStream, StreamProtocol, StreamStatus
from app.modules.vision.domain.entities.vision_alert import VisionAlert, AlertStatus
from app.modules.vision.domain.entities.vision_event import VisionEvent
from app.modules.vision.domain.entities.vision_incident import VisionIncident

try:
    from app.modules.vision.domain.entities.hazard import Hazard
except ImportError:
    pass

__all__ = [
    "Camera", "CameraGroup", "CameraHealth", "CameraZone",
    "Detection", "DetectionClass", "DETECTION_CLASS_REGISTRY", "resolve_detection_class",
    "DetectionEvent", "AlertSeverity",
    "Frame", "FrameFormat", "FrameMetadata",
    "TrackingHistory", "TrackingObject", "ZoneCrossing",
    "VideoStream", "StreamProtocol", "StreamStatus",
    "VisionAlert", "AlertStatus",
    "VisionEvent",
    "VisionIncident",
]

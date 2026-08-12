"""
vision/application/events/vision_event_publisher.py — Vision Event Publisher.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from app.modules.events.event_dispatcher import EventDispatcher
from app.modules.events.event_validator import EventEnvelope
from app.modules.vision.domain.entities.detection_event import DetectionEvent
from app.modules.vision.domain.entities.frame import Frame
from app.modules.vision.domain.entities.frame_metadata import FrameMetadata
from app.modules.vision.domain.entities.tracking_object import TrackingObject
from app.modules.vision.domain.entities.vision_alert import VisionAlert
from app.modules.vision.domain.enums.stream_event_type import StreamEventType

class VisionEventPublisher:
    def __init__(self, dispatcher: EventDispatcher) -> None:
        self._dispatcher = dispatcher
        self._plant_id: str = "DEFAULT_PLANT"

    def _build_envelope(self, event_type: StreamEventType, payload: dict, zone_id: str | None, plant_id: str, source: str, trace_id: str | None = None) -> EventEnvelope:
        return EventEnvelope(
            event_id=str(uuid.uuid4()),
            event_type=event_type.value if hasattr(event_type, 'value') else str(event_type),
            timestamp=datetime.now(timezone.utc),
            source=source,
            plant_id=plant_id,
            zone_id=zone_id,
            trace_id=trace_id,
            payload=payload,
            metadata={}
        )

    async def publish_detection_event(self, det_event: DetectionEvent) -> None:
        payload = {
            "detection_id": det_event.detection_id,
            "camera_id": det_event.camera_id,
            "hazard_type": det_event.hazard_type.value if hasattr(det_event.hazard_type, 'value') else det_event.hazard_type,
            "confidence": det_event.confidence,
            "risk_score": det_event.risk_score,
            "risk_level": det_event.risk_level.value if hasattr(det_event.risk_level, 'value') else det_event.risk_level,
            "bounding_box": det_event.bounding_box,
            "track_id": det_event.track_id,
            "is_ppe_violation": det_event.is_ppe_violation,
            "is_restricted_zone": det_event.is_restricted_zone,
            "detected_at": det_event.detected_at.isoformat() if det_event.detected_at else None
        }
        env = self._build_envelope(
            det_event.stream_event_type,
            payload,
            det_event.zone_id,
            det_event.plant_id or self._plant_id,
            "vision.detection"
        )
        self._dispatcher.dispatch(env)

    async def publish_camera_status(self, camera_id: str, zone_id: str | None, plant_id: str, event_type: StreamEventType, details: dict) -> None:
        payload = {
            "camera_id": camera_id,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        env = self._build_envelope(
            event_type, payload, zone_id, plant_id, "vision.camera"
        )
        self._dispatcher.dispatch(env)

    async def publish_tracking_event(self, track: TrackingObject, event_type: StreamEventType) -> None:
        payload = {
            "track_id": track.track_id,
            "camera_id": track.camera_id,
            "object_class": track.object_class,
            "zone_id": track.zone_id,
            "duration_seconds": (track.last_seen - track.first_seen).total_seconds() if track.last_seen and track.first_seen else 0,
            "zone_crossings_count": len(track.zone_crossings) if hasattr(track, 'zone_crossings') and track.zone_crossings else 0
        }
        env = self._build_envelope(
            event_type, payload, track.zone_id, self._plant_id, "vision.tracking"
        )
        self._dispatcher.dispatch(env)

    async def publish_alert(self, alert: VisionAlert) -> None:
        evt_type = StreamEventType.PPE_VIOLATION
        payload = {
            "alert_id": alert.alert_id,
            "camera_id": alert.camera_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity.value if hasattr(alert.severity, 'value') else alert.severity,
            "description": alert.description,
            "detection_ids": alert.detection_ids
        }
        env = self._build_envelope(
            evt_type, payload, alert.zone_id, self._plant_id, "vision.alert"
        )
        self._dispatcher.dispatch(env)

    async def publish_frame_captured(self, frame: Frame, metadata: FrameMetadata) -> None:
        payload = {
            "frame_id": frame.frame_id,
            "camera_id": frame.camera_id,
            "sequence_number": frame.sequence_number,
            "captured_at": frame.timestamp.isoformat() if frame.timestamp else None,
            "detection_count": len(metadata.detections) if hasattr(metadata, 'detections') else 0,
            "inference_time_ms": metadata.inference_time_ms if hasattr(metadata, 'inference_time_ms') else 0
        }
        env = self._build_envelope(
            StreamEventType.FRAME_CAPTURED, payload, frame.zone_id, self._plant_id, "vision.frame"
        )
        self._dispatcher.dispatch(env)

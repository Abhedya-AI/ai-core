"""
vision/application/events/graphrag_indexer.py — Vision GraphRAG Event Indexer.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Any
from app.core.logging import get_logger
from app.modules.vision.domain.entities.detection_event import DetectionEvent, AlertSeverity
from app.modules.vision.domain.entities.vision_alert import VisionAlert
from app.modules.vision.domain.entities.tracking_object import TrackingObject
from app.modules.vision.domain.enums.hazard_type import HazardType
from app.modules.vision.domain.enums.stream_event_type import StreamEventType

log = get_logger("vision.application.events.graphrag_indexer")

class VisionGraphRAGIndexer:
    def __init__(self) -> None:
        self._graphrag = None
        self._available = False
        self._index_count = 0

    def _get_graphrag(self) -> Any | None:
        try:
            from app.modules.graphrag.service import GraphRAGService
            if self._graphrag is None:
                self._graphrag = GraphRAGService()
            self._available = True
            return self._graphrag
        except ImportError:
            try:
                from app.graphrag.service import GraphRAGService
                if self._graphrag is None:
                    self._graphrag = GraphRAGService()
                self._available = True
                return self._graphrag
            except ImportError:
                log.debug("GraphRAG service not available — vision events will not be indexed")
                return None

    def _build_detection_chunk(self, det_event: DetectionEvent) -> dict:
        evt_type = det_event.stream_event_type.value if hasattr(det_event.stream_event_type, 'value') else str(det_event.stream_event_type)
        hazard = det_event.hazard_type.value if hasattr(det_event.hazard_type, 'value') else str(det_event.hazard_type)
        risk_lvl = det_event.risk_level.value if hasattr(det_event.risk_level, 'value') else str(det_event.risk_level)
        
        ppe_str = 'PPE VIOLATION' if det_event.is_ppe_violation else ''
        restricted_str = 'RESTRICTED ZONE ENTRY' if det_event.is_restricted_zone else ''
        
        text = f"[{evt_type}] Camera {det_event.camera_id} Zone {det_event.zone_id} — {hazard} detected at {det_event.detected_at}.\n"
        text += f"Confidence: {det_event.confidence:.1%}. Risk Level: {risk_lvl}. Risk Score: {det_event.risk_score:.2f}.\n"
        text += f"{ppe_str}\n{restricted_str}\n"
        text += f"Detection ID: {det_event.detection_id}. Track ID: {det_event.track_id}."
        
        metadata = {
            "event_type": evt_type,
            "camera_id": det_event.camera_id,
            "zone_id": det_event.zone_id,
            "plant_id": det_event.plant_id,
            "hazard_type": hazard,
            "risk_level": risk_lvl,
            "severity": det_event.severity.value if hasattr(det_event.severity, 'value') else str(det_event.severity),
            "detected_at": det_event.detected_at.isoformat() if det_event.detected_at else None,
            "is_critical": det_event.severity == AlertSeverity.CRITICAL if hasattr(AlertSeverity, 'CRITICAL') else False
        }
        return {"text": text, "metadata": metadata, "doc_id": det_event.event_id or det_event.detection_id}

    def _build_alert_chunk(self, alert: VisionAlert) -> dict:
        text = f"[ALERT] {alert.alert_type} in {alert.zone_id} at {alert.created_at}. Severity: {alert.severity}. Status: {alert.status}. {alert.description}"
        return {
            "text": text,
            "metadata": {
                "alert_id": alert.alert_id,
                "type": alert.alert_type,
                "severity": alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity),
                "zone_id": alert.zone_id
            },
            "doc_id": alert.alert_id
        }

    def _build_tracking_chunk(self, track: TrackingObject) -> dict:
        text = f"[TRACKING] {track.object_class} in {track.zone_id} via {track.camera_id}. First seen: {track.first_seen}. Last seen: {track.last_seen}."
        return {
            "text": text,
            "metadata": {
                "track_id": track.track_id,
                "camera_id": track.camera_id,
                "zone_id": track.zone_id,
                "object_class": track.object_class
            },
            "doc_id": track.track_id
        }

    def _should_index_detection(self, det_event: DetectionEvent) -> bool:
        hazard = det_event.hazard_type.value if hasattr(det_event.hazard_type, 'value') else str(det_event.hazard_type)
        severity = det_event.severity.value if hasattr(det_event.severity, 'value') else str(det_event.severity)
        if severity in ('CRITICAL', 'HIGH') or det_event.is_ppe_violation or det_event.is_restricted_zone:
            return True
        if hazard in ('FIRE', 'SMOKE', 'CHEMICAL_SPILL', 'FALL'):
            return True
        return False

    async def index_detection_event(self, det_event: DetectionEvent) -> None:
        if not self._should_index_detection(det_event):
            return
        chunk = self._build_detection_chunk(det_event)
        gr = self._get_graphrag()
        if gr:
            try:
                await gr.index_document(chunk["text"], chunk["metadata"])
                self._index_count += 1
                log.debug(f"Indexed detection {det_event.detection_id}")
            except Exception as e:
                log.warning(f"Failed to index detection: {e}")

    async def index_alert(self, alert: VisionAlert) -> None:
        chunk = self._build_alert_chunk(alert)
        gr = self._get_graphrag()
        if gr:
            try:
                await gr.index_document(chunk["text"], chunk["metadata"])
                self._index_count += 1
            except Exception as e:
                log.warning(f"Failed to index alert: {e}")

    async def index_tracking_summary(self, track: TrackingObject) -> None:
        duration = (track.last_seen - track.first_seen).total_seconds() if track.last_seen and track.first_seen else 0
        if duration > 300 or (hasattr(track, 'zone_crossings') and track.zone_crossings):
            chunk = self._build_tracking_chunk(track)
            gr = self._get_graphrag()
            if gr:
                try:
                    await gr.index_document(chunk["text"], chunk["metadata"])
                    self._index_count += 1
                except Exception as e:
                    log.warning(f"Failed to index tracking: {e}")

    def get_stats(self) -> dict:
        return {"available": self._available, "index_count": self._index_count}

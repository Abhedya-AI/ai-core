"""
vision/application/tracking/simple_iou_tracker.py — Simple IoU Tracker.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from app.core.logging import get_logger
from app.modules.vision.application.tracking.tracker_interface import BaseTracker
from app.modules.vision.domain.entities.detection import Detection
from app.modules.vision.domain.entities.tracking_object import TrackingObject

log = get_logger("vision.application.tracking.iou_tracker")

IOU_THRESHOLD = 0.3
MAX_MISSED_FRAMES = 10

@dataclass
class _TrackState:
    track_id: str
    last_bbox: dict
    missed_count: int
    frame_count: int
    first_seen: datetime
    last_seen: datetime
    object_class: str
    trajectory: list[dict] = field(default_factory=list)
    confidence: float = 0.0

class SimpleIoUTracker(BaseTracker):
    def __init__(self, camera_id: str):
        self._tracks: dict[str, _TrackState] = {}
        self._camera_id = camera_id

    def _compute_iou(self, box1: dict, box2: dict) -> float:
        x_left = max(box1.get('x_min', 0), box2.get('x_min', 0))
        y_top = max(box1.get('y_min', 0), box2.get('y_min', 0))
        x_right = min(box1.get('x_max', 0), box2.get('x_max', 0))
        y_bottom = min(box1.get('y_max', 0), box2.get('y_max', 0))

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = (box1.get('x_max', 0) - box1.get('x_min', 0)) * (box1.get('y_max', 0) - box1.get('y_min', 0))
        box2_area = (box2.get('x_max', 0) - box2.get('x_min', 0)) * (box2.get('y_max', 0) - box2.get('y_min', 0))

        union_area = box1_area + box2_area - intersection_area
        if union_area == 0:
            return 0.0
        return intersection_area / union_area

    def _detection_to_bbox(self, det: Detection) -> dict:
        return det.bounding_box or {}

    def _track_state_to_domain(self, state: _TrackState, zone_id: str | None) -> TrackingObject:
        return TrackingObject(
            track_id=state.track_id,
            camera_id=self._camera_id,
            object_class=state.object_class,
            first_seen=state.first_seen,
            last_seen=state.last_seen,
            is_active=True,
            zone_id=zone_id,
            zone_crossings=[]
        )

    def update(self, detections: list[Detection], frame_id: str, timestamp: datetime) -> list[TrackingObject]:
        det_bboxes = [self._detection_to_bbox(d) for d in detections]
        track_ids = list(self._tracks.keys())
        track_states = [self._tracks[tid] for tid in track_ids]

        matches = []
        for d_idx, d_bbox in enumerate(det_bboxes):
            for t_idx, state in enumerate(track_states):
                iou = self._compute_iou(d_bbox, state.last_bbox)
                if iou >= IOU_THRESHOLD:
                    matches.append((d_idx, t_idx, iou))

        matches.sort(key=lambda x: x[2], reverse=True)
        matched_dets = set()
        matched_tracks = set()

        for d_idx, t_idx, iou in matches:
            if d_idx not in matched_dets and t_idx not in matched_tracks:
                matched_dets.add(d_idx)
                matched_tracks.add(t_idx)
                state = track_states[t_idx]
                state.last_bbox = det_bboxes[d_idx]
                state.last_seen = timestamp
                state.missed_count = 0
                state.frame_count += 1
                state.confidence = detections[d_idx].confidence
                if len(state.trajectory) > 50:
                    state.trajectory.pop(0)
                state.trajectory.append(det_bboxes[d_idx])

        for d_idx, d in enumerate(detections):
            if d_idx not in matched_dets:
                tid = str(uuid.uuid4())
                self._tracks[tid] = _TrackState(
                    track_id=tid,
                    last_bbox=det_bboxes[d_idx],
                    missed_count=0,
                    frame_count=1,
                    first_seen=timestamp,
                    last_seen=timestamp,
                    object_class=getattr(d.hazard_type, 'value', str(d.hazard_type)),
                    trajectory=[det_bboxes[d_idx]],
                    confidence=d.confidence
                )

        to_delete = []
        for t_idx, tid in enumerate(track_ids):
            if t_idx not in matched_tracks:
                self._tracks[tid].missed_count += 1
                if self._tracks[tid].missed_count > MAX_MISSED_FRAMES:
                    to_delete.append(tid)

        for tid in to_delete:
            del self._tracks[tid]

        return self.get_active_tracks()

    def get_active_tracks(self) -> list[TrackingObject]:
        return [self._track_state_to_domain(ts, None) for ts in self._tracks.values()]

    def reset(self) -> None:
        self._tracks.clear()

    @property
    def tracker_name(self) -> str:
        return 'simple-iou-v1'

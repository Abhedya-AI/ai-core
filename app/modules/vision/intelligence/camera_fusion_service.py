"""
intelligence/camera_fusion_service.py — Multi-Camera Cross-Tracking & Fusion Service.

Fuses overlapping camera views, performs cross-camera worker re-identification,
handles camera handoffs as workers traverse plant floors, and removes duplicate detections.
"""
from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger

log = get_logger("vision.intelligence.camera_fusion")


class FusedTrack(BaseModel):
    fused_worker_id: str
    camera_ids: list[str]
    current_primary_camera_id: str
    zone_id: str
    global_x: float
    global_y: float
    confidence: float
    last_updated: float


class MultiCameraFusionService:
    """Service correlating detection tracks across overlapping multi-camera network."""

    def __init__(self, spatial_match_distance_m: float = 1.5) -> None:
        self._match_threshold = spatial_match_distance_m
        self._fused_tracks: dict[str, FusedTrack] = {}  # fused_worker_id -> FusedTrack

    def fuse_camera_detections(
        self,
        camera_id: str,
        zone_id: str,
        detections: list[dict[str, Any]],  # list of {track_id, global_x, global_y, confidence, worker_id}
        timestamp: float,
    ) -> list[FusedTrack]:
        """
        Correlate incoming camera detections with global fused tracks.

        Removes duplicate entries for the same worker seen by overlapping cameras.
        """
        fused_results: list[FusedTrack] = []

        for det in detections:
            gx = det.get("global_x", 0.0)
            gy = det.get("global_y", 0.0)
            conf = det.get("confidence", 0.9)
            local_worker_id = det.get("worker_id") or det.get("track_id", "untracked")

            # Search for matching existing fused track by spatial proximity
            matched_track_id: str | None = None
            for fid, track in self._fused_tracks.items():
                if track.zone_id == zone_id:
                    dist = math.sqrt((track.global_x - gx) ** 2 + (track.global_y - gy) ** 2)
                    if dist <= self._match_threshold:
                        matched_track_id = fid
                        break

            if matched_track_id:
                # Update existing track (add camera, update position & primary camera)
                track = self._fused_tracks[matched_track_id]
                if camera_id not in track.camera_ids:
                    track.camera_ids.append(camera_id)
                track.current_primary_camera_id = camera_id
                track.global_x = (track.global_x + gx) / 2.0  # spatial averaging
                track.global_y = (track.global_y + gy) / 2.0
                track.confidence = max(track.confidence, conf)
                track.last_updated = timestamp
                fused_results.append(track)
                log.debug(f"Multi-camera fusion: Merged camera {camera_id} track into fused track {matched_track_id}")
            else:
                # Create new fused track
                fused_id = f"fused-{local_worker_id}"
                new_track = FusedTrack(
                    fused_worker_id=fused_id,
                    camera_ids=[camera_id],
                    current_primary_camera_id=camera_id,
                    zone_id=zone_id,
                    global_x=gx,
                    global_y=gy,
                    confidence=conf,
                    last_updated=timestamp,
                )
                self._fused_tracks[fused_id] = new_track
                fused_results.append(new_track)

        return fused_results

    def get_active_fused_tracks(self, zone_id: str | None = None) -> list[FusedTrack]:
        """Return list of active fused tracks."""
        if zone_id:
            return [t for t in self._fused_tracks.values() if t.zone_id == zone_id]
        return list(self._fused_tracks.values())

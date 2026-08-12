"""
domain/entities/tracking_history.py — TrackingHistory domain entity.

Immutable archived summary of a completed tracking session. Written to the
repository when a TrackingObject is deactivated, providing a compact,
queryable record of the entire object lifecycle (entry zone, exit zone,
total frames, duration, average confidence, and trajectory summary).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class TrackingHistory(BaseModel):
    """Archived complete history of a tracking session after it ends."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    track_id: str
    camera_id: str
    zone_id: str | None = None
    object_class: str
    total_frames: int
    duration_seconds: float
    entry_zone: str | None = None
    exit_zone: str | None = None
    zone_crossings: list[dict] = Field(default_factory=list)
    max_speed: float = 0.0
    avg_confidence: float = 0.0
    trajectory_summary: list[dict] = Field(default_factory=list)
    archived_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

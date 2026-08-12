"""
domain/entities/tracking_object.py — TrackingObject domain entity.

Represents a real-world object (person, vehicle, equipment) being tracked
across consecutive frames in a camera feed. Maintains trajectory history,
zone crossing records, and lifecycle state. All mutations return new frozen
instances following the immutable entity pattern.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ZoneCrossing(BaseModel):
    """Records a single zone crossing event for a tracked object."""

    model_config = ConfigDict(frozen=True)

    zone_id: str
    zone_name: str
    direction: str  # 'ENTERED' or 'EXITED'
    crossed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class TrackingObject(BaseModel):
    """A tracked object across multiple frames in a camera feed."""

    model_config = ConfigDict(frozen=True)

    track_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str
    zone_id: str | None = None
    plant_id: str | None = None
    object_class: str
    hazard_type: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    entry_zone: str | None = None
    exit_zone: str | None = None
    speed_estimate: float = Field(default=0.0)
    direction_angle: float = Field(default=0.0)
    trajectory: list[dict[str, Any]] = Field(default_factory=list)
    zone_crossings: list[ZoneCrossing] = Field(default_factory=list)
    is_active: bool = True
    frame_count: int = Field(default=1, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def duration_seconds(self) -> float:
        """Time elapsed between first and last sighting in seconds."""
        return (self.last_seen_at - self.first_seen_at).total_seconds()

    @property
    def is_person(self) -> bool:
        """True when the tracked object class is PERSON."""
        return self.object_class.upper() == "PERSON"

    @property
    def crossed_restricted_zone(self) -> bool:
        """True when the object has at least one zone crossing recorded."""
        return len(self.zone_crossings) > 0

    # ── State transitions (return new frozen instances) ────────────────────────

    def update_position(
        self,
        frame_id: str,
        bbox: dict[str, Any],
        timestamp: datetime,
    ) -> "TrackingObject":
        """Append a trajectory point and update last_seen_at and frame_count."""
        new_trajectory = [
            *self.trajectory,
            {"frame_id": frame_id, "bbox": bbox, "timestamp": timestamp.isoformat()},
        ]
        return self.model_copy(update={
            "trajectory": new_trajectory,
            "last_seen_at": timestamp,
            "frame_count": self.frame_count + 1,
        })

    def add_zone_crossing(self, crossing: ZoneCrossing) -> "TrackingObject":
        """Return a new instance with the zone crossing appended."""
        return self.model_copy(update={
            "zone_crossings": [*self.zone_crossings, crossing],
        })

    def deactivate(self) -> "TrackingObject":
        """Mark the track as no longer active and record the exit zone."""
        exit_z = self.zone_crossings[-1].zone_id if self.zone_crossings else self.exit_zone
        return self.model_copy(update={"is_active": False, "exit_zone": exit_z})

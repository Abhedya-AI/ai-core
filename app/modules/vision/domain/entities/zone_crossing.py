"""
domain/entities/zone_crossing.py — ZoneCrossing value object.

Records a single event where a tracked object crossed a zone boundary.
Used to build intrusion/occupancy timeline for TrackingHistory.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class ZoneCrossing(BaseModel):
    """A boundary-crossing event for a tracked object."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    track_id: str
    zone_id: str
    zone_name: str = ""
    direction: str = Field(
        default="ENTER",
        description="ENTER or EXIT — direction of crossing.",
    )
    is_restricted: bool = Field(
        default=False,
        description="True if this zone is restricted-access.",
    )
    crossed_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @property
    def is_entry(self) -> bool:
        return self.direction.upper() == "ENTER"

    @property
    def is_exit(self) -> bool:
        return self.direction.upper() == "EXIT"

    @property
    def is_violation(self) -> bool:
        """True if entry into a restricted zone."""
        return self.is_entry and self.is_restricted

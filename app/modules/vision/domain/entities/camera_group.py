"""
domain/entities/camera_group.py — CameraGroup domain entity.

Represents a logical grouping of cameras covering a zone or functional area.
Camera groups allow bulk operations, alert correlation, and occupancy rollup
across multiple cameras within the same zone or plant section.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CameraGroup(BaseModel):
    """Logical grouping of cameras covering a zone or functional area."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    zone_id: str | None = None
    plant_id: str | None = None
    camera_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def camera_count(self) -> int:
        """Number of cameras in this group."""
        return len(self.camera_ids)

    # ── State transitions (return new frozen instances) ────────────────────────

    def add_camera(self, camera_id: str) -> "CameraGroup":
        """Return a new CameraGroup with camera_id appended (idempotent)."""
        if camera_id in self.camera_ids:
            return self
        return self.model_copy(update={
            "camera_ids": [*self.camera_ids, camera_id],
            "updated_at": datetime.now(tz=timezone.utc),
        })

    def remove_camera(self, camera_id: str) -> "CameraGroup":
        """Return a new CameraGroup with camera_id removed."""
        return self.model_copy(update={
            "camera_ids": [cid for cid in self.camera_ids if cid != camera_id],
            "updated_at": datetime.now(tz=timezone.utc),
        })

"""
domain/entities/camera.py — Camera domain entity.

Represents a physical or virtual camera registered in the Vision Intelligence
System. Supports RTSP, USB, IP, file-based, and upload-based sources.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.vision.domain.enums.camera_type import CameraType
from app.modules.vision.domain.enums.camera_status import CameraStatus


class Camera(BaseModel):
    """Camera registered in the Vision Intelligence System."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    camera_type: CameraType = CameraType.IP
    stream_url: str | None = None
    location: str = Field(..., min_length=1)
    zone_id: str | None = None
    plant_id: str | None = None
    group_id: str | None = None
    username: str | None = None
    fps_limit: int = Field(default=5, ge=1, le=30)
    resolution: str = Field(default="1280x720")
    is_active: bool = True
    is_recording: bool = False
    health_status: CameraStatus = CameraStatus.OFFLINE
    last_seen_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def is_online(self) -> bool:
        """True when the camera is currently ONLINE."""
        return self.health_status == CameraStatus.ONLINE

    @property
    def is_rtsp(self) -> bool:
        """True when the camera uses the RTSP protocol."""
        return self.camera_type == CameraType.RTSP

    @property
    def stream_key(self) -> str:
        """Unique composite key used to identify an active stream session."""
        return f"{self.id}:{self.camera_type.value}"

    # ── State transitions (return new frozen instances) ────────────────────────

    def mark_online(self) -> "Camera":
        """Return a new Camera instance with ONLINE health status."""
        return self.model_copy(update={
            "health_status": CameraStatus.ONLINE,
            "updated_at": datetime.now(tz=timezone.utc),
        })

    def mark_offline(self) -> "Camera":
        """Return a new Camera instance with OFFLINE health status."""
        return self.model_copy(update={
            "health_status": CameraStatus.OFFLINE,
            "updated_at": datetime.now(tz=timezone.utc),
        })

    def mark_degraded(self) -> "Camera":
        """Return a new Camera instance with DEGRADED health status."""
        return self.model_copy(update={
            "health_status": CameraStatus.DEGRADED,
            "updated_at": datetime.now(tz=timezone.utc),
        })

    def mark_reconnecting(self) -> "Camera":
        """Return a new Camera instance with RECONNECTING health status."""
        return self.model_copy(update={
            "health_status": CameraStatus.RECONNECTING,
            "updated_at": datetime.now(tz=timezone.utc),
        })

    def set_recording(self, flag: bool) -> "Camera":
        """Return a new Camera instance with is_recording set to flag."""
        return self.model_copy(update={
            "is_recording": flag,
            "updated_at": datetime.now(tz=timezone.utc),
        })

    def update_last_seen(self) -> "Camera":
        """Return a new Camera instance with last_seen_at set to now."""
        return self.model_copy(update={
            "last_seen_at": datetime.now(tz=timezone.utc),
            "updated_at": datetime.now(tz=timezone.utc),
        })

"""
domain/entities/camera_health.py — CameraHealth domain entity.

Tracks real-time operational health metrics for a registered camera.
Updated on each heartbeat/telemetry push from the camera infrastructure.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.vision.domain.enums.camera_status import CameraStatus


class CameraHealth(BaseModel):
    """Real-time health telemetry for a single camera."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str
    status: CameraStatus = CameraStatus.OFFLINE
    fps_actual: float = Field(default=0.0, ge=0.0, description="Measured FPS over last sample window.")
    fps_target: float = Field(default=5.0, ge=0.0, description="Configured target FPS.")
    frame_drop_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Fraction of frames dropped [0..1].")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Stream capture-to-ingest latency in ms.")
    uptime_seconds: float = Field(default=0.0, ge=0.0, description="Cumulative uptime since last restart.")
    reconnect_count: int = Field(default=0, ge=0, description="Number of reconnection attempts.")
    last_frame_at: datetime | None = None
    last_heartbeat_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def is_healthy(self) -> bool:
        """True if camera is ONLINE and frame drop rate is acceptable."""
        return (
            self.status == CameraStatus.ONLINE
            and self.frame_drop_rate < 0.10
        )

    @property
    def fps_efficiency(self) -> float:
        """Ratio of actual FPS to target FPS (0.0 to 1.0+)."""
        if self.fps_target <= 0:
            return 0.0
        return round(self.fps_actual / self.fps_target, 4)

    @property
    def uptime_hours(self) -> float:
        """Uptime in hours (rounded to 2 dp)."""
        return round(self.uptime_seconds / 3600.0, 2)

"""
domain/entities/video_stream.py — VideoStream domain entity.

Represents an active video stream session originating from a Camera.
Tracks protocol, status, frame counters, drop rate, and timing. All
state transitions return new frozen instances (immutable entity pattern).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StreamProtocol(str, Enum):
    RTSP      = "RTSP"
    HLS       = "HLS"
    MJPEG     = "MJPEG"
    FILE      = "FILE"
    WEBSOCKET = "WEBSOCKET"


class StreamStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    STREAMING    = "STREAMING"
    PAUSED       = "PAUSED"
    STOPPED      = "STOPPED"
    ERROR        = "ERROR"


class VideoStream(BaseModel):
    """Active video stream session from a camera."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str
    protocol: StreamProtocol
    url: str | None = None
    status: StreamStatus = StreamStatus.INITIALIZING
    is_live: bool = True
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    stopped_at: datetime | None = None
    frame_count: int = 0
    dropped_frames: int = 0
    buffer_size: int = Field(default=30, description="Max frames in buffer queue")
    fps_actual: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        """True while the stream is INITIALIZING, STREAMING, or PAUSED."""
        return self.status in {StreamStatus.INITIALIZING, StreamStatus.STREAMING, StreamStatus.PAUSED}

    @property
    def duration_seconds(self) -> float:
        """Elapsed duration of the stream session in seconds."""
        end = self.stopped_at or datetime.now(tz=timezone.utc)
        return (end - self.started_at).total_seconds()

    @property
    def drop_rate(self) -> float:
        """Frame drop rate as a fraction in [0.0, 1.0]."""
        if self.frame_count <= 0:
            return 0.0
        return self.dropped_frames / self.frame_count

    # ── State transitions (return new frozen instances) ────────────────────────

    def start_streaming(self) -> "VideoStream":
        """Transition to STREAMING status."""
        return self.model_copy(update={"status": StreamStatus.STREAMING})

    def pause(self) -> "VideoStream":
        """Transition to PAUSED status."""
        return self.model_copy(update={"status": StreamStatus.PAUSED})

    def stop(self) -> "VideoStream":
        """Transition to STOPPED status and record stopped_at timestamp."""
        return self.model_copy(update={
            "status": StreamStatus.STOPPED,
            "stopped_at": datetime.now(tz=timezone.utc),
        })

    def increment_frame(self, dropped: bool = False) -> "VideoStream":
        """Return a new instance with frame_count incremented (and dropped_frames if dropped=True)."""
        updates: dict[str, Any] = {"frame_count": self.frame_count + 1}
        if dropped:
            updates["dropped_frames"] = self.dropped_frames + 1
        return self.model_copy(update=updates)

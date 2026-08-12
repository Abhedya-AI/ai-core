"""
domain/entities/frame.py — Frame domain entity.

Represents a captured video frame from a camera.
Immutable by design (frozen Pydantic model).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FrameFormat(str, Enum):
    JPEG = "JPEG"
    PNG  = "PNG"
    WEBP = "WEBP"
    RAW  = "RAW"


class Frame(BaseModel):
    """A captured video frame from a camera stream."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str
    stream_id: str | None = None
    sequence_number: int = Field(default=0, ge=0, description="Frame sequence number within the stream.")
    width: int = Field(default=1280, ge=1, description="Frame width in pixels.")
    height: int = Field(default=720, ge=1, description="Frame height in pixels.")
    channels: int = Field(default=3, ge=1, description="Number of color channels (3=RGB, 1=greyscale).")
    format: FrameFormat = FrameFormat.JPEG
    size_bytes: int = Field(default=0, ge=0, description="Raw frame size in bytes.")
    storage_path: str | None = None
    is_key_frame: bool = Field(default=False, description="True if this is an I-frame (key frame).")
    captured_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def resolution(self) -> str:
        """Human-readable resolution string e.g. '1280x720'."""
        return f"{self.width}x{self.height}"

    @property
    def megapixels(self) -> float:
        """Frame size in megapixels."""
        return round((self.width * self.height) / 1_000_000, 3)

    @property
    def has_storage(self) -> bool:
        """True if this frame has been persisted to storage."""
        return self.storage_path is not None and len(self.storage_path) > 0

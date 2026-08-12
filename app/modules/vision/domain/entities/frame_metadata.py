"""
domain/entities/frame_metadata.py — FrameMetadata domain entity.

Rich analytical metadata about a captured frame, produced after
the frame has been processed by the detection pipeline.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FrameMetadata(BaseModel):
    """Analytical metadata produced after processing a video frame."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    frame_id: str
    camera_id: str
    detection_count: int = Field(default=0, ge=0, description="Number of objects detected in this frame.")
    has_hazard: bool = Field(default=False, description="True if any hazard was detected.")
    hazard_types: list[str] = Field(default_factory=list, description="List of detected hazard type values.")
    sharpness_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Blur/sharpness quality metric [0=blurry, 1=sharp].")
    brightness_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Brightness level metric.")
    occlusion_pct: float = Field(default=0.0, ge=0.0, le=1.0, description="Fraction of frame occluded.")
    processing_ms: float = Field(default=0.0, ge=0.0, description="Pipeline processing latency in ms.")
    model_version: str = Field(default="yolov8n", description="Detection model version used.")
    risk_level: str | None = None
    risk_score: float | None = None
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def is_sharp(self) -> bool:
        """True if the frame is acceptably sharp (≥ 0.6)."""
        return self.sharpness_score >= 0.6

    @property
    def has_detections(self) -> bool:
        """True if at least one object was detected."""
        return self.detection_count > 0

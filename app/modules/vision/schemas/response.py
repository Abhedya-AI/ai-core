"""
schemas/response.py — Pydantic response schemas for the Vision API.

These define the API contract on the output side. Application use-cases
return domain entities; the API routes convert them to these schemas
before serialising to JSON.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── BoundingBox ───────────────────────────────────────────────────────────────

class BoundingBoxSchema(BaseModel):
    """Normalised bounding box in image space ([0, 1])."""

    x_min: float = Field(..., description="Left edge (normalised).")
    y_min: float = Field(..., description="Top edge (normalised).")
    x_max: float = Field(..., description="Right edge (normalised).")
    y_max: float = Field(..., description="Bottom edge (normalised).")


# ── RiskScore ─────────────────────────────────────────────────────────────────

class RiskScoreSchema(BaseModel):
    """Business representation of calculated risk."""

    score: float = Field(..., description="Continuous risk score ∈ [0, 1].")
    level: str = Field(..., description="Discrete RiskLevel.")
    reason: str = Field(default="", description="Human-readable explanation.")


# ── Camera ────────────────────────────────────────────────────────────────────

class CameraSchema(BaseModel):
    """Camera registered in the Vision System."""

    id: UUID = Field(..., description="Unique camera UUID.")
    name: str = Field(..., description="Camera name.")
    location: str = Field(..., description="Camera location / zone.")
    is_active: bool = Field(default=True, description="Whether camera is active.")
    created_at: datetime = Field(..., description="UTC creation timestamp.")


# ── Detection ─────────────────────────────────────────────────────────────────

class DetectionSchema(BaseModel):
    """A single detected hazard persisted in the database."""

    id: UUID = Field(..., description="Unique detection UUID.")
    camera_id: UUID = Field(..., description="Unique camera UUID.")
    hazard_type: str = Field(..., description="Canonical HazardType value.")
    confidence: float = Field(..., description="Model confidence ∈ [0, 1].")
    bounding_box: BoundingBoxSchema = Field(..., description="Object location in the frame.")
    risk: RiskScoreSchema = Field(..., description="Calculated risk score.")
    status: str = Field(..., description="Lifecycle status (PENDING/VERIFIED/REJECTED/ARCHIVED).")
    detected_at: datetime = Field(..., description="UTC detection timestamp.")


# ── VisionEvent ───────────────────────────────────────────────────────────────

class VisionEventSchema(BaseModel):
    """Event published to Kafka after successful hazard detection."""

    event_id: UUID = Field(..., description="Unique event UUID.")
    detection_id: UUID = Field(..., description="Unique detection UUID.")
    camera_id: UUID = Field(..., description="Unique camera UUID.")
    hazard_type: str = Field(..., description="Canonical HazardType value.")
    risk_level: str = Field(..., description="Discrete RiskLevel.")
    confidence: float = Field(..., description="Model confidence ∈ [0, 1].")
    occurred_at: datetime = Field(..., description="UTC event timestamp.")


# ── API Endpoint Responses ────────────────────────────────────────────────────

class AnalyzeFrameResponse(BaseModel):
    """Response body for POST /api/v1/vision/analyze."""

    success: bool = Field(..., description="Whether analysis succeeded.")
    message: str = Field(..., description="Status message.")
    events: list[VisionEventSchema] = Field(default_factory=list, description="Events published for detections.")


class ListEventsResponse(BaseModel):
    """Response body for GET /api/v1/vision/events."""

    total: int = Field(..., description="Total matching events (before pagination).")
    limit: int = Field(..., description="Page size used.")
    offset: int = Field(..., description="Current offset.")
    events: list[VisionEventSchema] = Field(default_factory=list)


class GetEventResponse(BaseModel):
    """Response body for GET /api/v1/vision/events/{event_id}."""

    event: VisionEventSchema | None = Field(
        default=None,
        description="The requested event, or null if not found.",
    )

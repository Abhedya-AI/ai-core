"""
schemas/response.py — Pydantic response schemas for the Vision API.

These define the API contract on the output side.  Application use-cases
return domain entities; the API routes convert them to these schemas
before serialising to JSON.

Design
──────
• Nested schemas mirror the domain entity hierarchy.
• All enums are serialised as plain strings (str values from the Enum).
• Timestamps are serialised as ISO-8601 strings.
• Every field includes an OpenAPI-compatible description.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ── BoundingBox ───────────────────────────────────────────────────────────────

class BoundingBoxSchema(BaseModel):
    """Normalised bounding box in image space ([0, 1])."""

    x_min: float = Field(..., description="Left edge (normalised).")
    y_min: float = Field(..., description="Top edge (normalised).")
    x_max: float = Field(..., description="Right edge (normalised).")
    y_max: float = Field(..., description="Bottom edge (normalised).")


# ── Detection ─────────────────────────────────────────────────────────────────

class DetectionSchema(BaseModel):
    """A single detected object mapped to domain language."""

    id:           str               = Field(..., description="Unique detection UUID.")
    hazard_type:  str               = Field(..., description="Canonical HazardType value.")
    status:       str               = Field(..., description="Lifecycle status (PENDING/VERIFIED/REJECTED/ARCHIVED).")
    confidence:   float             = Field(..., description="Model confidence ∈ [0, 1].")
    bounding_box: BoundingBoxSchema = Field(..., description="Object location in the frame.")
    frame_id:     str               = Field(..., description="Source frame identifier.")
    camera_id:    str               = Field(..., description="Source camera identifier.")
    timestamp:    datetime          = Field(..., description="UTC detection timestamp.")
    image_path:   str | None       = Field(default=None, description="Persisted frame path.")


# ── Hazard ────────────────────────────────────────────────────────────────────

class HazardSchema(BaseModel):
    """A domain-level hazard aggregated from one or more detections."""

    id:                   str               = Field(..., description="Unique hazard UUID.")
    hazard_type:          str               = Field(..., description="Canonical HazardType value.")
    confidence:           float             = Field(..., description="Aggregated confidence ∈ [0, 1].")
    risk_level:           str               = Field(..., description="Discrete risk level for this hazard.")
    bounding_box:         BoundingBoxSchema = Field(..., description="Bounding region.")
    source_detection_ids: list[str]         = Field(..., description="Detection IDs contributing to this hazard.")
    description:          str               = Field(..., description="Human-readable hazard summary.")
    timestamp:            datetime          = Field(..., description="UTC hazard timestamp.")
    requires_immediate_action: bool         = Field(..., description="True for HIGH or CRITICAL hazards.")


# ── RiskScore ─────────────────────────────────────────────────────────────────

class RiskScoreSchema(BaseModel):
    """Aggregated risk assessment for the analysed frame."""

    score:       float = Field(..., description="Continuous risk score ∈ [0, 1].")
    level:       str   = Field(..., description="Discrete RiskLevel.")
    is_critical: bool  = Field(..., description="True when level = CRITICAL.")
    reason:      str   = Field(default="", description="Human-readable explanation of the risk score.")


# ── VisionEvent ───────────────────────────────────────────────────────────────

class VisionEventSchema(BaseModel):
    """Full serialised VisionEvent returned after frame analysis."""

    event_id:        str                  = Field(..., description="Unique event UUID.")
    timestamp:       datetime             = Field(..., description="UTC analysis timestamp.")
    camera_id:       str                  = Field(..., description="Source camera.")
    frame_id:        str                  = Field(..., description="Source frame.")
    detection_count: int                  = Field(..., description="Total detections.")
    hazard_count:    int                  = Field(..., description="Total hazards.")
    is_critical:     bool                 = Field(..., description="True when risk level = CRITICAL.")
    risk_score:      RiskScoreSchema      = Field(..., description="Aggregated risk assessment.")
    detections:      list[DetectionSchema]= Field(default_factory=list)
    hazards:         list[HazardSchema]   = Field(default_factory=list)
    image_path:      str | None          = Field(default=None, description="Persisted frame path.")
    location:        str | None          = Field(default=None, description="Location string.")
    metadata:        dict[str, str]      = Field(default_factory=dict)


# ── Top-level API responses ───────────────────────────────────────────────────

class AnalyzeFrameResponse(BaseModel):
    """
    Response body for POST /api/v1/vision/analyze.

    success     False only if analysis completed but produced a fatal
                internal error (HTTP 500 is used for unexpected errors).
    message     Human-readable status message.
    event       Full VisionEvent (None if success=False).
    """

    success: bool              = Field(..., description="Whether analysis succeeded.")
    message: str               = Field(..., description="Status message.")
    event:   VisionEventSchema | None = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Frame analysed successfully.",
                    "event": {
                        "event_id": "a1b2c3d4-...",
                        "timestamp": "2024-01-15T09:00:00Z",
                        "camera_id": "CAM-PLANT-A-01",
                        "frame_id": "frame-00123",
                        "detection_count": 3,
                        "hazard_count": 2,
                        "is_critical": False,
                        "risk_score": {
                            "value": 0.72,
                            "level": "HIGH",
                            "is_actionable": True,
                            "contributing_hazards": [
                                {"hazard": "NO_HELMET", "weight": 0.6},
                                {"hazard": "FIRE", "weight": 0.4},
                            ],
                        },
                        "detections": [],
                        "hazards": [],
                        "image_path": "/storage/frames/frame-00123.jpg",
                        "location": "Zone-3",
                        "metadata": {},
                    },
                }
            ]
        }
    }


class ListEventsResponse(BaseModel):
    """Response body for GET /api/v1/vision/events."""

    total:  int                    = Field(..., description="Total matching events (before pagination).")
    limit:  int                    = Field(..., description="Page size used.")
    offset: int                    = Field(..., description="Current offset.")
    events: list[VisionEventSchema]= Field(default_factory=list)


class GetEventResponse(BaseModel):
    """Response body for GET /api/v1/vision/events/{event_id}."""

    event: VisionEventSchema | None = Field(
        default=None,
        description="The requested event, or null if not found.",
    )

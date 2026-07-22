"""
schemas/request.py — Pydantic request schemas for the Vision API.

These define the API contract on the input side.  Application use-cases
receive these objects after FastAPI has validated and parsed the request.

Separation from domain
──────────────────────
Request schemas carry HTTP/API concerns (field aliases, validation
messages, OpenAPI examples) that would pollute the domain.  The
application layer converts them to domain calls.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Frame analysis ────────────────────────────────────────────────────────────

class AnalyzeFrameRequest(BaseModel):
    """
    Request body for POST /api/v1/vision/analyze.

    The client submits the raw image as a multipart file upload.
    This model carries the metadata that accompanies the file.

    Fields
    ──────
    camera_id   Identifies the source camera / feed.
    frame_id    Caller-assigned identifier for this frame.
                Defaults to a server-generated UUID if omitted.
    location    Optional free-text or "lat,lon" string.
    min_confidence
                Detections below this threshold are discarded.
                Range [0, 1]; default 0.4.
    save_image  Whether to persist the raw frame to storage.
    metadata    Arbitrary key-value bag forwarded to the VisionEvent.
    """

    camera_id:      str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Identifier of the source camera or video feed.",
        examples=["CAM-PLANT-A-01"],
    )
    frame_id:       str | None = Field(
        default=None,
        max_length=128,
        description="Caller-assigned frame identifier. Auto-generated if omitted.",
        examples=["frame-2024-01-15T09:00:00-000001"],
    )
    location:       str | None = Field(
        default=None,
        max_length=256,
        description='Optional location string, e.g. "Zone-3" or "12.9716,77.5946".',
        examples=["Zone-3, Building-B"],
    )
    min_confidence: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold. Detections below this are dropped.",
        examples=[0.5],
    )
    save_image:     bool = Field(
        default=True,
        description="If True, persist the analysed frame to object storage.",
    )
    metadata:       dict[str, str] = Field(
        default_factory=dict,
        description="Arbitrary metadata forwarded to the VisionEvent.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "camera_id": "CAM-PLANT-A-01",
                    "frame_id": "frame-00123",
                    "location": "Zone-3, Building-B",
                    "min_confidence": 0.5,
                    "save_image": True,
                    "metadata": {"shift": "morning", "operator": "op-42"},
                }
            ]
        }
    }


# ── Event retrieval ───────────────────────────────────────────────────────────

class ListEventsRequest(BaseModel):
    """
    Query parameters for GET /api/v1/vision/events.

    All fields are optional; they compose into a server-side filter.
    """

    camera_id:   str | None = Field(default=None, description="Filter by camera ID.")
    min_risk:    str | None = Field(
        default=None,
        description="Minimum risk level: LOW | MEDIUM | HIGH | CRITICAL.",
        examples=["HIGH"],
    )
    hazard_type: str | None = Field(
        default=None,
        description="Filter events containing this hazard type.",
        examples=["FIRE"],
    )
    since:       str | None = Field(
        default=None,
        description="ISO-8601 datetime — return events on or after this timestamp.",
        examples=["2024-01-15T00:00:00Z"],
    )
    until:       str | None = Field(
        default=None,
        description="ISO-8601 datetime — return events on or before this timestamp.",
        examples=["2024-01-15T23:59:59Z"],
    )
    limit:       int = Field(default=50, ge=1, le=200, description="Page size.")
    offset:      int = Field(default=0, ge=0, description="Pagination offset.")

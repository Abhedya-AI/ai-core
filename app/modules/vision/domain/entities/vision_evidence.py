"""
domain/entities/vision_evidence.py — Vision Evidence Package Model.

Consolidates bounding boxes, confidence, camera metadata, frame timestamps,
Knowledge Graph context, Sensor Intelligence context, GraphRAG citations,
and reasoning summaries into a single strongly typed package for Supervisor
and downstream consumption.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    confidence: float = 1.0
    label: str = ""


class VisionEvidence(BaseModel):
    """
    Structured Evidence Package accompanying every AI safety assessment decision.
    """

    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str
    camera_name: str | None = None
    zone_id: str | None = None
    plant_id: str | None = None
    frame_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    frame_id: str | None = None

    # Visual Evidence
    primary_detection_label: str
    detection_confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_boxes: list[BoundingBox] = Field(default_factory=list)
    snapshot_url: str | None = None

    # Contextual Evidence
    knowledge_graph_path: list[str] = Field(default_factory=list)
    graphrag_sources: list[str] = Field(default_factory=list)
    sensor_telemetry: dict[str, Any] = Field(default_factory=dict)
    historical_incident_ids: list[str] = Field(default_factory=list)

    # Reasoning Summary
    reasoning_summary: str
    relevant_regulations: list[str] = Field(default_factory=list)
    alternative_interpretations: list[str] = Field(default_factory=list)

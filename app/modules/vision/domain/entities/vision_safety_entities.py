"""
domain/entities/vision_safety_entities.py — Domain Entities for Vision Safety Intelligence Engine.

Contains PPEViolation, VisionViolation, WorkerActivity, EquipmentInteraction,
ZoneOccupancy, and HeatmapGrid entities.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PPEViolation(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    worker_id: str | None = None
    camera_id: str
    zone_id: str
    missing_ppe: list[str]  # e.g., ['HELMET', 'SAFETY_VEST']
    detected_ppe: list[str] = Field(default_factory=list)
    compliance_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: str = "HIGH"
    policy_id: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VisionViolation(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    violation_type: str  # UNSAFE_BEHAVIOR | RESTRICTED_ZONE | PROXIMITY
    severity: str = "HIGH"
    worker_id: str | None = None
    camera_id: str
    zone_id: str
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_id: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WorkerActivity(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    worker_id: str
    activity_type: str  # WALKING | STANDING | LIFTING | OPERATING_MACHINERY | FALLEN
    camera_id: str
    zone_id: str
    duration_seconds: float = 0.0
    velocity: float = 0.0
    pose_confidence: float = 1.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EquipmentInteraction(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    worker_id: str
    equipment_id: str
    equipment_type: str  # FORKLIFT | CRANE | ROBOT_CELL | ROTATING_MACHINERY
    distance_meters: float
    is_unsafe_proximity: bool = False
    interaction_type: str = "UNSAFE_PROXIMITY"
    duration_seconds: float = 0.0
    camera_id: str
    zone_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ZoneOccupancy(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    zone_id: str
    worker_count: int = 0
    density_ratio: float = 0.0
    capacity_limit: int = 50
    is_congested: bool = False
    is_capacity_exceeded: bool = False
    evacuation_progress_pct: float | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HeatmapCell(BaseModel):
    x_cell: int
    y_cell: int
    intensity: float = 0.0
    detection_count: int = 0


class HeatmapGrid(BaseModel):
    zone_id: str
    camera_id: str
    grid_rows: int = 10
    grid_cols: int = 10
    cells: list[HeatmapCell] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

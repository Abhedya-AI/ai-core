"""
application/dto/vision_safety_dto.py — Vision Safety Application DTOs.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PPECheckRequest(BaseModel):
    camera_id: str
    zone_id: str
    detected_ppe: list[str]
    worker_id: str | None = None
    worker_role: str | None = None
    equipment_type: str | None = None


class ZoneAccessCheckRequest(BaseModel):
    camera_id: str
    zone_id: str
    worker_id: str | None = None
    worker_role: str | None = None
    worker_x: float
    worker_y: float
    polygon: list[tuple[float, float]]
    allowed_roles: list[str] = Field(default_factory=list)
    dwell_time_seconds: float = 0.0


class InteractionCheckRequest(BaseModel):
    camera_id: str
    zone_id: str
    worker_id: str
    equipment_id: str
    equipment_type: str
    worker_pos: tuple[float, float]
    equipment_pos: tuple[float, float]


class FallEvaluationRequest(BaseModel):
    camera_id: str
    zone_id: str
    worker_id: str
    bbox_aspect_ratio: float
    downward_velocity: float
    is_crouching: bool = False


class FireVerificationRequest(BaseModel):
    camera_id: str
    zone_id: str
    visual_type: str  # 'FIRE' or 'SMOKE'
    camera_confidence: float = 0.85
    sensor_smoke_detected: bool = False
    sensor_temp_celsius: float | None = None
    sensor_gas_ppm: float | None = None


class VisionAIProcessRequest(BaseModel):
    camera_id: str
    zone_id: str
    detected_ppe: list[str] = Field(default_factory=list)
    worker_id: str | None = None
    behavior_type: str | None = None
    velocity: float = 0.0
    equipment_id: str | None = None
    equipment_type: str | None = None
    bbox_aspect_ratio: float = 0.5
    visual_hazard_type: str | None = None

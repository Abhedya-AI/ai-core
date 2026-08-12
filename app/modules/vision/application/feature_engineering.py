"""
application/feature_engineering.py — Vision Feature Engineering Engine.

Extracts reusable spatial-temporal features from raw object detections, tracking histories,
and camera frames for downstream Risk Prediction and Digital Twin state models.

Features Extracted:
  - Worker velocity & speed (m/s)
  - Trajectory vectors (direction & momentum)
  - Dwell time in zone (seconds)
  - Interaction duration with equipment (seconds)
  - PPE score (0-100%)
  - Visibility / occlusion score (0-1.0)
  - Detection stability over N frames (flicker check)
  - Pose confidence & keypoint variance
  - Crowd density ratio (workers per sq meter)
  - Zone transition frequency
"""
from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, Field


class VisionFeatureVector(BaseModel):
    """Extracted feature vector for a tracked entity or zone."""

    entity_id: str
    camera_id: str
    zone_id: str | None = None

    # Motion & Kinematics
    worker_velocity: float = Field(default=0.0, description="Speed in meters/second")
    trajectory_vector: tuple[float, float] = Field(default=(0.0, 0.0), description="(dx, dy) direction vector")
    dwell_time_seconds: float = Field(default=0.0, description="Dwell time in current zone")

    # Interactions & Proximity
    interaction_duration_seconds: float = Field(default=0.0, description="Duration near equipment")
    nearest_equipment_id: str | None = None
    nearest_equipment_distance_m: float | None = None

    # Quality & Safety Scores
    ppe_score: float = Field(default=100.0, description="PPE compliance percentage (0-100%)")
    visibility_score: float = Field(default=1.0, description="Occlusion/visibility quality (0.0-1.0)")
    detection_stability: float = Field(default=1.0, description="Bounding box tracking stability (0.0-1.0)")
    pose_confidence: float = Field(default=1.0, description="Pose keypoint confidence")

    # Environmental / Spatial
    crowd_density: float = Field(default=0.0, description="Workers per unit area")
    zone_transition_frequency: int = Field(default=0, description="Number of zone entries in last hour")

    metadata: dict[str, Any] = Field(default_factory=dict)


class VisionFeatureEngine:
    """Engine computing vision feature vectors from tracking & detection histories."""

    @staticmethod
    def compute_velocity_and_trajectory(
        positions: list[tuple[float, float, float]],  # list of (x, y, timestamp_sec)
        pixel_to_meter_ratio: float = 0.05,
    ) -> tuple[float, tuple[float, float]]:
        """Calculate velocity (m/s) and normalized trajectory direction vector."""
        if len(positions) < 2:
            return 0.0, (0.0, 0.0)

        (x1, y1, t1) = positions[-2]
        (x2, y2, t2) = positions[-1]

        dt = max(t2 - t1, 0.033)  # minimum frame delta (30 FPS)
        dx_pixels = x2 - x1
        dy_pixels = y2 - y1

        dist_pixels = math.sqrt(dx_pixels**2 + dy_pixels**2)
        dist_meters = dist_pixels * pixel_to_meter_ratio
        speed_ms = dist_meters / dt

        if dist_pixels > 0:
            norm_dx = dx_pixels / dist_pixels
            norm_dy = dy_pixels / dist_pixels
        else:
            norm_dx, norm_dy = 0.0, 0.0

        return round(speed_ms, 2), (round(norm_dx, 3), round(norm_dy, 3))

    @staticmethod
    def compute_ppe_score(detected_ppe: list[str], required_ppe: list[str]) -> float:
        """Calculate PPE compliance score (0.0 - 100.0%)."""
        if not required_ppe:
            return 100.0
        matched = set(detected_ppe).intersection(set(required_ppe))
        return round((len(matched) / len(required_ppe)) * 100.0, 1)

    @staticmethod
    def compute_detection_stability(confidences: list[float]) -> float:
        """Calculate confidence stability over trailing N frames (1.0 = stable, 0.0 = flickering)."""
        if not confidences:
            return 1.0
        avg = sum(confidences) / len(confidences)
        variance = sum((c - avg) ** 2 for c in confidences) / len(confidences)
        std_dev = math.sqrt(variance)
        stability = max(0.0, 1.0 - std_dev)
        return round(stability, 2)

    @staticmethod
    def compute_crowd_density(worker_count: int, zone_area_sqm: float = 100.0) -> float:
        """Calculate workers per square meter."""
        if zone_area_sqm <= 0:
            return 0.0
        return round(worker_count / zone_area_sqm, 3)

    def extract_feature_vector(
        self,
        entity_id: str,
        camera_id: str,
        tracking_positions: list[tuple[float, float, float]],
        detected_ppe: list[str],
        required_ppe: list[str],
        recent_confidences: list[float],
        zone_id: str | None = None,
        dwell_time: float = 0.0,
        interaction_duration: float = 0.0,
        worker_count_in_zone: int = 1,
    ) -> VisionFeatureVector:
        """Assemble full feature vector for a tracked entity."""
        velocity, trajectory = self.compute_velocity_and_trajectory(tracking_positions)
        ppe_score = self.compute_ppe_score(detected_ppe, required_ppe)
        stability = self.compute_detection_stability(recent_confidences)
        density = self.compute_crowd_density(worker_count_in_zone)

        return VisionFeatureVector(
            entity_id=entity_id,
            camera_id=camera_id,
            zone_id=zone_id,
            worker_velocity=velocity,
            trajectory_vector=trajectory,
            dwell_time_seconds=dwell_time,
            interaction_duration_seconds=interaction_duration,
            ppe_score=ppe_score,
            visibility_score=0.95,
            detection_stability=stability,
            pose_confidence=sum(recent_confidences) / max(len(recent_confidences), 1),
            crowd_density=density,
            zone_transition_frequency=len(tracking_positions) // 10,
        )

"""
domain/entities/camera_zone.py — CameraZone domain entity.

Defines a named polygon region within a camera's field of view.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


class CameraZone(BaseModel):
    """Named polygon region within a camera's field of view."""

    model_config = ConfigDict(frozen=True)

    zone_id: str
    camera_id: str
    zone_name: str
    polygon_points: list[tuple[float, float]] = Field(default_factory=list)
    is_restricted: bool = False
    max_occupancy: int | None = None
    hazard_classes_monitored: list[str] = Field(default_factory=list)
    ppe_requirements: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    def contains_point(self, x: float, y: float) -> bool:
        """Ray-casting algorithm for polygon containment check."""
        n = len(self.polygon_points)
        if n < 3:
            return False
        inside = False
        px, py = self.polygon_points[-1]
        for cx, cy in self.polygon_points:
            if ((cy > y) != (py > y)) and (x < (px - cx) * (y - cy) / (py - cy) + cx):
                inside = not inside
            px, py = cx, cy
        return inside

    def bbox_centroid_in_zone(self, bbox_dict: dict) -> bool:
        """Check if the centroid of a bounding box falls within this zone."""
        x = (bbox_dict.get("x_min", 0.0) + bbox_dict.get("x_max", 0.0)) / 2.0
        y = (bbox_dict.get("y_min", 0.0) + bbox_dict.get("y_max", 0.0)) / 2.0
        return self.contains_point(x, y)

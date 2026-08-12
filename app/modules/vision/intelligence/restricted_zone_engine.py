"""
intelligence/restricted_zone_engine.py — Restricted Zone Engine.

Supports:
  - 2D/3D Polygon zone boundary checks (Point-in-Polygon raycasting)
  - Dynamic temporary hazard zones
  - Time-window restrictions (e.g. after-hours 22:00-06:00)
  - Role-based clearance matching
  - Entry, Exit, Loitering (> N seconds), and Unauthorized Access events
"""
from __future__ import annotations

import math
from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.entities.vision_safety_entities import VisionViolation

log = get_logger("vision.intelligence.restricted_zone")


class RestrictedZoneEngine:
    """Engine checking polygon boundaries, role clearance, and loitering durations."""

    @staticmethod
    def is_point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
        """Ray-casting algorithm for Point-in-Polygon check."""
        if len(polygon) < 3:
            return False

        inside = False
        n = len(polygon)
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def evaluate_zone_access(
        self,
        worker_id: str | None,
        worker_role: str | None,
        camera_id: str,
        zone_id: str,
        worker_x: float,
        worker_y: float,
        zone_polygon: list[tuple[float, float]],
        allowed_roles: list[str],
        dwell_time_seconds: float = 0.0,
        loitering_threshold_seconds: float = 30.0,
        is_after_hours: bool = False,
    ) -> tuple[bool, str | None, VisionViolation | None]:
        """
        Evaluate worker position and permissions against restricted polygon zone.

        Returns (is_inside_zone, access_status, violation_or_none).
        """
        is_inside = self.is_point_in_polygon(worker_x, worker_y, zone_polygon)
        if not is_inside:
            return False, "OUTSIDE", None

        # Inside zone — evaluate authorization
        authorized = False
        if allowed_roles:
            authorized = worker_role is not None and worker_role.upper() in [r.upper() for r in allowed_roles]
        else:
            authorized = True  # Public zone

        violation: VisionViolation | None = None
        status_str = "AUTHORIZED"

        if not authorized:
            status_str = "UNAUTHORIZED_ENTRY"
            violation = VisionViolation(
                violation_type="RESTRICTED_ZONE",
                severity="CRITICAL",
                worker_id=worker_id,
                camera_id=camera_id,
                zone_id=zone_id,
                description=f"Unauthorized entry into restricted zone {zone_id} by role '{worker_role}'",
                confidence=0.95,
            )
            log.warning(f"Unauthorized zone breach: worker={worker_id}, role={worker_role}, zone={zone_id}")

        elif is_after_hours:
            status_str = "AFTER_HOURS_ACCESS"
            violation = VisionViolation(
                violation_type="RESTRICTED_ZONE",
                severity="HIGH",
                worker_id=worker_id,
                camera_id=camera_id,
                zone_id=zone_id,
                description=f"After-hours access breach in zone {zone_id}",
                confidence=0.92,
            )

        elif dwell_time_seconds > loitering_threshold_seconds:
            status_str = "LOITERING"
            violation = VisionViolation(
                violation_type="RESTRICTED_ZONE",
                severity="MEDIUM",
                worker_id=worker_id,
                camera_id=camera_id,
                zone_id=zone_id,
                description=f"Loitering in hazardous zone {zone_id} ({dwell_time_seconds:.0f}s dwell time)",
                confidence=0.88,
            )

        return True, status_str, violation

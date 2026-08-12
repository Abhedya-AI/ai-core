"""
intelligence/occupancy_engine.py — Occupancy & Density Engine.

Calculates real-time worker count, zone occupancy density, capacity limits,
congestion triggers, and evacuation progress percentages.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.entities.vision_safety_entities import ZoneOccupancy

log = get_logger("vision.intelligence.occupancy")


class OccupancyEngine:
    """Engine monitoring zone worker counts, capacity thresholds, and density."""

    def evaluate_occupancy(
        self,
        zone_id: str,
        detected_worker_count: int,
        capacity_limit: int = 50,
        zone_area_sqm: float = 100.0,
        evacuation_target_count: int | None = None,
    ) -> ZoneOccupancy:
        """Calculate density, capacity excess, and evacuation metrics."""
        density = (
            round(detected_worker_count / zone_area_sqm, 3) if zone_area_sqm > 0 else 0.0
        )
        is_capacity_exceeded = detected_worker_count > capacity_limit
        is_congested = (
            detected_worker_count >= int(capacity_limit * 0.8) or density > 0.5
        )

        evac_pct: float | None = None
        if evacuation_target_count is not None and evacuation_target_count > 0:
            cleared = max(0, evacuation_target_count - detected_worker_count)
            evac_pct = round((cleared / evacuation_target_count) * 100.0, 1)

        if is_capacity_exceeded:
            log.warning(
                f"Zone capacity exceeded: zone={zone_id}, count={detected_worker_count}/{capacity_limit}"
            )

        return ZoneOccupancy(
            zone_id=zone_id,
            worker_count=detected_worker_count,
            density_ratio=density,
            capacity_limit=capacity_limit,
            is_congested=is_congested,
            is_capacity_exceeded=is_capacity_exceeded,
            evacuation_progress_pct=evac_pct,
        )

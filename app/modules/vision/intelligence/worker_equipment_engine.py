"""
intelligence/worker_equipment_engine.py — Worker-Equipment Interaction Engine.

Monitors spatial proximity and interaction dynamics between workers and hazardous equipment:
  - Forklifts
  - Cranes & overhead hoists
  - Robot cells / automated arms
  - Rotating heavy machinery

Calculates Euclidean & bounding-box distances and generates EquipmentInteraction entities.
"""
from __future__ import annotations

import math
from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.entities.vision_safety_entities import EquipmentInteraction

log = get_logger("vision.intelligence.worker_equipment")

# Proximity threshold distances (meters) by equipment type
PROXIMITY_THRESHOLDS: dict[str, float] = {
    "FORKLIFT": 3.0,
    "CRANE": 5.0,
    "ROBOT_CELL": 2.0,
    "ROTATING_MACHINERY": 1.5,
    "DEFAULT": 2.0,
}


class WorkerEquipmentEngine:
    """Engine analyzing worker-equipment proximity and interaction risks."""

    @staticmethod
    def calculate_distance_meters(
        w_x: float, w_y: float, e_x: float, e_y: float, pixel_to_meter: float = 0.05
    ) -> float:
        """Calculate spatial distance in meters between worker and equipment centroids."""
        dist_px = math.sqrt((w_x - e_x) ** 2 + (w_y - e_y) ** 2)
        return round(dist_px * pixel_to_meter, 2)

    def evaluate_interaction(
        self,
        worker_id: str,
        equipment_id: str,
        equipment_type: str,
        worker_pos: tuple[float, float],
        equipment_pos: tuple[float, float],
        camera_id: str,
        zone_id: str,
        interaction_duration: float = 0.0,
    ) -> EquipmentInteraction:
        """
        Evaluate worker and equipment locations and generate EquipmentInteraction entity.
        """
        eq_type_upper = equipment_type.upper()
        threshold = PROXIMITY_THRESHOLDS.get(eq_type_upper, PROXIMITY_THRESHOLDS["DEFAULT"])

        dist_m = self.calculate_distance_meters(
            worker_pos[0], worker_pos[1], equipment_pos[0], equipment_pos[1]
        )
        is_unsafe = dist_m < threshold

        interaction_type = "SAFE_OPERATION"
        if is_unsafe:
            if eq_type_upper == "FORKLIFT":
                interaction_type = "WORKER_NEAR_FORKLIFT"
            elif eq_type_upper == "CRANE":
                interaction_type = "WORKER_NEAR_CRANE"
            elif eq_type_upper == "ROBOT_CELL":
                interaction_type = "WORKER_INSIDE_ROBOT_CELL"
            elif eq_type_upper == "ROTATING_MACHINERY":
                interaction_type = "WORKER_NEAR_ROTATING_MACHINERY"
            else:
                interaction_type = "UNSAFE_EQUIPMENT_PROXIMITY"

            log.warning(
                f"Unsafe worker-equipment proximity: worker={worker_id}, equip={equipment_id} ({eq_type_upper}), dist={dist_m}m"
            )

        return EquipmentInteraction(
            worker_id=worker_id,
            equipment_id=equipment_id,
            equipment_type=eq_type_upper,
            distance_meters=dist_m,
            is_unsafe_proximity=is_unsafe,
            interaction_type=interaction_type,
            duration_seconds=interaction_duration,
            camera_id=camera_id,
            zone_id=zone_id,
        )

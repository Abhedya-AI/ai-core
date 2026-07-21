"""occupancy.py — Zone Occupancy & Headcount Module."""

from app.modules.agents.vision.models import VisionDetection


class OccupancyModule:
    """Tracks personnel headcount and zone occupancy thresholds."""

    @staticmethod
    def evaluate_occupancy(zone_id: str, detections: list[VisionDetection], max_capacity: int = 12) -> dict:
        """
        Evaluate worker headcount per zone.

        Returns:
            dict containing 'zone_id', 'headcount', 'max_capacity', and 'over_capacity'.
        """
        person_count = sum(1 for d in detections if d.label.lower() in ("person", "worker", "operator"))
        is_over_capacity = person_count > max_capacity

        return {
            "zone_id": zone_id,
            "headcount": person_count,
            "max_capacity": max_capacity,
            "status": "OVER_CAPACITY" if is_over_capacity else "NORMAL",
            "over_capacity": is_over_capacity,
        }

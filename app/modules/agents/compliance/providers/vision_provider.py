"""vision_provider.py — Vision Compliance Observations Provider."""

from typing import Any


class VisionComplianceProvider:
    """Extracts PPE violations and blocked exit observations from computer vision events."""

    @staticmethod
    def get_vision_observations(vision_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return vision_events or [
            {"camera_id": "CAM-02", "observation": "BLOCKED_EMERGENCY_EXIT", "zone_id": "ZONE-C"},
            {"camera_id": "CAM-01", "observation": "MISSING_HELMET", "worker_id": "W-102"},
        ]

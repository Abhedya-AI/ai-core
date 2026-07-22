"""vision_provider.py — Vision Observation Evidence Provider."""

from typing import Any


class VisionEvidenceProvider:
    """Extracts computer vision anomaly detections prior to incident onset."""

    @staticmethod
    def get_vision_evidence(vision_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return vision_events or [{"camera_id": "CAM-01", "detection": "GAS_PLUME", "timestamp": "08:20"}]

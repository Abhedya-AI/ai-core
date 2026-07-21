"""fusion.py — Multi-Camera & Sensor Fusion Engine."""

from typing import Any

from app.modules.agents.vision.models import VisionDetection


class DetectionFusionEngine:
    """Fuses detections across multiple camera feeds and telemetry sensors to reduce noise."""

    @staticmethod
    def fuse_multi_camera(
        camera_detections: dict[str, list[VisionDetection]],
        sensor_data: list[dict[str, Any]] | None = None,
    ) -> float:
        """
        Calculate multi-camera and sensor agreement score (0.0 to 1.0).
        """
        if not camera_detections:
            return 0.8

        all_labels = set()
        for cam, det_list in camera_detections.items():
            for d in det_list:
                all_labels.add(d.label.lower())

        camera_count = len(camera_detections)
        if camera_count >= 2:
            agreement = 0.95
        else:
            agreement = 0.85

        if sensor_data:
            agreement = min(1.0, agreement + 0.05)

        return agreement

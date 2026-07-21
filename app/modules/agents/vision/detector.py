"""detector.py — Object Detection Engine for Vision Intelligence."""

from typing import Any

from app.core.logging import get_logger
from app.modules.agents.vision.models import BoundingBox, VisionDetection

log = get_logger("agents.vision.detector")


class ObjectDetector:
    """Swappable object detection inferencer (YOLO / OpenCV / mock backend)."""

    def __init__(self, model_version: str = "YOLOv8x-Safety-v1.0") -> None:
        self.model_version = model_version

    def detect_objects(self, frame_data: Any, camera_id: str = "CAM-01") -> list[VisionDetection]:
        """
        Run object detection inference on video frame or stream metadata.

        Returns:
            list of VisionDetection objects.
        """
        log.info(f"Running object detection on camera '{camera_id}' using model '{self.model_version}'")
        detections: list[VisionDetection] = []

        if isinstance(frame_data, list):
            # Frame data passed as raw label strings or dicts
            for idx, item in enumerate(frame_data):
                if isinstance(item, str):
                    detections.append(
                        VisionDetection(
                            label=item,
                            confidence=0.92,
                            bbox=BoundingBox(x_min=0.1 * idx, y_min=0.1, x_max=0.3 * idx + 0.2, y_max=0.5),
                        )
                    )
                elif isinstance(item, dict):
                    detections.append(
                        VisionDetection(
                            label=item.get("label", "person"),
                            confidence=float(item.get("confidence", 0.90)),
                            bbox=BoundingBox(**item.get("bbox", {})),
                        )
                    )
        else:
            # Default mock inference if frame_data is raw bytes or None
            detections = [
                VisionDetection(label="person", confidence=0.95, bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.3, y_max=0.8)),
                VisionDetection(label="helmet", confidence=0.91, bbox=BoundingBox(x_min=0.12, y_min=0.1, x_max=0.25, y_max=0.25)),
                VisionDetection(label="smoke", confidence=0.88, bbox=BoundingBox(x_min=0.5, y_min=0.2, x_max=0.8, y_max=0.6)),
            ]

        return detections

"""smoke.py — Early Smoke Detection Module."""

from app.modules.agents.vision.models import VisionDetection


class SmokeModule:
    """Detects early smoke plume presence separate from flame/fire."""

    @staticmethod
    def detect_smoke(detections: list[VisionDetection]) -> list[VisionDetection]:
        """Extract early smoke detections."""
        smoke_labels = {"smoke", "plume", "dense_smoke", "haze"}
        return [d for d in detections if d.label.lower() in smoke_labels]

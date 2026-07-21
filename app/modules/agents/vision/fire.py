"""fire.py — Fire & Thermal Anomaly Detection Module."""

from app.modules.agents.vision.models import VisionDetection


class FireModule:
    """Detects active flames, sparks, explosions, and hot surface anomalies."""

    @staticmethod
    def detect_fire(detections: list[VisionDetection]) -> list[VisionDetection]:
        """Extract fire detections."""
        fire_labels = {"fire", "flame", "spark", "explosion", "hot_surface"}
        return [d for d in detections if d.label.lower() in fire_labels]

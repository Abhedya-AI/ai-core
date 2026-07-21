"""spill.py — Liquid & Chemical Spill Detection Module."""

from app.modules.agents.vision.models import VisionDetection


class SpillModule:
    """Detects chemical leaks, oil spills, water pooling, and liquid containment breaches."""

    @staticmethod
    def detect_spills(detections: list[VisionDetection]) -> list[VisionDetection]:
        """Extract spill and leak detections."""
        spill_labels = {"spill", "oil_spill", "chemical_leak", "puddle", "liquid_leak"}
        return [d for d in detections if d.label.lower() in spill_labels]

"""confidence.py — Operational Confidence Engine."""

from app.modules.agents.vision.models import VisionConfidence, VisionDetection


class ConfidenceEngine:
    """Computes operational confidence beyond raw detector scores."""

    @staticmethod
    def compute_confidence(
        detections: list[VisionDetection],
        multi_camera_agreement: float = 0.9,
    ) -> VisionConfidence:
        """
        Compute operational confidence metrics.

        Returns:
            VisionConfidence DTO.
        """
        if not detections:
            return VisionConfidence()

        avg_model_conf = sum(d.confidence for d in detections) / len(detections)
        avg_tracker_cons = sum(d.metadata.get("temporal_consistency", 0.9) for d in detections) / len(detections)

        op_confidence = round(
            (avg_model_conf * 0.4) + (avg_tracker_cons * 0.3) + (multi_camera_agreement * 0.3),
            2,
        )

        return VisionConfidence(
            raw_model_confidence=round(avg_model_conf, 2),
            tracker_consistency=round(avg_tracker_cons, 2),
            multi_camera_agreement=round(multi_camera_agreement, 2),
            sensor_agreement=0.95,
            operational_confidence=op_confidence,
        )

"""confidence.py — Multi-Factor Prediction Confidence Engine."""

from app.modules.agents.prediction.models import PredictionConfidence, PredictionFeatures


class PredictionConfidenceEngine:
    """Calculates multi-factor prediction confidence combining model, data, freshness, and quality."""

    @staticmethod
    def calculate_confidence(features: PredictionFeatures, raw_model_conf: float = 0.90) -> PredictionConfidence:
        """
        Compute prediction confidence across multiple data quality vectors.

        Returns:
            PredictionConfidence DTO.
        """
        data_completeness = 0.95 if features.feature_vector else 0.70
        feature_freshness = 0.98 if features.sensor_temp_c > 0 else 0.80
        sensor_quality = 0.92

        overall = round(
            (raw_model_conf * 0.4) + (data_completeness * 0.2) + (feature_freshness * 0.2) + (sensor_quality * 0.2),
            2,
        )

        return PredictionConfidence(
            model_confidence=raw_model_conf,
            data_completeness=data_completeness,
            feature_freshness=feature_freshness,
            sensor_quality=sensor_quality,
            overall_confidence=overall,
        )

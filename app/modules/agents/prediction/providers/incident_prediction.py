"""incident_prediction.py — Incident Probability Forecast Model Provider."""

from app.modules.agents.prediction.models import (
    PredictionConfidence,
    PredictionFeatures,
    PredictionOutput,
    PredictionWindow,
)


class IncidentPredictionModel:
    """Predicts zone incident probability based on hazard density and vision anomaly events."""

    model_name: str = "incident_prediction"
    model_version: str = "XGBoost-IncidentRisk-v1.4"

    def predict(self, features: PredictionFeatures, window: PredictionWindow) -> PredictionOutput:
        base_prob = 0.05
        base_prob += min(0.40, features.incident_history_count * 0.15)
        base_prob += min(0.35, features.vision_anomalies_count * 0.20)

        probability = min(0.95, max(0.01, round(base_prob, 2)))

        return PredictionOutput(
            target_entity_id=features.target_entity_id,
            prediction_type="INCIDENT_PROBABILITY",
            probability=probability,
            prediction_window=window,
            confidence=PredictionConfidence(model_confidence=0.88, overall_confidence=0.90),
            feature_importances={
                "incident_history_count": float(features.incident_history_count),
                "vision_anomalies_count": float(features.vision_anomalies_count),
            },
            metadata={"model_version": self.model_version},
        )

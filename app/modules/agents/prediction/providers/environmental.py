"""environmental.py — Environmental Risk Forecast Model Provider."""

from app.modules.agents.prediction.models import (
    PredictionConfidence,
    PredictionFeatures,
    PredictionOutput,
    PredictionWindow,
)


class EnvironmentalRiskModel:
    """Predicts ambient temperature, gas buildup, and weather risk escalation."""

    model_name: str = "environmental"
    model_version: str = "Prophet-EnviroRisk-v1.0"

    def predict(self, features: PredictionFeatures, window: PredictionWindow) -> PredictionOutput:
        prob = min(0.90, max(0.10, round((features.sensor_temp_c - 20.0) / 50.0, 2)))
        return PredictionOutput(
            target_entity_id=features.target_entity_id,
            prediction_type="ENVIRONMENTAL_RISK",
            probability=prob,
            prediction_window=window,
            confidence=PredictionConfidence(model_confidence=0.89, overall_confidence=0.91),
            feature_importances={"sensor_temp_c": features.sensor_temp_c},
            metadata={"model_version": self.model_version},
        )

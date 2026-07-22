"""maintenance.py — Maintenance Forecast Model Provider."""

from app.modules.agents.prediction.models import (
    PredictionConfidence,
    PredictionFeatures,
    PredictionOutput,
    PredictionWindow,
)


class MaintenanceForecastModel:
    """Predicts optimal preventive maintenance scheduling timelines."""

    model_name: str = "maintenance"
    model_version: str = "LightGBM-MaintForecast-v1.0"

    def predict(self, features: PredictionFeatures, window: PredictionWindow) -> PredictionOutput:
        prob = min(0.95, max(0.10, round(features.operating_hours / 2000.0, 2)))
        recommended_days = max(1.0, round(30.0 - (features.maintenance_overdue_days * 0.8), 1))

        return PredictionOutput(
            target_entity_id=features.target_entity_id,
            prediction_type="MAINTENANCE_FORECAST",
            probability=prob,
            remaining_useful_life_days=recommended_days,
            prediction_window=window,
            confidence=PredictionConfidence(model_confidence=0.91, overall_confidence=0.92),
            feature_importances={"operating_hours": features.operating_hours},
            metadata={"model_version": self.model_version},
        )

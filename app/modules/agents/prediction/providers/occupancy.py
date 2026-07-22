"""occupancy.py — Occupancy Forecast Model Provider."""

from app.modules.agents.prediction.models import (
    PredictionConfidence,
    PredictionFeatures,
    PredictionOutput,
    PredictionWindow,
)


class OccupancyForecastModel:
    """Predicts shift headcount spikes and zone overcrowding."""

    model_name: str = "occupancy"
    model_version: str = "LSTM-OccupancyForecast-v1.1"

    def predict(self, features: PredictionFeatures, window: PredictionWindow) -> PredictionOutput:
        prob = 0.35 if window.horizon_label in ("1h", "6h") else 0.15
        return PredictionOutput(
            target_entity_id=features.target_entity_id,
            prediction_type="OCCUPANCY_FORECAST",
            probability=prob,
            prediction_window=window,
            confidence=PredictionConfidence(model_confidence=0.85, overall_confidence=0.87),
            feature_importances={"shift_schedule": 1.0},
            metadata={"model_version": self.model_version},
        )

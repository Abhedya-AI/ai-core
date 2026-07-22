"""prediction_provider.py — Prediction Forecast Provider."""

from typing import Any


class PredictionEmergencyProvider:
    """Extracts hazard escalation timelines and remaining useful life from Prediction Agent outputs."""

    @staticmethod
    def get_prediction_context(metadata: dict[str, Any]) -> dict[str, Any]:
        return metadata.get(
            "prediction_output",
            {"predicted_escalation_min": 4.0, "hazard_spread_probability": 0.85},
        )

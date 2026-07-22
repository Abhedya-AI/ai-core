"""explanation.py — Feature Importance XAI Explanation Generator."""

from app.modules.agents.prediction.models import PredictionFeatures, PredictionOutput


class PredictionExplanationGenerator:
    """Generates feature importance XAI explanations from prediction outputs."""

    @staticmethod
    def generate_explanation(prediction: PredictionOutput, features: PredictionFeatures) -> str:
        """
        Build feature importance XAI explanation string.

        Example:
        High probability of failure (83.0%) for 'EQ-PUMP-1' within 24h because:
        • Bearing vibration increased 18.5% over baseline.
        • Maintenance overdue by 32 days.
        • Operating temperature reached 82°C.
        """
        target = prediction.target_entity_id
        prob_pct = round(prediction.probability * 100.0, 1)
        horizon = prediction.prediction_window.horizon_label

        lines = [
            f"Prediction Forecast for '{target}' (Horizon: {horizon})",
            f"Forecasted Probability: {prob_pct}% (Type: {prediction.prediction_type})",
            "Root Contributing Features:",
        ]

        if features.sensor_vibration_delta_pct > 0:
            lines.append(f"  • Bearing vibration increased {features.sensor_vibration_delta_pct}% over baseline.")
        if features.sensor_temp_c > 60.0:
            lines.append(f"  • Operating temperature reached {features.sensor_temp_c}°C.")
        if features.maintenance_overdue_days > 0:
            lines.append(f"  • Maintenance overdue by {features.maintenance_overdue_days} days.")
        if prediction.remaining_useful_life_days is not None:
            lines.append(f"  • Estimated Remaining Useful Life (RUL): {prediction.remaining_useful_life_days} days.")

        return "\n".join(lines)

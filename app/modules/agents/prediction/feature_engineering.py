"""feature_engineering.py — Feature Engineering Layer."""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.prediction.models import PredictionFeatures

log = get_logger("agents.prediction.features")


class FeatureEngineer:
    """Transforms raw AgentContext, sensor readings, and maintenance history into structured PredictionFeatures."""

    @staticmethod
    def extract_features(context: AgentContext) -> PredictionFeatures:
        """
        Extract features from AgentContext.

        Returns:
            PredictionFeatures object.
        """
        target_id = context.target_entity_id or "EQ-DEFAULT"
        log.info(f"Extracting prediction features for '{target_id}'")

        vibration_delta = 0.0
        temp_c = 25.0
        for sensor in context.sensor_data:
            stype = str(sensor.get("type", "")).lower()
            val = float(sensor.get("value", 0.0))
            if "vibration" in stype:
                vibration_delta = val
            elif "temp" in stype or "temperature" in stype:
                temp_c = val

        maint_logs = context.metadata.get("maintenance_logs", [])
        overdue_days = sum(int(m.get("overdue_days", 0)) for m in maint_logs)

        incident_count = len(context.metadata.get("incidents", []))
        vision_count = len(context.vision_events or [])
        operating_hours = float(context.metadata.get("operating_hours", 1250.0))

        feature_vector = [
            vibration_delta,
            temp_c,
            float(overdue_days),
            operating_hours,
            float(incident_count),
            float(vision_count),
        ]

        return PredictionFeatures(
            target_entity_id=target_id,
            sensor_vibration_delta_pct=vibration_delta,
            sensor_temp_c=temp_c,
            maintenance_overdue_days=overdue_days,
            operating_hours=operating_hours,
            incident_history_count=incident_count,
            vision_anomalies_count=vision_count,
            feature_vector=feature_vector,
        )

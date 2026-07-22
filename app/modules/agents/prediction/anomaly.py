"""anomaly.py — Telemetry Anomaly Detection Helper."""

from app.modules.agents.prediction.models import PredictionFeatures


class AnomalyDetector:
    """Detects statistical anomalies in telemetry feature vectors."""

    @staticmethod
    def detect_anomalies(features: PredictionFeatures) -> list[str]:
        """Detect feature anomalies exceeding operating baselines."""
        anomalies = []
        if features.sensor_vibration_delta_pct > 15.0:
            anomalies.append(f"Vibration delta spike of +{features.sensor_vibration_delta_pct}% over baseline")
        if features.sensor_temp_c > 75.0:
            anomalies.append(f"Thermal anomaly: operating temp {features.sensor_temp_c}°C exceeds limit")
        if features.maintenance_overdue_days > 14:
            anomalies.append(f"Maintenance overdue by {features.maintenance_overdue_days} days")
        return anomalies

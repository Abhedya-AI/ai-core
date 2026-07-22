"""sensor_provider.py — Sensor Telemetry Timeline Provider."""

from typing import Any


class SensorEvidenceProvider:
    """Extracts chronological sensor reading anomalies."""

    @staticmethod
    def get_sensor_timeline(sensor_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        timeline = []
        for s in sensor_data:
            timeline.append({
                "timestamp": s.get("timestamp", "08:14"),
                "sensor_id": s.get("id", "S-01"),
                "reading": s.get("value", 0.0),
                "threshold": s.get("threshold", 100.0),
                "status": "ANOMALY" if float(s.get("value", 0)) > float(s.get("threshold", 100)) else "NORMAL",
            })
        return timeline

import math
import uuid
from typing import List
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, AnomalyType, AnomalySeverity
from app.modules.sensor.analysis.engine_registry import BaseAnomalyEngine

log = get_logger("sensor.analysis.engines.statistical")

class StatisticalEngine(BaseAnomalyEngine):
    """Z-score outlier detection engine."""
    
    def __init__(self, warning_sigma: float = 2.0, critical_sigma: float = 3.0, min_samples: int = 20):
        self.warning_sigma = warning_sigma
        self.critical_sigma = critical_sigma
        self.min_samples = min_samples

    @property
    def name(self) -> str:
        """Name of the engine."""
        return "StatisticalEngine"

    def analyze(self, reading: SensorReading, history: List[float]) -> List[SensorAnomaly]:
        """Analyze reading using z-score method against history."""
        if len(history) < self.min_samples:
            return []

        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std = math.sqrt(variance)

        if std == 0:
            std = 1e-9  # Prevent division by zero

        z_score = abs(reading.value - mean) / std

        anomalies = []
        if z_score > self.warning_sigma:
            severity = AnomalySeverity.CRITICAL if z_score > self.critical_sigma else AnomalySeverity.MEDIUM
            
            anomaly = SensorAnomaly(
                anomaly_id=str(uuid.uuid4()),
                sensor_id=reading.sensor_id,
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                severity=severity,
                value=reading.value,
                expected_value=round(mean, 4),
                deviation_sigma=round(z_score, 2),
                description=f"Value deviated by {z_score:.2f} sigma from expected {mean:.2f}",
                engine_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            anomalies.append(anomaly)

        return anomalies

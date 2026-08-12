import uuid
from typing import List
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, AnomalyType, AnomalySeverity
from app.modules.sensor.analysis.engine_registry import BaseAnomalyEngine

log = get_logger("sensor.analysis.engines.threshold")

class ThresholdEngine(BaseAnomalyEngine):
    """Static boundary enforcement engine."""
    
    def __init__(self, default_min: float = -1e6, default_max: float = 1e6):
        self.default_min = default_min
        self.default_max = default_max

    @property
    def name(self) -> str:
        """Name of the engine."""
        return "ThresholdEngine"

    def analyze(self, reading: SensorReading, history: List[float]) -> List[SensorAnomaly]:
        """Analyze reading to enforce static boundaries."""
        metadata = reading.metadata or {}
        min_threshold = float(metadata.get("min_threshold", self.default_min))
        max_threshold = float(metadata.get("max_threshold", self.default_max))
        value = reading.value

        anomalies = []
        
        # Check above max
        if value > max_threshold:
            anomalies.append(self._create_anomaly(
                reading, AnomalySeverity.HIGH, 
                f"Value {value} exceeds max threshold {max_threshold}",
                max_threshold
            ))
        elif max_threshold != self.default_max and value >= max_threshold * 0.9:
            anomalies.append(self._create_anomaly(
                reading, AnomalySeverity.LOW, 
                f"Approaching max threshold {max_threshold}",
                max_threshold
            ))
            
        # Check below min
        if value < min_threshold:
            anomalies.append(self._create_anomaly(
                reading, AnomalySeverity.HIGH, 
                f"Value {value} is below min threshold {min_threshold}",
                min_threshold
            ))
        elif min_threshold != self.default_min and value <= min_threshold + abs(min_threshold * 0.1):
            anomalies.append(self._create_anomaly(
                reading, AnomalySeverity.LOW, 
                f"Approaching min threshold {min_threshold}",
                min_threshold
            ))

        return anomalies

    def _create_anomaly(self, reading: SensorReading, severity: AnomalySeverity, description: str, threshold: float) -> SensorAnomaly:
        """Helper to create anomaly objects."""
        return SensorAnomaly(
            anomaly_id=str(uuid.uuid4()),
            sensor_id=reading.sensor_id,
            anomaly_type=AnomalyType.THRESHOLD_BREACH,
            severity=severity,
            value=reading.value,
            threshold=threshold,
            description=description,
            engine_name=self.name,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

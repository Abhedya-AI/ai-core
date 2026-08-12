import uuid
from typing import List
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, AnomalyType, AnomalySeverity
from app.modules.sensor.analysis.engine_registry import BaseAnomalyEngine

log = get_logger("sensor.analysis.engines.rate_of_change")

class RateOfChangeEngine(BaseAnomalyEngine):
    """Rapid change detection engine."""

    def __init__(self, default_max_rate: float = 10.0, critical_multiplier: float = 3.0):
        self.default_max_rate = default_max_rate
        self.critical_multiplier = critical_multiplier

    @property
    def name(self) -> str:
        """Name of the engine."""
        return "RateOfChangeEngine"

    def analyze(self, reading: SensorReading, history: List[float]) -> List[SensorAnomaly]:
        """Analyze reading to detect rapid changes compared to recent history."""
        if len(history) < 1:
            return []

        last_value = history[-1]
        current_value = reading.value
        time_delta = 1.0  
        
        rate = abs(current_value - last_value) / time_delta
        metadata = reading.metadata or {}
        max_rate = float(metadata.get("max_rate_per_sec", self.default_max_rate))

        anomalies = []
        if rate > max_rate:
            severity = AnomalySeverity.CRITICAL if rate > max_rate * self.critical_multiplier else AnomalySeverity.HIGH
            pct_over = ((rate - max_rate) / max_rate) * 100 if max_rate > 0 else 0.0
            
            anomalies.append(SensorAnomaly(
                anomaly_id=str(uuid.uuid4()),
                sensor_id=reading.sensor_id,
                anomaly_type=AnomalyType.RATE_OF_CHANGE,
                severity=severity,
                value=reading.value,
                expected_value=last_value,
                threshold=max_rate,
                description=f"Rate of change {rate:.2f} exceeded limit {max_rate:.2f} by {pct_over:.1f}%",
                engine_name=self.name,
                timestamp=datetime.now(timezone.utc).isoformat()
            ))

        return anomalies

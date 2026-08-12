import uuid
from typing import List
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, AnomalyType, AnomalySeverity
from app.modules.sensor.analysis.engine_registry import BaseAnomalyEngine

log = get_logger("sensor.analysis.engines.pattern")

class PatternEngine(BaseAnomalyEngine):
    """Pattern anomaly detection engine."""

    def __init__(self, stuck_threshold: int = 10, drift_window: int = 30, drift_slope_threshold: float = 0.1):
        self.stuck_threshold = stuck_threshold
        self.drift_window = drift_window
        self.drift_slope_threshold = drift_slope_threshold

    @property
    def name(self) -> str:
        """Name of the engine."""
        return "PatternEngine"

    def analyze(self, reading: SensorReading, history: List[float]) -> List[SensorAnomaly]:
        """Analyze reading for stuck values, drifts, and rapid oscillations."""
        anomalies = []
        full_history = history + [reading.value]

        # 1. Stuck Value Detection
        if len(full_history) >= self.stuck_threshold:
            recent_stuck = full_history[-self.stuck_threshold:]
            if all(v == recent_stuck[0] for v in recent_stuck):
                anomalies.append(self._create_anomaly(
                    reading, AnomalyType.STUCK_VALUE, AnomalySeverity.MEDIUM,
                    f"Value stuck at {recent_stuck[0]} for {self.stuck_threshold} readings"
                ))

        # 2. Drift Detection
        if len(full_history) >= self.drift_window:
            recent_drift = full_history[-self.drift_window:]
            is_increasing = all(recent_drift[i] <= recent_drift[i+1] for i in range(len(recent_drift)-1))
            is_decreasing = all(recent_drift[i] >= recent_drift[i+1] for i in range(len(recent_drift)-1))
            
            if is_increasing or is_decreasing:
                n = len(recent_drift)
                x = list(range(n))
                y = recent_drift
                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(x[i]*y[i] for i in range(n))
                sum_xx = sum(x[i]*x[i] for i in range(n))
                
                denominator = (n * sum_xx - sum_x * sum_x)
                if denominator != 0:
                    slope = (n * sum_xy - sum_x * sum_y) / denominator
                    if abs(slope) > self.drift_slope_threshold:
                        anomalies.append(self._create_anomaly(
                            reading, AnomalyType.DRIFT, AnomalySeverity.MEDIUM,
                            f"Monotonic drift detected with slope {slope:.4f}"
                        ))

        # 3. Oscillation Detection
        oscillation_window = 10
        if len(full_history) >= oscillation_window:
            recent_osc = full_history[-oscillation_window:]
            sign_changes = 0
            last_diff = 0
            for i in range(1, len(recent_osc)):
                diff = recent_osc[i] - recent_osc[i-1]
                if diff == 0:
                    continue
                if last_diff != 0 and (diff * last_diff < 0):
                    sign_changes += 1
                last_diff = diff
            
            if sign_changes > 6:
                anomalies.append(self._create_anomaly(
                    reading, AnomalyType.PATTERN_DEVIATION, AnomalySeverity.LOW,
                    f"Rapid oscillation detected with {sign_changes} direction changes in {oscillation_window} readings"
                ))

        return anomalies

    def _create_anomaly(self, reading: SensorReading, a_type: AnomalyType, severity: AnomalySeverity, desc: str) -> SensorAnomaly:
        """Helper to create anomaly objects."""
        return SensorAnomaly(
            anomaly_id=str(uuid.uuid4()),
            sensor_id=reading.sensor_id,
            anomaly_type=a_type,
            severity=severity,
            value=reading.value,
            description=desc,
            engine_name=self.name,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

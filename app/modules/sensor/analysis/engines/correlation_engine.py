import uuid
import math
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, AnomalyType, AnomalySeverity
from app.modules.sensor.analysis.engine_registry import BaseAnomalyEngine

log = get_logger("sensor.analysis.engines.correlation")

class CorrelationEngine(BaseAnomalyEngine):
    """Cross-sensor correlation break detection engine."""

    def __init__(self, min_correlation: float = 0.7, min_samples: int = 30):
        self.min_correlation = min_correlation
        self.min_samples = min_samples
        self._correlation_pairs: Dict[str, List[str]] = {}
        self._peer_histories: Dict[str, List[float]] = {}

    @property
    def name(self) -> str:
        """Name of the engine."""
        return "CorrelationEngine"

    def register_correlation(self, sensor_id_a: str, sensor_id_b: str) -> None:
        """Register a correlation expectation between two sensors."""
        if sensor_id_a not in self._correlation_pairs:
            self._correlation_pairs[sensor_id_a] = []
        if sensor_id_b not in self._correlation_pairs[sensor_id_a]:
            self._correlation_pairs[sensor_id_a].append(sensor_id_b)

        if sensor_id_b not in self._correlation_pairs:
            self._correlation_pairs[sensor_id_b] = []
        if sensor_id_a not in self._correlation_pairs[sensor_id_b]:
            self._correlation_pairs[sensor_id_b].append(sensor_id_a)

    def update_peer_history(self, sensor_id: str, value: float) -> None:
        """Update history of peer sensors used for correlation calculation."""
        if sensor_id not in self._peer_histories:
            self._peer_histories[sensor_id] = []
        self._peer_histories[sensor_id].append(value)
        if len(self._peer_histories[sensor_id]) > 1000:
            self._peer_histories[sensor_id] = self._peer_histories[sensor_id][-1000:]

    def analyze(self, reading: SensorReading, history: List[float]) -> List[SensorAnomaly]:
        """Analyze reading to detect correlation breaks with peers."""
        anomalies = []
        sensor_id = reading.sensor_id
        full_history = history + [reading.value]
        
        if len(full_history) < self.min_samples:
            return anomalies
            
        correlated_peers = self._correlation_pairs.get(sensor_id, [])
        for peer_id in correlated_peers:
            peer_history = self._peer_histories.get(peer_id, [])
            if len(peer_history) < self.min_samples:
                continue
                
            min_len = min(len(full_history), len(peer_history))
            x = full_history[-min_len:]
            y = peer_history[-min_len:]
            
            corr = self._calculate_pearson(x, y)
            
            if corr is not None and abs(corr) < self.min_correlation:
                anomalies.append(SensorAnomaly(
                    anomaly_id=str(uuid.uuid4()),
                    sensor_id=sensor_id,
                    anomaly_type=AnomalyType.CORRELATION_BREAK,
                    severity=AnomalySeverity.MEDIUM,
                    value=reading.value,
                    expected_value=corr,
                    description=f"Correlation with {peer_id} dropped to {corr:.2f} (expected > {self.min_correlation})",
                    engine_name=self.name,
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))

        return anomalies

    def _calculate_pearson(self, x: List[float], y: List[float]) -> Optional[float]:
        """Calculate Pearson correlation coefficient without numpy."""
        n = len(x)
        if n == 0:
            return None
            
        sum_x = sum(x)
        sum_y = sum(y)
        sum_x_sq = sum(v*v for v in x)
        sum_y_sq = sum(v*v for v in y)
        sum_xy = sum(x[i]*y[i] for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x_sq - sum_x ** 2) * (n * sum_y_sq - sum_y ** 2))
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator

"""
sensor/application/correlation_service.py — Cross-Sensor Correlation Service.

Detects correlation breaks between paired sensors.
Examples: Smoke+Temperature, Gas+Pressure, Humidity+Temperature.
"""
from __future__ import annotations
import math
from datetime import datetime, timezone
from app.core.logging import get_logger
from app.modules.sensor.domain.correlation_models import (
    CorrelationPair, CorrelationResult, CorrelationAlert, CorrelationStrength,
)

log = get_logger("sensor.correlation_service")

class SensorCorrelationService:
    """Evaluates cross-sensor correlations and generates alerts for breaks."""

    def __init__(self):
        """Initialize correlation service with default industrial pairs."""
        self._pairs: dict[str, CorrelationPair] = {}
        self._histories: dict[str, list[float]] = {}
        self._results: list[CorrelationResult] = []
        self._alerts: list[CorrelationAlert] = []

        self._register_default_pairs()

    def _register_default_pairs(self) -> None:
        """Register default expected correlations for industrial safety."""
        # Using dummy IDs for demonstration of default setup, though normally
        # these would be mapped to specific sensor types rather than literal IDs.
        defaults = [
            CorrelationPair(sensor_id_a="SMOKE_TYPE", sensor_id_b="TEMP_TYPE", expected_correlation=0.75),
            CorrelationPair(sensor_id_a="GAS_TYPE", sensor_id_b="PRES_TYPE", expected_correlation=0.70),
            CorrelationPair(sensor_id_a="HUM_TYPE", sensor_id_b="TEMP_TYPE", expected_correlation=0.65),
            CorrelationPair(sensor_id_a="PRES_TYPE", sensor_id_b="VIB_TYPE", expected_correlation=0.60)
        ]
        for pair in defaults:
            self.register_pair(pair)

    def register_pair(self, pair: CorrelationPair) -> None:
        """Register a new correlation pair."""
        self._pairs[pair.pair_id] = pair
        log.info(f"Registered correlation pair {pair.sensor_id_a} <-> {pair.sensor_id_b}")

    def update_history(self, sensor_id: str, value: float, max_history: int = 100) -> None:
        """Add a new value to a sensor's history for correlation."""
        if sensor_id not in self._histories:
            self._histories[sensor_id] = []
        
        self._histories[sensor_id].append(value)
        if len(self._histories[sensor_id]) > max_history:
            self._histories[sensor_id] = self._histories[sensor_id][-max_history:]

    def _pearson(self, xs: list[float], ys: list[float]) -> float:
        """Calculate Pearson correlation coefficient for two datasets."""
        n = min(len(xs), len(ys))
        if n < 2:
            return 0.0

        xs = xs[-n:]
        ys = ys[-n:]

        sum_x = sum(xs)
        sum_y = sum(ys)
        sum_xy = sum(x * y for x, y in zip(xs, ys))
        sum_x2 = sum(x * x for x in xs)
        sum_y2 = sum(y * y for y in ys)

        num = (n * sum_xy) - (sum_x * sum_y)
        den = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
        
        if den == 0:
            return 0.0
            
        return num / den

    def _classify_strength(self, r: float) -> CorrelationStrength:
        """Classify the strength of a Pearson correlation coefficient."""
        abs_r = abs(r)
        if abs_r > 0.8:
            return CorrelationStrength.STRONG
        elif abs_r > 0.5:
            return CorrelationStrength.MODERATE
        elif abs_r > 0.3:
            return CorrelationStrength.WEAK
        return CorrelationStrength.NEGLIGIBLE

    def evaluate_correlations(self) -> list[CorrelationAlert]:
        """Evaluate all enabled correlation pairs and generate alerts if broken."""
        new_alerts = []
        
        for pair in self._pairs.values():
            if not pair.enabled:
                continue
                
            hist_a = self._histories.get(pair.sensor_id_a, [])
            hist_b = self._histories.get(pair.sensor_id_b, [])
            
            n = min(len(hist_a), len(hist_b))
            if n < 10:
                # Require minimum samples
                continue
                
            r = self._pearson(hist_a, hist_b)
            strength = self._classify_strength(r)
            
            dev = 0.0
            is_broken = False
            
            if pair.expected_correlation is not None:
                dev = pair.expected_correlation - r
                if dev > 0.25:
                    is_broken = True

            result = CorrelationResult(
                pair_id=pair.pair_id,
                sensor_id_a=pair.sensor_id_a,
                sensor_id_b=pair.sensor_id_b,
                pearson_r=r,
                strength=strength,
                is_broken=is_broken,
                deviation_from_expected=dev,
                sample_count=n,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            # Update latest result for pair
            self._results = [res for res in self._results if res.pair_id != pair.pair_id]
            self._results.append(result)

            if is_broken:
                alert = CorrelationAlert(
                    pair_id=pair.pair_id,
                    result=result,
                    severity="HIGH",
                    description=f"Correlation broken between {pair.sensor_id_a} and {pair.sensor_id_b}. Expected {pair.expected_correlation:.2f}, got {r:.2f}",
                    recommended_action="Inspect sensors for tampering, drift, or local environmental anomalies."
                )
                self._alerts.append(alert)
                new_alerts.append(alert)
                log.warning(f"Correlation broken alert generated for pair {pair.pair_id}")

        return new_alerts

    def get_pair_result(self, pair_id: str) -> CorrelationResult | None:
        """Get the most recent correlation result for a specific pair."""
        for res in self._results:
            if res.pair_id == pair_id:
                return res
        return None

    def get_all_pairs(self) -> list[CorrelationPair]:
        """Get all registered correlation pairs."""
        return list(self._pairs.values())

    def get_all_results(self) -> list[CorrelationResult]:
        """Get all stored correlation results."""
        return self._results

    def get_latest_results(self) -> list[CorrelationResult]:
        """Alias for get_all_results."""
        return self.get_all_results()

    def get_alerts(self, limit: int = 50) -> list[CorrelationAlert]:
        """Get the most recent correlation alerts."""
        alerts = sorted(self._alerts, key=lambda a: a.triggered_at, reverse=True)
        return alerts[:limit]

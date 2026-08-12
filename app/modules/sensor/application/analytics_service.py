"""
sensor/application/analytics_service.py — Sensor Analytics Service.

Provides: moving averages (SMA/EMA), peak detection, trend analysis
via manual linear regression, uptime statistics, failure probability
estimation, and full analytical reports.

All calculations are numpy-free using pure Python math.
"""
from __future__ import annotations
import math
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorHealthState
from app.modules.sensor.domain.analytics_models import (
    MovingAverage, PeakRecord, TrendAnalysis, TrendDirection,
    SensorUptimeStats, FailureProbability, SensorAnalyticsReport,
)
from app.modules.sensor.application.telemetry_buffer import TelemetryBuffer
from app.modules.sensor.application.health_tracker import SensorHealthTracker

log = get_logger("sensor.analytics_service")


class SensorAnalyticsService:
    """Service to compute analytics metrics for sensor data."""

    def __init__(
        self,
        buffer: Optional[TelemetryBuffer] = None,
        health_tracker: Optional[SensorHealthTracker] = None,
    ) -> None:
        self.buffer = buffer or TelemetryBuffer()
        self.health_tracker = health_tracker or SensorHealthTracker()

    def _get_values(self, sensor_id: str, default_count: int = 50) -> list[float]:
        if self.buffer:
            return self.buffer.get_values(sensor_id, count=default_count)
        return []

    def calculate_moving_averages(self, sensor_id: str, values: list[float], window: int = 20) -> MovingAverage:
        """Calculate Simple and Exponential Moving Averages for a list of values."""
        if not values:
            return MovingAverage(
                sensor_id=sensor_id, window_size=window, sma=0.0, ema=0.0,
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        n = min(len(values), window)
        recent_vals = values[-n:]
        
        # SMA
        sma = sum(recent_vals) / n

        # EMA
        alpha = 2 / (n + 1)
        ema = recent_vals[0]
        for val in recent_vals[1:]:
            ema = alpha * val + (1 - alpha) * ema

        return MovingAverage(
            sensor_id=sensor_id,
            window_size=n,
            sma=sma,
            ema=ema,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    async def calculate_moving_average(self, sensor_id: str, window: int = 20) -> MovingAverage:
        """Async convenience method fetching values from telemetry buffer."""
        values = self._get_values(sensor_id, default_count=window * 2)
        return self.calculate_moving_averages(sensor_id, values, window=window)

    def detect_peaks(self, sensor_id: str, values: list[float]) -> PeakRecord:
        """Find peak and trough values in a list of readings."""
        if not values:
            now = datetime.now(timezone.utc).isoformat()
            return PeakRecord(
                sensor_id=sensor_id, peak_value=0.0, trough_value=0.0,
                peak_timestamp=now, trough_timestamp=now, range=0.0
            )

        peak_val = max(values)
        trough_val = min(values)
        now = datetime.now(timezone.utc).isoformat()

        return PeakRecord(
            sensor_id=sensor_id,
            peak_value=peak_val,
            trough_value=trough_val,
            peak_timestamp=now,
            trough_timestamp=now,
            range=peak_val - trough_val
        )

    async def find_peaks(self, sensor_id: str) -> PeakRecord:
        """Async convenience method fetching values from telemetry buffer."""
        values = self._get_values(sensor_id)
        return self.detect_peaks(sensor_id, values)

    def analyze_trend(self, sensor_id: str, values: Optional[list[float]] = None) -> TrendAnalysis:
        """Perform linear regression to find trend and project next value."""
        if values is None:
            values = self._get_values(sensor_id)

        n = len(values)
        if n < 2:
            return TrendAnalysis(
                sensor_id=sensor_id, direction=TrendDirection.UNKNOWN, slope=0.0,
                r_squared=0.0, window_readings=n, forecast_next_value=0.0,
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        x = list(range(n))
        y = values
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        denominator = (n * sum_x2 - sum_x ** 2)
        if denominator == 0:
            slope = 0.0
            intercept = sum_y / n if n > 0 else 0.0
            r_squared = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n
            
            # R-squared
            y_mean = sum_y / n
            ss_tot = sum((yi - y_mean) ** 2 for yi in y)
            ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

        if abs(slope) < 0.01:
            direction = TrendDirection.STABLE
        elif slope > 0.05:
            direction = TrendDirection.RISING
        elif slope < -0.05:
            direction = TrendDirection.FALLING
        else:
            direction = TrendDirection.VOLATILE

        forecast = intercept + slope * n

        return TrendAnalysis(
            sensor_id=sensor_id,
            direction=direction,
            slope=slope,
            r_squared=r_squared,
            window_readings=n,
            forecast_next_value=forecast,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def calculate_uptime(
        self,
        sensor_id: str,
        health_state: Optional[SensorHealthState] = None,
        readings: Optional[list[float]] = None
    ) -> SensorUptimeStats:
        """Calculate uptime statistics and descriptive stats for readings."""
        if readings is None:
            readings = self._get_values(sensor_id)
        if health_state is None:
            health_state = self.health_tracker.get_health(sensor_id) or SensorHealthState(sensor_id=sensor_id)

        if not readings:
            return SensorUptimeStats(
                sensor_id=sensor_id, uptime_pct=health_state.uptime_pct, total_readings=health_state.total_readings,
                anomalous_readings=health_state.total_anomalies, anomaly_rate_pct=0.0, mean_value=0.0,
                std_value=0.0, min_value=0.0, max_value=0.0, p95_value=0.0, p99_value=0.0
            )

        n = len(readings)
        mean_val = sum(readings) / n
        std_val = math.sqrt(sum((x - mean_val) ** 2 for x in readings) / n) if n > 1 else 0.0
        
        sorted_reads = sorted(readings)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)
        p95_val = sorted_reads[min(p95_idx, n - 1)]
        p99_val = sorted_reads[min(p99_idx, n - 1)]

        anomalies = getattr(health_state, 'total_anomalies', 0)
        anomaly_rate = (anomalies / max(health_state.total_readings or n, 1)) * 100.0

        return SensorUptimeStats(
            sensor_id=sensor_id,
            uptime_pct=health_state.uptime_pct,
            total_readings=n,
            anomalous_readings=anomalies,
            anomaly_rate_pct=round(anomaly_rate, 2),
            mean_value=round(mean_val, 4),
            std_value=round(std_val, 4),
            min_value=sorted_reads[0],
            max_value=sorted_reads[-1],
            p95_value=p95_val,
            p99_value=p99_val
        )

    def estimate_failure_probability(
        self,
        sensor_id: str,
        health_state: Optional[SensorHealthState] = None,
        trend: Optional[TrendAnalysis] = None,
        anomaly_rate: Optional[float] = None
    ) -> FailureProbability:
        """Estimate the probability of failure based on current state and trends."""
        if health_state is None:
            health_state = self.health_tracker.get_health(sensor_id) or SensorHealthState(sensor_id=sensor_id)
        if trend is None:
            trend = self.analyze_trend(sensor_id)
        if anomaly_rate is None:
            uptime_stats = self.calculate_uptime(sensor_id, health_state=health_state)
            anomaly_rate = uptime_stats.anomaly_rate_pct

        factors = []
        base_prob = (anomaly_rate / 100.0) * 0.5
        factors.append(f"Base anomaly probability: {base_prob:.2f}")

        trend_factor = 0.0
        if trend.direction == TrendDirection.RISING and trend.slope > 1.0:
            trend_factor = 0.2
            factors.append("Steep rising trend increases risk")
        elif trend.direction == TrendDirection.VOLATILE:
            trend_factor = 0.1
            factors.append("Volatile trend increases risk")
            
        health_factor = 0.0
        h_status = getattr(health_state, 'status', None)
        if h_status:
            h_status_str = h_status.value if hasattr(h_status, 'value') else str(h_status)
            if h_status_str == "CRITICAL":
                health_factor = 0.3
                factors.append("Critical health state")
            elif h_status_str == "WARNING":
                health_factor = 0.2
                factors.append("Warning health state")
            elif h_status_str == "DEGRADED":
                health_factor = 0.1
                factors.append("Degraded health state")

        prob = min(max(base_prob + trend_factor + health_factor, 0.0), 1.0)
        
        rul = None
        if prob > 0.8:
            rul = 2.0
        elif prob > 0.6:
            rul = 24.0
        elif prob > 0.4:
            rul = 168.0

        return FailureProbability(
            sensor_id=sensor_id,
            probability=round(prob, 4),
            confidence=0.8,
            contributing_factors=factors,
            estimated_rul_hours=rul,
            maintenance_due=prob > 0.6,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    async def predict_failure(self, sensor_id: str) -> FailureProbability:
        """Async convenience wrapper for predict failure endpoint."""
        return self.estimate_failure_probability(sensor_id)

    def generate_report(
        self,
        sensor_id: str,
        readings: Optional[list[float]] = None,
        health_state: Optional[SensorHealthState] = None,
        period_hours: int = 24
    ) -> SensorAnalyticsReport:
        """Generate a complete analytical report for a sensor."""
        if readings is None:
            readings = self._get_values(sensor_id)
        if health_state is None:
            health_state = self.health_tracker.get_health(sensor_id) or SensorHealthState(sensor_id=sensor_id)

        moving_avg = self.calculate_moving_averages(sensor_id, readings)
        peaks = self.detect_peaks(sensor_id, readings)
        trend = self.analyze_trend(sensor_id, readings)
        uptime = self.calculate_uptime(sensor_id, health_state, readings)
        failure_prob = self.estimate_failure_probability(sensor_id, health_state, trend, uptime.anomaly_rate_pct)

        summary = f"Sensor {sensor_id}: {trend.direction.value} trend, {uptime.anomaly_rate_pct:.1f}% anomaly rate, failure probability {failure_prob.probability:.1%}"

        return SensorAnalyticsReport(
            sensor_id=sensor_id,
            period_hours=period_hours,
            moving_averages=moving_avg,
            peak=peaks,
            trend=trend,
            uptime=uptime,
            failure_probability=failure_prob,
            summary=summary
        )

    async def generate_fleet_summary(self) -> dict[str, Any]:
        """Generate summary metrics across all buffered sensors."""
        sensor_ids = self.buffer.get_all_sensor_ids() if self.buffer else []
        total_sensors = len(sensor_ids)
        fleet_health = self.health_tracker.get_fleet_summary() if self.health_tracker else {}
        
        return {
            "total_sensors": total_sensors,
            "fleet_health": fleet_health,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

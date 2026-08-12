"""
sensor/application/health_tracker.py — Per-Sensor Health State Machine.

Manages the finite state machine for each sensor's operational health.
Tracks consecutive anomalies and healthy readings to enforce hysteresis
and prevent alert flapping.

State Transitions:
  HEALTHY → DEGRADED (3+ consecutive anomalies)
  DEGRADED → WARNING (5+ consecutive anomalies)
  WARNING → CRITICAL (8+ consecutive anomalies)
  CRITICAL → HEALTHY (10+ consecutive clean readings)
  Any state → OFFLINE (>5 minutes without a reading)
  Any state → CALIBRATING (manual override)

Welford's online algorithm is used for rolling mean/std computation
without storing the full history window.
"""
from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Optional

from app.core.logging import get_logger
from app.modules.sensor.domain.models import (
    SensorAnomaly,
    SensorHealth,
    SensorHealthState,
    SensorReading,
)

log = get_logger("sensor.health_tracker")


class SensorHealthTracker:
    """
    Per-sensor health state machine with hysteresis.

    Thread-safe for use in async FastAPI route handlers via module-level
    singleton pattern (one tracker per process).
    """

    # ── Hysteresis thresholds ─────────────────────────────────────────────────
    DEGRADED_THRESHOLD: int = 3   # consecutive anomalies → DEGRADED
    WARNING_THRESHOLD: int = 5    # consecutive anomalies → WARNING
    CRITICAL_THRESHOLD: int = 8   # consecutive anomalies → CRITICAL
    RECOVERY_THRESHOLD: int = 10  # consecutive healthy  → HEALTHY
    OFFLINE_TIMEOUT_SEC: float = 300.0  # 5 min no data → OFFLINE

    def __init__(self) -> None:
        # Per-sensor state storage
        self._states: dict[str, SensorHealthState] = {}
        # Welford accumulators
        self._rolling_count: dict[str, int] = {}
        self._rolling_mean: dict[str, float] = {}
        self._rolling_m2: dict[str, float] = {}
        # Timing
        self._last_reading_epoch: dict[str, float] = {}

    def _get_or_create(self, sensor_id: str) -> SensorHealthState:
        """Return existing state or create a new HEALTHY one."""
        if sensor_id not in self._states:
            self._states[sensor_id] = SensorHealthState(sensor_id=sensor_id)
            self._rolling_count[sensor_id] = 0
            self._rolling_mean[sensor_id] = 0.0
            self._rolling_m2[sensor_id] = 0.0
        return self._states[sensor_id]

    def _welford_update(self, sensor_id: str, value: float) -> tuple[float, float]:
        """Update Welford accumulators, return (mean, std_dev)."""
        n = self._rolling_count[sensor_id] + 1
        delta = value - self._rolling_mean[sensor_id]
        mean = self._rolling_mean[sensor_id] + delta / n
        delta2 = value - mean
        m2 = self._rolling_m2[sensor_id] + delta * delta2

        self._rolling_count[sensor_id] = n
        self._rolling_mean[sensor_id] = mean
        self._rolling_m2[sensor_id] = m2

        std_dev = math.sqrt(m2 / n) if n > 1 else 0.0
        return mean, std_dev

    def update(
        self,
        sensor_id: str,
        reading: SensorReading,
        anomalies: list[SensorAnomaly],
    ) -> tuple[SensorHealthState, Optional[SensorHealth]]:
        """
        Process a reading and update the sensor's health state machine.

        Args:
            sensor_id:  Sensor to update.
            reading:    The incoming reading (for Welford stats update).
            anomalies:  Detected anomalies on this reading (empty = healthy).

        Returns:
            Tuple of:
              - new SensorHealthState
              - previous SensorHealth status IF it changed, else None
        """
        now_epoch = time.time()
        self._last_reading_epoch[sensor_id] = now_epoch

        state = self._get_or_create(sensor_id)
        previous_status: Optional[SensorHealth] = None
        old_status = state.status

        # Welford update
        mean, std_dev = self._welford_update(sensor_id, reading.value)

        # Update counters
        has_anomaly = bool(anomalies)
        consecutive_anomalies = (state.consecutive_anomalies + 1) if has_anomaly else 0
        consecutive_healthy = (state.consecutive_healthy + 1) if not has_anomaly else 0
        total_readings = state.total_readings + 1
        total_anomalies = state.total_anomalies + (1 if has_anomaly else 0)
        uptime_pct = ((total_readings - total_anomalies) / total_readings) * 100.0
        last_healthy = (
            datetime.now(timezone.utc).isoformat()
            if not has_anomaly
            else state.last_healthy_reading
        )

        # ── State transition logic ──────────────────────────────────────────
        new_status = old_status

        if consecutive_anomalies >= self.CRITICAL_THRESHOLD:
            new_status = SensorHealth.CRITICAL
        elif consecutive_anomalies >= self.WARNING_THRESHOLD:
            if old_status != SensorHealth.CRITICAL:
                new_status = SensorHealth.WARNING
        elif consecutive_anomalies >= self.DEGRADED_THRESHOLD:
            if old_status not in (SensorHealth.CRITICAL, SensorHealth.WARNING):
                new_status = SensorHealth.DEGRADED

        # Recovery path: enough clean readings
        if consecutive_healthy >= self.RECOVERY_THRESHOLD:
            new_status = SensorHealth.HEALTHY

        # Build new immutable state
        new_state = SensorHealthState(
            sensor_id=sensor_id,
            status=new_status,
            consecutive_anomalies=consecutive_anomalies,
            consecutive_healthy=consecutive_healthy,
            last_healthy_reading=last_healthy,
            last_reading_timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_pct=round(uptime_pct, 2),
            total_readings=total_readings,
            total_anomalies=total_anomalies,
            mean_reading=round(mean, 4),
            std_reading=round(std_dev, 4),
        )
        self._states[sensor_id] = new_state

        # Return previous status only if changed (triggers event emission)
        if new_status != old_status:
            previous_status = old_status
            log.info(
                f"Sensor {sensor_id} health transitioned: "
                f"{old_status.value} → {new_status.value} "
                f"(consecutive_anomalies={consecutive_anomalies}, "
                f"consecutive_healthy={consecutive_healthy})"
            )

        return new_state, previous_status

    def get_health(self, sensor_id: str) -> SensorHealthState | None:
        """
        Get current health state, checking for OFFLINE timeout.

        Returns None if sensor has never been seen.
        """
        state = self._states.get(sensor_id)
        if state is None:
            return None

        # Check OFFLINE timeout
        last_epoch = self._last_reading_epoch.get(sensor_id, 0.0)
        if last_epoch > 0 and (time.time() - last_epoch) > self.OFFLINE_TIMEOUT_SEC:
            offline_state = SensorHealthState(
                sensor_id=sensor_id,
                status=SensorHealth.OFFLINE,
                consecutive_anomalies=state.consecutive_anomalies,
                consecutive_healthy=0,
                last_healthy_reading=state.last_healthy_reading,
                last_reading_timestamp=state.last_reading_timestamp,
                uptime_pct=state.uptime_pct,
                total_readings=state.total_readings,
                total_anomalies=state.total_anomalies,
                mean_reading=state.mean_reading,
                std_reading=state.std_reading,
            )
            self._states[sensor_id] = offline_state
            return offline_state

        return state

    def get_all_states(self) -> list[SensorHealthState]:
        """Return current health state for all tracked sensors."""
        return [self.get_health(sid) for sid in list(self._states.keys()) if self.get_health(sid)]

    def get_fleet_summary(self) -> dict[str, int]:
        """Return per-status sensor counts across the fleet."""
        summary: dict[str, int] = {status.value: 0 for status in SensorHealth}
        for sensor_id in list(self._states.keys()):
            state = self.get_health(sensor_id)
            if state:
                summary[state.status.value] = summary.get(state.status.value, 0) + 1
        return summary

    def get_at_risk_sensors(self) -> list[SensorHealthState]:
        """Return sensors in WARNING, CRITICAL, or OFFLINE state."""
        at_risk_statuses = {SensorHealth.WARNING, SensorHealth.CRITICAL, SensorHealth.OFFLINE}
        return [
            state for state in self.get_all_states()
            if state.status in at_risk_statuses
        ]

    def mark_offline(self, sensor_id: str) -> SensorHealthState:
        """Manually force a sensor to OFFLINE state."""
        state = self._get_or_create(sensor_id)
        new_state = SensorHealthState(
            sensor_id=sensor_id,
            status=SensorHealth.OFFLINE,
            consecutive_anomalies=state.consecutive_anomalies,
            consecutive_healthy=0,
            last_healthy_reading=state.last_healthy_reading,
            last_reading_timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_pct=state.uptime_pct,
            total_readings=state.total_readings,
            total_anomalies=state.total_anomalies,
            mean_reading=state.mean_reading,
            std_reading=state.std_reading,
        )
        self._states[sensor_id] = new_state
        log.info(f"Sensor {sensor_id} manually marked OFFLINE")
        return new_state

    def mark_calibrating(self, sensor_id: str) -> SensorHealthState:
        """Manually force a sensor to CALIBRATING state."""
        state = self._get_or_create(sensor_id)
        new_state = SensorHealthState(
            sensor_id=sensor_id,
            status=SensorHealth.CALIBRATING,
            consecutive_anomalies=0,
            consecutive_healthy=0,
            last_healthy_reading=state.last_healthy_reading,
            last_reading_timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_pct=state.uptime_pct,
            total_readings=state.total_readings,
            total_anomalies=state.total_anomalies,
            mean_reading=state.mean_reading,
            std_reading=state.std_reading,
        )
        self._states[sensor_id] = new_state
        log.info(f"Sensor {sensor_id} manually marked CALIBRATING")
        return new_state

    def mark_recovered(self, sensor_id: str) -> SensorHealthState:
        """Manually force a sensor back to HEALTHY state."""
        state = self._get_or_create(sensor_id)
        new_state = SensorHealthState(
            sensor_id=sensor_id,
            status=SensorHealth.HEALTHY,
            consecutive_anomalies=0,
            consecutive_healthy=self.RECOVERY_THRESHOLD,
            last_healthy_reading=datetime.now(timezone.utc).isoformat(),
            last_reading_timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_pct=state.uptime_pct,
            total_readings=state.total_readings,
            total_anomalies=state.total_anomalies,
            mean_reading=state.mean_reading,
            std_reading=state.std_reading,
        )
        self._states[sensor_id] = new_state
        log.info(f"Sensor {sensor_id} manually marked HEALTHY (recovered)")
        return new_state

"""metrics.py — Notification Agent Operational Metrics.

Tracks:
  - Notifications sent / failed / deduplicated / rate-limited
  - Delivery success rate per channel
  - Acknowledgement latency
  - Escalation count
  - Provider latency (simulated)
  - Retry count
  - Duplicate suppression rate
"""

from collections import defaultdict
from typing import Any

from app.core.logging import get_logger

log = get_logger("agents.notification.metrics")


class NotificationMetrics:
    """
    Real-time operational metrics for the Notification Agent.

    In production, these counters would be emitted as Prometheus metrics
    and visualized in Grafana dashboards.
    """

    def __init__(self) -> None:
        self._sent: int = 0
        self._failed: int = 0
        self._deduplicated: int = 0
        self._rate_limited: int = 0
        self._escalations: int = 0
        self._retries: int = 0
        self._acknowledged: int = 0

        # Per-channel success and failure counts
        self._channel_success: dict[str, int] = defaultdict(int)
        self._channel_failures: dict[str, int] = defaultdict(int)

        # Per-event-type counts
        self._event_type_counts: dict[str, int] = defaultdict(int)

        # Acknowledgement latencies in seconds
        self._ack_latencies: list[float] = []

    def record_sent(self, channel: str, event_type: str) -> None:
        self._sent += 1
        self._channel_success[channel] += 1
        self._event_type_counts[event_type] += 1

    def record_failed(self, channel: str) -> None:
        self._failed += 1
        self._channel_failures[channel] += 1

    def record_deduplicated(self) -> None:
        self._deduplicated += 1

    def record_rate_limited(self) -> None:
        self._rate_limited += 1

    def record_escalation(self) -> None:
        self._escalations += 1

    def record_retry(self) -> None:
        self._retries += 1

    def record_acknowledgement(self, latency_seconds: float) -> None:
        self._acknowledged += 1
        self._ack_latencies.append(latency_seconds)

    def delivery_success_rate(self) -> float:
        """Overall delivery success rate (0.0–1.0)."""
        total = self._sent + self._failed
        if total == 0:
            return 1.0
        return round(self._sent / total, 4)

    def channel_success_rate(self, channel: str) -> float:
        """Per-channel success rate."""
        success = self._channel_success.get(channel, 0)
        failure = self._channel_failures.get(channel, 0)
        total = success + failure
        if total == 0:
            return 1.0
        return round(success / total, 4)

    def avg_ack_latency_seconds(self) -> float:
        """Average acknowledgement latency in seconds."""
        if not self._ack_latencies:
            return 0.0
        return round(sum(self._ack_latencies) / len(self._ack_latencies), 2)

    def duplicate_suppression_rate(self) -> float:
        """Ratio of deduplicated events to total attempted sends."""
        total = self._sent + self._deduplicated
        if total == 0:
            return 0.0
        return round(self._deduplicated / total, 4)

    def snapshot(self) -> dict[str, Any]:
        """Return a full metrics snapshot dict."""
        return {
            "notifications_sent": self._sent,
            "notifications_failed": self._failed,
            "notifications_deduplicated": self._deduplicated,
            "notifications_rate_limited": self._rate_limited,
            "escalations": self._escalations,
            "retries": self._retries,
            "acknowledgements": self._acknowledged,
            "delivery_success_rate": self.delivery_success_rate(),
            "avg_ack_latency_seconds": self.avg_ack_latency_seconds(),
            "duplicate_suppression_rate": self.duplicate_suppression_rate(),
            "channel_success": dict(self._channel_success),
            "channel_failures": dict(self._channel_failures),
            "event_type_counts": dict(self._event_type_counts),
        }

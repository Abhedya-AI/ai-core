"""rate_limiter.py — Per-Recipient Rate Limiter.

Prevents notification spam by enforcing per-recipient per-channel
message rate limits within a sliding time window.

Emergency severity alerts bypass rate limiting.

Configuration:
  max_per_window: Maximum messages per recipient per window.
  window_seconds: Duration of the sliding window.
"""

import time
from collections import defaultdict

from app.core.logging import get_logger
from app.modules.agents.notification.models import NotificationChannel, NotificationSeverity

log = get_logger("agents.notification.rate_limiter")

# Default rate limit: 5 notifications per minute per recipient per channel
_DEFAULT_MAX = 5
_DEFAULT_WINDOW_SECONDS = 60

# Severity levels that bypass rate limiting entirely
_BYPASS_SEVERITIES = {NotificationSeverity.EMERGENCY, NotificationSeverity.CRITICAL}


class RateLimiter:
    """
    Per-recipient, per-channel sliding window rate limiter.

    Emergency and Critical severity alerts always bypass rate limiting.
    """

    def __init__(
        self,
        max_per_window: int = _DEFAULT_MAX,
        window_seconds: int = _DEFAULT_WINDOW_SECONDS,
    ) -> None:
        self._max = max_per_window
        self._window = window_seconds
        # (recipient_id, channel) → list of send timestamps
        self._buckets: dict[tuple[str, str], list[float]] = defaultdict(list)

    def is_allowed(
        self,
        recipient_id: str,
        channel: NotificationChannel,
        severity: NotificationSeverity,
    ) -> bool:
        """
        Check whether sending a notification is permitted under current rate limits.

        Args:
            recipient_id: Target recipient ID.
            channel: Target channel.
            severity: Notification severity (EMERGENCY/CRITICAL bypass limits).

        Returns:
            True if allowed, False if rate-limited.
        """
        # Emergency and Critical bypass rate limiting
        if severity in _BYPASS_SEVERITIES:
            log.debug(f"RateLimiter: bypass for severity={severity.value}, recipient={recipient_id}")
            return True

        key = (recipient_id, channel.value)
        now = time.monotonic()

        # Purge expired timestamps
        bucket = [ts for ts in self._buckets[key] if (now - ts) <= self._window]
        self._buckets[key] = bucket

        if len(bucket) >= self._max:
            log.warning(
                f"RateLimiter: BLOCKED recipient={recipient_id} channel={channel.value} "
                f"({len(bucket)}/{self._max} in {self._window}s window)"
            )
            return False

        bucket.append(now)
        return True

    def record_send(
        self,
        recipient_id: str,
        channel: NotificationChannel,
    ) -> None:
        """Record a successful send for rate tracking (used after allowed check)."""
        key = (recipient_id, channel.value)
        self._buckets[key].append(time.monotonic())

    def current_count(self, recipient_id: str, channel: NotificationChannel) -> int:
        """Return the current message count within the active window."""
        key = (recipient_id, channel.value)
        now = time.monotonic()
        return sum(1 for ts in self._buckets[key] if (now - ts) <= self._window)

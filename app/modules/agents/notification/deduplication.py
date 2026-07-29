"""deduplication.py — Alert Storm Prevention via Deduplication.

Prevents notification storms by suppressing duplicate events of the same type
within a configurable time window, instead updating the event count.

Example:
  SmokeDetected × 5 in 60s → 1 notification with count=5 (not 5 separate alerts)
"""

import time
from collections import defaultdict

from app.core.logging import get_logger

log = get_logger("agents.notification.deduplication")


class DeduplicationEngine:
    """
    Deduplicates notifications within a sliding time window.

    Each deduplication group is keyed by (event_type, zone_id).
    Within the window, subsequent events are suppressed and counted.
    """

    def __init__(self, window_seconds: int = 60) -> None:
        self._window_seconds = window_seconds
        # group_key → (first_seen_ts, count, notification_id)
        self._groups: dict[str, tuple[float, int, str]] = defaultdict(
            lambda: (0.0, 0, "")
        )

    def build_group_key(self, event_type: str, zone_id: str | None) -> str:
        """Build a deduplication group key from event type and zone."""
        return f"{event_type}::{zone_id or 'global'}"

    def is_duplicate(self, event_type: str, zone_id: str | None = None) -> tuple[bool, int]:
        """
        Check if an event is a duplicate within the active window.

        Args:
            event_type: Domain event type.
            zone_id: Optional zone identifier.

        Returns:
            Tuple of (is_duplicate: bool, current_count: int).
        """
        key = self.build_group_key(event_type, zone_id)
        now = time.monotonic()
        first_seen, count, _ = self._groups[key]

        if count > 0 and (now - first_seen) <= self._window_seconds:
            # Within window — increment and suppress
            self._groups[key] = (first_seen, count + 1, _)
            log.debug(
                f"Dedup suppressed: event_type={event_type}, zone={zone_id}, "
                f"count={count + 1}, window={self._window_seconds}s"
            )
            return True, count + 1

        # Outside window or first occurrence — reset
        self._groups[key] = (now, 1, "")
        return False, 1

    def get_suppressed_count(self, event_type: str, zone_id: str | None = None) -> int:
        """Return the current suppression count for a group."""
        key = self.build_group_key(event_type, zone_id)
        _, count, _ = self._groups[key]
        return count

    def clear_group(self, event_type: str, zone_id: str | None = None) -> None:
        """Explicitly clear a deduplication group (e.g., after incident resolution)."""
        key = self.build_group_key(event_type, zone_id)
        if key in self._groups:
            del self._groups[key]
            log.debug(f"Dedup group cleared: {key}")

"""acknowledgement.py — Acknowledgement Manager.

Critical alerts require operator confirmation (ACK).
If no acknowledgement is received within the configured timeout,
escalation is triggered.
"""

import time
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.agents.notification.models import AcknowledgementRecord, NotificationChannel

log = get_logger("agents.notification.acknowledgement")


class AcknowledgementManager:
    """
    Tracks acknowledgement state for notifications that require confirmation.

    Pending notifications are tracked by notification_id with their deadline timestamp.
    When an operator acknowledges, escalation is halted.
    """

    def __init__(self, ack_timeout_seconds: int = 300) -> None:
        """
        Args:
            ack_timeout_seconds: Time in seconds before escalation is triggered.
                                 Default: 300s (5 minutes).
        """
        self._timeout = ack_timeout_seconds
        # notification_id → deadline_monotonic_ts
        self._pending: dict[str, float] = {}
        # notification_id → AcknowledgementRecord
        self._acknowledged: dict[str, AcknowledgementRecord] = {}

    def register_pending(self, notification_id: str) -> None:
        """Register a notification as pending acknowledgement."""
        deadline = time.monotonic() + self._timeout
        self._pending[notification_id] = deadline
        log.debug(
            f"AcknowledgementManager: registered {notification_id}, "
            f"timeout={self._timeout}s"
        )

    def acknowledge(
        self,
        notification_id: str,
        acknowledged_by: str,
        channel: NotificationChannel = NotificationChannel.DASHBOARD,
        notes: str = "",
    ) -> AcknowledgementRecord:
        """
        Record an operator acknowledgement.

        Args:
            notification_id: Notification being acknowledged.
            acknowledged_by: User ID or name of the acknowledging operator.
            channel: Channel through which the ACK was received.
            notes: Optional operator notes.

        Returns:
            AcknowledgementRecord with timestamp.
        """
        record = AcknowledgementRecord(
            notification_id=notification_id,
            acknowledged_by=acknowledged_by,
            acknowledged_at=datetime.now(timezone.utc).isoformat(),
            channel=channel,
            notes=notes,
        )
        self._acknowledged[notification_id] = record
        self._pending.pop(notification_id, None)

        log.info(
            f"AcknowledgementManager: {notification_id} acknowledged by "
            f"'{acknowledged_by}' via {channel.value}"
        )
        return record

    def is_acknowledged(self, notification_id: str) -> bool:
        """Return True if the notification has been acknowledged."""
        return notification_id in self._acknowledged

    def is_overdue(self, notification_id: str) -> bool:
        """
        Return True if the acknowledgement deadline has passed.

        Only applies to pending notifications; returns False if already acknowledged.
        """
        if notification_id in self._acknowledged:
            return False
        deadline = self._pending.get(notification_id)
        if deadline is None:
            return False
        return time.monotonic() > deadline

    def get_overdue_notifications(self) -> list[str]:
        """Return all notification IDs whose acknowledgement deadline has passed."""
        now = time.monotonic()
        overdue = [
            nid for nid, deadline in self._pending.items()
            if now > deadline and nid not in self._acknowledged
        ]
        return overdue

    def get_pending_count(self) -> int:
        """Return the number of notifications still awaiting acknowledgement."""
        return len(self._pending)

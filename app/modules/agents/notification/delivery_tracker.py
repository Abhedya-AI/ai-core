"""delivery_tracker.py — End-to-End Delivery Status Tracker.

Tracks notification lifecycle from QUEUED → SENT → DELIVERED → ACKNOWLEDGED → RESOLVED.
Each notification and its per-channel delivery records are stored and queryable.
"""

from datetime import datetime, timezone

from app.core.logging import get_logger
from app.modules.agents.notification.models import (
    DeliveryRecord,
    DeliveryStatus,
    Notification,
    NotificationStatus,
)

log = get_logger("agents.notification.delivery_tracker")


class DeliveryTracker:
    """
    Maintains in-memory delivery state for all active notifications.

    In production, this would persist records to a time-series database or
    append-only event store (e.g., PostgreSQL + partitioned delivery_log table).
    """

    def __init__(self) -> None:
        # notification_id → Notification
        self._notifications: dict[str, Notification] = {}
        # notification_id → list[DeliveryRecord]
        self._deliveries: dict[str, list[DeliveryRecord]] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, notification: Notification) -> None:
        """Register a new notification for tracking."""
        self._notifications[notification.notification_id] = notification
        self._deliveries[notification.notification_id] = []
        log.debug(f"DeliveryTracker: registered notification {notification.notification_id}")

    # ------------------------------------------------------------------
    # Status Updates
    # ------------------------------------------------------------------

    def record_delivery(self, delivery: DeliveryRecord) -> None:
        """Append a delivery record and update parent notification status."""
        nid = delivery.notification_id
        if nid not in self._deliveries:
            self._deliveries[nid] = []
        self._deliveries[nid].append(delivery)

        # Update parent notification delivery_records list
        notification = self._notifications.get(nid)
        if notification:
            notification.delivery_records.append(delivery)

            # Advance status to SENT if at least one delivery succeeded
            if delivery.status == DeliveryStatus.SUCCESS:
                if notification.status == NotificationStatus.QUEUED:
                    notification.status = NotificationStatus.SENT
                elif notification.status == NotificationStatus.DISPATCHED:
                    notification.status = NotificationStatus.DELIVERED

        log.debug(
            f"DeliveryTracker: recorded {delivery.status.value} for "
            f"notification={nid}, channel={delivery.provider.value}"
        )

    def mark_acknowledged(self, notification_id: str, acknowledged_by: str) -> bool:
        """
        Mark a notification as acknowledged.

        Returns:
            True if found and updated, False otherwise.
        """
        notification = self._notifications.get(notification_id)
        if not notification:
            log.warning(f"DeliveryTracker: unknown notification_id={notification_id} for acknowledgement")
            return False

        notification.status = NotificationStatus.ACKNOWLEDGED
        notification.resolved_at = datetime.now(timezone.utc).isoformat()
        log.info(f"DeliveryTracker: notification {notification_id} ACKNOWLEDGED by {acknowledged_by}")
        return True

    def mark_resolved(self, notification_id: str) -> bool:
        """Mark a notification fully resolved."""
        notification = self._notifications.get(notification_id)
        if not notification:
            return False
        notification.status = NotificationStatus.RESOLVED
        notification.resolved_at = datetime.now(timezone.utc).isoformat()
        log.info(f"DeliveryTracker: notification {notification_id} RESOLVED")
        return True

    def mark_failed(self, notification_id: str, reason: str) -> None:
        """Mark a notification as failed."""
        notification = self._notifications.get(notification_id)
        if notification:
            notification.status = NotificationStatus.FAILED
            log.warning(f"DeliveryTracker: notification {notification_id} FAILED: {reason}")

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_notification(self, notification_id: str) -> Notification | None:
        """Retrieve a tracked notification by ID."""
        return self._notifications.get(notification_id)

    def get_deliveries(self, notification_id: str) -> list[DeliveryRecord]:
        """Retrieve all delivery records for a notification."""
        return self._deliveries.get(notification_id, [])

    def all_notifications(self) -> list[Notification]:
        """Return all tracked notifications."""
        return list(self._notifications.values())

    def pending_acknowledgements(self) -> list[Notification]:
        """Return notifications that require acknowledgement and haven't received it."""
        return [
            n for n in self._notifications.values()
            if n.requires_acknowledgement
            and n.status not in (
                NotificationStatus.ACKNOWLEDGED,
                NotificationStatus.RESOLVED,
                NotificationStatus.FAILED,
            )
        ]

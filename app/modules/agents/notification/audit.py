"""audit.py — Notification Audit Trail.

Records every notification event for compliance and post-incident review.

Stored fields:
  - recipient, channel, message content
  - template version used
  - delivery time, acknowledgement time
  - retry count, escalation history
  - event source, trace ID
"""

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.agents.notification.models import (
    AcknowledgementRecord,
    DeliveryRecord,
    EscalationRecord,
    Notification,
)

log = get_logger("agents.notification.audit")


class AuditEntry:
    """A single audit trail entry."""

    __slots__ = (
        "entry_id",
        "notification_id",
        "event_type",
        "action",
        "actor",
        "channel",
        "recipient_id",
        "detail",
        "timestamp",
        "trace_id",
        "metadata",
    )

    def __init__(
        self,
        notification_id: str,
        event_type: str,
        action: str,
        actor: str = "SYSTEM",
        channel: str = "",
        recipient_id: str = "",
        detail: str = "",
        trace_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        import uuid
        self.entry_id = str(uuid.uuid4())
        self.notification_id = notification_id
        self.event_type = event_type
        self.action = action
        self.actor = actor
        self.channel = channel
        self.recipient_id = recipient_id
        self.detail = detail
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.trace_id = trace_id
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "notification_id": self.notification_id,
            "event_type": self.event_type,
            "action": self.action,
            "actor": self.actor,
            "channel": self.channel,
            "recipient_id": self.recipient_id,
            "detail": self.detail,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
        }


class AuditTrail:
    """
    Maintains an append-only in-memory audit log for all notification lifecycle events.

    Production implementation would persist entries to:
      - PostgreSQL audit_log table (append-only, immutable)
      - Or a dedicated audit service (e.g., BigQuery, S3 parquet)
    """

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def log_queued(self, notification: Notification, trace_id: str = "") -> None:
        """Log that a notification was queued."""
        self._append(AuditEntry(
            notification_id=notification.notification_id,
            event_type=notification.event_type,
            action="QUEUED",
            detail=f"severity={notification.severity.value}, "
                   f"recipients={len(notification.recipients)}, "
                   f"channels={[c.value for c in notification.channels]}",
            trace_id=trace_id,
        ))

    def log_delivery(self, delivery: DeliveryRecord, event_type: str = "", trace_id: str = "") -> None:
        """Log a delivery attempt outcome."""
        self._append(AuditEntry(
            notification_id=delivery.notification_id,
            event_type=event_type,
            action=f"DELIVERY_{delivery.status.value}",
            channel=delivery.provider.value,
            recipient_id=delivery.recipient_id,
            detail=f"provider_msg_id={delivery.provider_message_id}, "
                   f"error={delivery.error_message or 'none'}",
            trace_id=trace_id,
        ))

    def log_acknowledgement(self, ack: AcknowledgementRecord, event_type: str = "", trace_id: str = "") -> None:
        """Log an operator acknowledgement."""
        self._append(AuditEntry(
            notification_id=ack.notification_id,
            event_type=event_type,
            action="ACKNOWLEDGED",
            actor=ack.acknowledged_by,
            channel=ack.channel.value,
            detail=f"notes={ack.notes or 'none'}",
            trace_id=trace_id,
        ))

    def log_escalation(self, escalation: EscalationRecord, event_type: str = "", trace_id: str = "") -> None:
        """Log a notification escalation step."""
        self._append(AuditEntry(
            notification_id=escalation.notification_id,
            event_type=event_type,
            action=f"ESCALATED_LEVEL_{escalation.level}",
            recipient_id=escalation.escalated_to,
            detail=f"reason={escalation.reason}",
            trace_id=trace_id,
        ))

    def log_deduplicated(self, notification_id: str, event_type: str, count: int, trace_id: str = "") -> None:
        """Log a suppressed duplicate notification."""
        self._append(AuditEntry(
            notification_id=notification_id,
            event_type=event_type,
            action="DEDUPLICATED",
            detail=f"suppressed_count={count}",
            trace_id=trace_id,
        ))

    def log_rate_limited(self, notification_id: str, event_type: str, recipient_id: str, channel: str, trace_id: str = "") -> None:
        """Log a rate-limited notification."""
        self._append(AuditEntry(
            notification_id=notification_id,
            event_type=event_type,
            action="RATE_LIMITED",
            recipient_id=recipient_id,
            channel=channel,
            trace_id=trace_id,
        ))

    def get_entries(self, notification_id: str | None = None) -> list[dict]:
        """Retrieve audit entries, optionally filtered by notification ID."""
        if notification_id:
            return [e.to_dict() for e in self._entries if e.notification_id == notification_id]
        return [e.to_dict() for e in self._entries]

    def total_entries(self) -> int:
        """Return total number of audit log entries."""
        return len(self._entries)

    def _append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)
        log.debug(f"AuditTrail: [{entry.action}] notification={entry.notification_id}")

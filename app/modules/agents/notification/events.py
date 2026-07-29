"""events.py — Notification Domain Event Generator.

Publishes back to the EventBus:
  - NotificationQueued
  - NotificationSent
  - NotificationDelivered
  - NotificationFailed
  - NotificationAcknowledged
  - NotificationEscalated
  - NotificationResolved
"""

from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.notification.models import (
    DeliveryRecord,
    DeliveryStatus,
    EscalationRecord,
    Notification,
)


class NotificationEventGenerator:
    """Generates standardized domain events for the Notification Agent's lifecycle."""

    @staticmethod
    def notification_queued(
        agent_name: str,
        notification: Notification,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="NotificationQueued",
            agent_name=agent_name,
            payload={
                "notification_id": notification.notification_id,
                "event_type": notification.event_type,
                "severity": notification.severity.value,
                "recipient_count": len(notification.recipients),
                "channels": [c.value for c in notification.channels],
            },
            trace_id=trace_id,
        )

    @staticmethod
    def notification_sent(
        agent_name: str,
        notification: Notification,
        delivery: DeliveryRecord,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="NotificationSent",
            agent_name=agent_name,
            payload={
                "notification_id": notification.notification_id,
                "delivery_id": delivery.delivery_id,
                "channel": delivery.provider.value,
                "recipient_id": delivery.recipient_id,
                "provider_message_id": delivery.provider_message_id,
            },
            trace_id=trace_id,
        )

    @staticmethod
    def notification_failed(
        agent_name: str,
        notification: Notification,
        delivery: DeliveryRecord,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="NotificationFailed",
            agent_name=agent_name,
            payload={
                "notification_id": notification.notification_id,
                "delivery_id": delivery.delivery_id,
                "channel": delivery.provider.value,
                "recipient_id": delivery.recipient_id,
                "error": delivery.error_message,
            },
            trace_id=trace_id,
        )

    @staticmethod
    def notification_acknowledged(
        agent_name: str,
        notification_id: str,
        acknowledged_by: str,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="NotificationAcknowledged",
            agent_name=agent_name,
            payload={
                "notification_id": notification_id,
                "acknowledged_by": acknowledged_by,
            },
            trace_id=trace_id,
        )

    @staticmethod
    def notification_escalated(
        agent_name: str,
        escalation: EscalationRecord,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="NotificationEscalated",
            agent_name=agent_name,
            payload={
                "notification_id": escalation.notification_id,
                "level": escalation.level,
                "escalated_to": escalation.escalated_to,
                "reason": escalation.reason,
            },
            trace_id=trace_id,
        )

    @staticmethod
    def notification_resolved(
        agent_name: str,
        notification_id: str,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="NotificationResolved",
            agent_name=agent_name,
            payload={"notification_id": notification_id},
            trace_id=trace_id,
        )

    @staticmethod
    def notification_deduplicated(
        agent_name: str,
        event_type: str,
        count: int,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="NotificationDeduplicated",
            agent_name=agent_name,
            payload={"original_event_type": event_type, "suppressed_count": count},
            trace_id=trace_id,
        )

    @staticmethod
    def build_all_delivery_events(
        agent_name: str,
        notification: Notification,
        delivery_records: list[DeliveryRecord],
        trace_id: str,
    ) -> list[AgentDomainEvent]:
        """Build sent/failed events for all delivery records."""
        events: list[AgentDomainEvent] = [
            NotificationEventGenerator.notification_queued(agent_name, notification, trace_id)
        ]
        for record in delivery_records:
            if record.status == DeliveryStatus.SUCCESS:
                events.append(
                    NotificationEventGenerator.notification_sent(agent_name, notification, record, trace_id)
                )
            else:
                events.append(
                    NotificationEventGenerator.notification_failed(agent_name, notification, record, trace_id)
                )
        return events

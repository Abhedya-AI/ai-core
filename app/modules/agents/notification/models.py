"""models.py — Notification Agent Domain Models & DTOs."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.modules.agents.core.agent_result import AgentResult


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class NotificationSeverity(str, Enum):
    """Severity levels that drive channel selection and escalation policy."""

    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class NotificationChannel(str, Enum):
    """Supported outbound communication channels."""

    EMAIL = "EMAIL"
    SMS = "SMS"
    VOICE = "VOICE"
    WHATSAPP = "WHATSAPP"
    SLACK = "SLACK"
    TEAMS = "TEAMS"
    PUSH = "PUSH"
    WEBSOCKET = "WEBSOCKET"
    PAGERDUTY = "PAGERDUTY"
    WEBHOOK = "WEBHOOK"
    DASHBOARD = "DASHBOARD"


class NotificationStatus(str, Enum):
    """Full lifecycle tracking statuses for a single notification."""

    QUEUED = "QUEUED"
    DISPATCHED = "DISPATCHED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    DEDUPLICATED = "DEDUPLICATED"
    RATE_LIMITED = "RATE_LIMITED"


class DeliveryStatus(str, Enum):
    """Per-channel delivery outcome."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class RecipientProfile(BaseModel):
    """Resolved recipient with delivery preferences."""

    recipient_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(...)
    name: str = Field(default="Unknown")
    role: str = Field(default="OPERATOR")
    department: str = Field(default="OPERATIONS")
    zone_id: str | None = Field(default=None)
    shift: str = Field(default="DAY")
    preferred_channels: list[NotificationChannel] = Field(
        default_factory=lambda: [NotificationChannel.EMAIL, NotificationChannel.PUSH]
    )
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    push_token: str | None = Field(default=None)
    locale: str = Field(default="en")
    timezone: str = Field(default="UTC")
    on_call: bool = Field(default=False)


class RenderedMessage(BaseModel):
    """A fully rendered message ready for dispatch."""

    subject: str = Field(default="")
    body_text: str = Field(...)
    body_html: str = Field(default="")
    body_markdown: str = Field(default="")
    rich_card: dict[str, Any] = Field(default_factory=dict)
    channel: NotificationChannel = Field(...)
    locale: str = Field(default="en")
    template_id: str = Field(default="")
    template_version: str = Field(default="1.0")


class DeliveryRecord(BaseModel):
    """Tracks a single delivery attempt to a provider."""

    delivery_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    notification_id: str = Field(...)
    recipient_id: str = Field(...)
    provider: NotificationChannel = Field(...)
    status: DeliveryStatus = Field(default=DeliveryStatus.PENDING)
    sent_at: str | None = Field(default=None)
    delivered_at: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    retry_count: int = Field(default=0)
    provider_message_id: str | None = Field(default=None)


class AcknowledgementRecord(BaseModel):
    """Records an acknowledgement event for a critical alert."""

    notification_id: str = Field(...)
    acknowledged_by: str = Field(...)
    acknowledged_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    channel: NotificationChannel = Field(default=NotificationChannel.DASHBOARD)
    notes: str = Field(default="")


class EscalationRecord(BaseModel):
    """Tracks a single escalation step."""

    escalation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    notification_id: str = Field(...)
    level: int = Field(default=1)
    escalated_to: str = Field(...)
    triggered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    reason: str = Field(default="NO_ACKNOWLEDGEMENT")


class Notification(BaseModel):
    """Central notification object tracked through its full lifecycle."""

    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str = Field(...)
    event_type: str = Field(...)
    severity: NotificationSeverity = Field(default=NotificationSeverity.MEDIUM)
    status: NotificationStatus = Field(default=NotificationStatus.QUEUED)
    recipients: list[RecipientProfile] = Field(default_factory=list)
    channels: list[NotificationChannel] = Field(default_factory=list)
    rendered_messages: list[RenderedMessage] = Field(default_factory=list)
    delivery_records: list[DeliveryRecord] = Field(default_factory=list)
    acknowledgements: list[AcknowledgementRecord] = Field(default_factory=list)
    escalation_records: list[EscalationRecord] = Field(default_factory=list)
    requires_acknowledgement: bool = Field(default=False)
    deduplicated: bool = Field(default=False)
    dedup_group_key: str | None = Field(default=None)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_at: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationAgentResult(AgentResult):
    """Domain-extended result returned by the Notification Intelligence Agent."""

    notifications_queued: int = Field(default=0)
    notifications_sent: int = Field(default=0)
    notifications_deduplicated: int = Field(default=0)
    notifications_failed: int = Field(default=0)
    notifications: list[Notification] = Field(default_factory=list)
    delivery_records: list[DeliveryRecord] = Field(default_factory=list)
    escalation_records: list[EscalationRecord] = Field(default_factory=list)

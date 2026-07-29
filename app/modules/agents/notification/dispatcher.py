"""dispatcher.py — Channel Dispatcher and NotificationProvider ABC.

Provides:
  - NotificationProvider: Abstract base all channel implementations must satisfy.
  - DeliveryResult: Outcome of a single send attempt.
  - ChannelDispatcher: Routes RenderedMessage objects to the correct provider.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.agents.notification.models import DeliveryRecord, DeliveryStatus, NotificationChannel, RecipientProfile, RenderedMessage

log = get_logger("agents.notification.dispatcher")


# ---------------------------------------------------------------------------
# Delivery Result DTO
# ---------------------------------------------------------------------------

class DeliveryResult:
    """Result from a single provider send attempt."""

    def __init__(
        self,
        success: bool,
        provider_message_id: str | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.success = success
        self.provider_message_id = provider_message_id or str(uuid.uuid4())
        self.error_message = error_message
        self.metadata = metadata or {}


# ---------------------------------------------------------------------------
# Abstract Provider Interface
# ---------------------------------------------------------------------------

class NotificationProvider(ABC):
    """
    Abstract base class for all outbound notification providers.

    Every provider implements a single send() method.
    The orchestrator never knows which provider is used.
    """

    channel: NotificationChannel

    @abstractmethod
    async def send(
        self,
        message: RenderedMessage,
        recipient: RecipientProfile,
        notification_id: str,
    ) -> DeliveryResult:
        """
        Send a rendered notification to a single recipient.

        Args:
            message: Fully rendered message for this channel.
            recipient: Target recipient profile.
            notification_id: Parent notification ID for tracking.

        Returns:
            DeliveryResult indicating success or failure.
        """


# ---------------------------------------------------------------------------
# Simulated Provider Implementations
# ---------------------------------------------------------------------------

class EmailProvider(NotificationProvider):
    """SMTP Email Provider (simulated for test environment)."""

    channel = NotificationChannel.EMAIL

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        log.info(f"[EMAIL] → {recipient.email} | Subject: '{message.subject}'")
        return DeliveryResult(
            success=True,
            provider_message_id=f"email_{notification_id[:8]}",
        )


class SMSProvider(NotificationProvider):
    """Twilio SMS Provider (simulated)."""

    channel = NotificationChannel.SMS

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        phone = recipient.phone or "UNKNOWN"
        log.info(f"[SMS] → {phone} | '{message.body_text[:60]}...'")
        return DeliveryResult(
            success=True,
            provider_message_id=f"sms_{notification_id[:8]}",
        )


class VoiceProvider(NotificationProvider):
    """Twilio Voice Call Provider (simulated)."""

    channel = NotificationChannel.VOICE

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        phone = recipient.phone or "UNKNOWN"
        log.info(f"[VOICE] → {phone} | script: '{message.body_text[:60]}...'")
        return DeliveryResult(
            success=True,
            provider_message_id=f"voice_{notification_id[:8]}",
        )


class WhatsAppProvider(NotificationProvider):
    """WhatsApp Business API Provider (simulated)."""

    channel = NotificationChannel.WHATSAPP

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        phone = recipient.phone or "UNKNOWN"
        log.info(f"[WHATSAPP] → {phone} | '{message.body_text[:60]}...'")
        return DeliveryResult(
            success=True,
            provider_message_id=f"wa_{notification_id[:8]}",
        )


class SlackProvider(NotificationProvider):
    """Slack Webhook Provider (simulated)."""

    channel = NotificationChannel.SLACK

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        log.info(f"[SLACK] → {recipient.name} | '{message.subject}'")
        return DeliveryResult(
            success=True,
            provider_message_id=f"slack_{notification_id[:8]}",
        )


class TeamsProvider(NotificationProvider):
    """Microsoft Teams Webhook Provider (simulated)."""

    channel = NotificationChannel.TEAMS

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        log.info(f"[TEAMS] → {recipient.name} | '{message.subject}'")
        return DeliveryResult(
            success=True,
            provider_message_id=f"teams_{notification_id[:8]}",
        )


class PushProvider(NotificationProvider):
    """Firebase Cloud Messaging Push Provider (simulated)."""

    channel = NotificationChannel.PUSH

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        token = recipient.push_token or "UNKNOWN"
        log.info(f"[PUSH] → {token} | '{message.subject}'")
        return DeliveryResult(
            success=True,
            provider_message_id=f"push_{notification_id[:8]}",
        )


class WebSocketProvider(NotificationProvider):
    """WebSocket real-time push provider (simulated)."""

    channel = NotificationChannel.WEBSOCKET

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        log.info(f"[WEBSOCKET] → {recipient.user_id} | '{message.subject}'")
        return DeliveryResult(
            success=True,
            provider_message_id=f"ws_{notification_id[:8]}",
        )


class PagerDutyProvider(NotificationProvider):
    """PagerDuty Incident API Provider (simulated)."""

    channel = NotificationChannel.PAGERDUTY

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        log.info(f"[PAGERDUTY] → {recipient.name} | '{message.subject}'")
        return DeliveryResult(
            success=True,
            provider_message_id=f"pd_{notification_id[:8]}",
        )


class WebhookProvider(NotificationProvider):
    """Generic HTTP Webhook Provider (simulated)."""

    channel = NotificationChannel.WEBHOOK

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        log.info(f"[WEBHOOK] → {recipient.user_id} | event payload dispatched")
        return DeliveryResult(
            success=True,
            provider_message_id=f"hook_{notification_id[:8]}",
        )


class DashboardProvider(NotificationProvider):
    """In-app dashboard notification provider (simulated)."""

    channel = NotificationChannel.DASHBOARD

    async def send(self, message: RenderedMessage, recipient: RecipientProfile, notification_id: str) -> DeliveryResult:
        log.info(f"[DASHBOARD] → {recipient.user_id} | '{message.subject}'")
        return DeliveryResult(
            success=True,
            provider_message_id=f"dash_{notification_id[:8]}",
        )


# ---------------------------------------------------------------------------
# Channel Dispatcher
# ---------------------------------------------------------------------------

_PROVIDER_REGISTRY: dict[NotificationChannel, NotificationProvider] = {
    NotificationChannel.EMAIL: EmailProvider(),
    NotificationChannel.SMS: SMSProvider(),
    NotificationChannel.VOICE: VoiceProvider(),
    NotificationChannel.WHATSAPP: WhatsAppProvider(),
    NotificationChannel.SLACK: SlackProvider(),
    NotificationChannel.TEAMS: TeamsProvider(),
    NotificationChannel.PUSH: PushProvider(),
    NotificationChannel.WEBSOCKET: WebSocketProvider(),
    NotificationChannel.PAGERDUTY: PagerDutyProvider(),
    NotificationChannel.WEBHOOK: WebhookProvider(),
    NotificationChannel.DASHBOARD: DashboardProvider(),
}


class ChannelDispatcher:
    """
    Routes RenderedMessage objects to the correct NotificationProvider.

    Adding a new channel requires only registering a new provider in _PROVIDER_REGISTRY.
    """

    async def dispatch(
        self,
        message: RenderedMessage,
        recipient: RecipientProfile,
        notification_id: str,
    ) -> DeliveryRecord:
        """
        Dispatch a rendered message via the appropriate provider.

        Args:
            message: Rendered message for the target channel.
            recipient: Target recipient.
            notification_id: Parent notification ID.

        Returns:
            DeliveryRecord tracking the outcome.
        """
        provider = _PROVIDER_REGISTRY.get(message.channel)
        now = datetime.now(timezone.utc).isoformat()

        if not provider:
            log.warning(f"No provider registered for channel: {message.channel}")
            return DeliveryRecord(
                notification_id=notification_id,
                recipient_id=recipient.recipient_id,
                provider=message.channel,
                status=DeliveryStatus.FAILED,
                sent_at=now,
                error_message=f"No provider for channel: {message.channel}",
            )

        try:
            result = await provider.send(message, recipient, notification_id)
            status = DeliveryStatus.SUCCESS if result.success else DeliveryStatus.FAILED
            return DeliveryRecord(
                notification_id=notification_id,
                recipient_id=recipient.recipient_id,
                provider=message.channel,
                status=status,
                sent_at=now,
                delivered_at=now if result.success else None,
                error_message=result.error_message,
                provider_message_id=result.provider_message_id,
            )
        except Exception as exc:  # noqa: BLE001
            log.error(f"Provider {message.channel} raised exception: {exc}")
            return DeliveryRecord(
                notification_id=notification_id,
                recipient_id=recipient.recipient_id,
                provider=message.channel,
                status=DeliveryStatus.FAILED,
                sent_at=now,
                error_message=str(exc),
            )

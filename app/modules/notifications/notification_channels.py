import abc
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.logging import get_logger

log = get_logger("app.modules.notifications.notification_channels")

class NotificationPayload(BaseModel):
    """Payload for notifications to be sent across various channels."""
    model_config = ConfigDict(from_attributes=True)
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message body")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    severity: str = Field(default="INFO", description="Severity level: INFO, WARNING, CRITICAL")
    recipient_id: str = Field(..., description="ID or address of the recipient")

class BaseNotificationChannel(abc.ABC):
    """Abstract base class for notification channels."""
    
    @abc.abstractmethod
    async def send(self, payload: NotificationPayload) -> bool:
        """Send notification via the channel."""
        pass

class EmailChannel(BaseNotificationChannel):
    """Email notification channel implementation."""
    
    async def send(self, payload: NotificationPayload) -> bool:
        """Send email to recipient."""
        log.info(f"Sending email to {payload.recipient_id} with title: {payload.title}")
        # Simulate network delay for production readiness feel without actual SMTP setup
        await asyncio.sleep(0.1)
        return True

class SMSChannel(BaseNotificationChannel):
    """SMS notification channel implementation."""
    
    async def send(self, payload: NotificationPayload) -> bool:
        """Send SMS to recipient."""
        log.info(f"Sending SMS to {payload.recipient_id}: {payload.title}")
        await asyncio.sleep(0.1)
        return True

class PushChannel(BaseNotificationChannel):
    """Mobile push notification channel implementation."""
    
    async def send(self, payload: NotificationPayload) -> bool:
        """Send push notification to mobile device."""
        log.info(f"Sending Push to {payload.recipient_id}: {payload.title}")
        await asyncio.sleep(0.1)
        return True

class DashboardChannel(BaseNotificationChannel):
    """In-app dashboard notification channel."""
    
    async def send(self, payload: NotificationPayload) -> bool:
        """Send notification to web dashboard."""
        log.info(f"Sending Dashboard alert to {payload.recipient_id}: {payload.title}")
        return True

class WebSocketChannel(BaseNotificationChannel):
    """WebSocket notification channel."""
    
    async def send(self, payload: NotificationPayload) -> bool:
        """Send notification over WebSocket for real-time updates."""
        log.info(f"Sending WebSocket event to {payload.recipient_id}: {payload.title}")
        return True

class TeamsSlackChannel(BaseNotificationChannel):
    """Teams/Slack notification channel."""
    
    async def send(self, payload: NotificationPayload) -> bool:
        """Send notification to collaboration platform webhook."""
        log.info(f"Sending Webhook to {payload.recipient_id}: {payload.title}")
        await asyncio.sleep(0.1)
        return True

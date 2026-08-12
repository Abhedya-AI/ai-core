import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

from app.core.logging import get_logger
from app.modules.notifications.notification_channels import (
    NotificationPayload, 
    BaseNotificationChannel,
    EmailChannel,
    SMSChannel,
    PushChannel,
    DashboardChannel,
    WebSocketChannel,
    TeamsSlackChannel
)
from app.modules.notifications.escalation_matrix import EscalationMatrixManager

log = get_logger("app.modules.notifications.notification_service")

class NotificationService:
    """Core notification service handling deduplication, rate limiting, and escalations."""
    
    def __init__(self):
        """Initialize NotificationService with default channels and escalation manager."""
        self.channels: Dict[str, BaseNotificationChannel] = {
            "email": EmailChannel(),
            "sms": SMSChannel(),
            "push": PushChannel(),
            "dashboard": DashboardChannel(),
            "websocket": WebSocketChannel(),
            "teams": TeamsSlackChannel(),
        }
        self.escalation_manager = EscalationMatrixManager(self.channels)
        self.sent_notifications_cache: Dict[str, datetime] = {}
        self.dedup_window = timedelta(minutes=5)
        
    def _generate_dedup_hash(self, payload: NotificationPayload) -> str:
        """Generate a deterministic hash for deduplication based on content and recipient."""
        content = f"{payload.recipient_id}:{payload.title}:{payload.severity}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def _is_rate_limited(self, dedup_hash: str) -> bool:
        """Check if the notification should be suppressed due to rate limiting/deduplication."""
        now = datetime.utcnow()
        if dedup_hash in self.sent_notifications_cache:
            last_sent = self.sent_notifications_cache[dedup_hash]
            if now - last_sent < self.dedup_window:
                return True
        self.sent_notifications_cache[dedup_hash] = now
        # Perform basic cleanup
        self._cleanup_cache(now)
        return False
        
    def _cleanup_cache(self, now: datetime):
        """Remove old entries from dedup cache to prevent memory leaks."""
        keys_to_remove = []
        for k, v in self.sent_notifications_cache.items():
            if now - v > self.dedup_window * 2:
                keys_to_remove.append(k)
        for k in keys_to_remove:
            del self.sent_notifications_cache[k]

    async def send_notification(self, channel_name: str, payload: NotificationPayload) -> bool:
        """Send a standard notification if not rate limited or deduplicated."""
        if channel_name not in self.channels:
            log.error(f"Unsupported notification channel: {channel_name}")
            return False
            
        dedup_hash = self._generate_dedup_hash(payload)
        if await self._is_rate_limited(dedup_hash):
            log.debug(f"Notification deduplicated/rate-limited for {payload.recipient_id}: {payload.title}")
            return False
            
        channel = self.channels[channel_name]
        return await channel.send(payload)
        
    async def trigger_escalation(self, incident_id: str, policy_id: str, title: str, message: str) -> bool:
        """Delegate incident escalation to the escalation manager."""
        return await self.escalation_manager.trigger_escalation(incident_id, policy_id, title, message)
        
    async def acknowledge_incident(self, incident_id: str, user_id: str) -> bool:
        """Acknowledge an active incident, halting further escalation."""
        return await self.escalation_manager.acknowledge_incident(incident_id, user_id)

"""notification_service.py — Service managing worker notifications and push alerts."""

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.knowledge.domain.entities.notification import Notification
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("knowledge.services.notification")


class NotificationService:
    """Domain service managing safety notifications, alerts, and worker delivery statuses."""

    def __init__(self, repository: BaseNeo4jRepository | None = None) -> None:
        self._repo = repository or BaseNeo4jRepository()
        self._event_bus = EventBus.get()

    async def send_notification(self, notification: Notification) -> dict[str, Any]:
        """Send a notification alert to a worker."""
        props = notification.to_graph_properties()
        res = await self._repo.create_node(
            type("CreateNodeRequest", (), {"label": "Notification", "node_id": notification.id, "properties": props})()
        )
        log.info(f"Notification sent to Worker {notification.recipient_worker_id} via [{notification.channel}]")

        await self._event_bus.publish(
            topic=Topics.WORKER_STATUS_UPDATED,
            payload={
                "notification_id": notification.id,
                "recipient_worker_id": notification.recipient_worker_id,
                "priority": notification.priority,
            },
            key=notification.recipient_worker_id,
        )
        return res

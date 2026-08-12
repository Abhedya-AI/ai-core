"""event_provider.py — Event Provider Wrapper."""

from app.core.logging import get_logger
from app.infrastructure.kafka.producer import EventBus
from app.infrastructure.kafka.registry import Topics
from app.modules.agents.core.events import AgentDomainEvent

log = get_logger("agents.supervisor.event_provider")


class EventProvider:
    """Wraps EventBus publication for Supervisor Agent."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus or EventBus.get()

    async def publish_events(self, events: list[AgentDomainEvent], key: str = "") -> None:
        """Publish domain events to EventBus."""
        for event in events:
            try:
                await self._event_bus.publish(
                    topic=Topics.WORKER_STATUS_UPDATED,
                    payload=event.model_dump(),
                    key=key or event.trace_id,
                )
                log.debug(f"EventProvider: published '{event.event_type}' to EventBus")
            except Exception as exc:  # noqa: BLE001
                log.error(f"EventProvider: failed to publish '{event.event_type}': {exc}")

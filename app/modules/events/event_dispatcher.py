"""
Event dispatcher for asynchronously dispatching events.
"""
import asyncio
from typing import List, Callable, Awaitable
from app.modules.events.event_validator import EventEnvelope
from app.modules.events.retry_manager import EventRetryManager
from app.modules.events.dead_letter_queue import DeadLetterQueue
from app.core.logging import get_logger

log = get_logger("app.modules.events.event_dispatcher")

class EventDispatcher:
    """Asynchronous event dispatcher."""

    def __init__(self, retry_manager: EventRetryManager, dlq: DeadLetterQueue) -> None:
        """
        Initialize the event dispatcher.
        
        Args:
            retry_manager: Manager for retrying failed dispatches.
            dlq: Dead letter queue for events that exhaust retries.
        """
        self.retry_manager = retry_manager
        self.dlq = dlq
        self._handlers: List[Callable[[EventEnvelope], Awaitable[None]]] = []

    def register_handler(self, handler: Callable[[EventEnvelope], Awaitable[None]]) -> None:
        """
        Register a global handler for all events dispatched through this dispatcher.
        
        Args:
            handler: Async function that takes an EventEnvelope.
        """
        self._handlers.append(handler)

    async def dispatch(self, event: EventEnvelope) -> None:
        """
        Dispatch an event to all registered handlers concurrently.
        
        Args:
            event: The event to dispatch.
        """
        if not self._handlers:
            log.debug(f"No handlers registered in dispatcher for event {event.event_id}")
            return
            
        tasks = []
        for handler in self._handlers:
            tasks.append(self._dispatch_to_handler(handler, event))
            
        await asyncio.gather(*tasks)

    async def _dispatch_to_handler(
        self, 
        handler: Callable[[EventEnvelope], Awaitable[None]], 
        event: EventEnvelope
    ) -> None:
        """
        Dispatch an event to a single handler with retries and DLQ fallback.
        
        Args:
            handler: The target handler.
            event: The event to dispatch.
        """
        try:
            await self.retry_manager.execute_with_retry(handler, event.event_id, event)
            log.debug(f"Successfully dispatched event {event.event_id} to handler {handler.__name__}")
        except Exception as e:
            log.error(f"Failed to dispatch event {event.event_id} to {handler.__name__} after retries. Moving to DLQ.")
            dlq_id = f"{event.event_id}-{handler.__name__}"
            await self.dlq.push(
                event_data=event.model_dump(),
                error_message=str(e),
                item_id=dlq_id
            )

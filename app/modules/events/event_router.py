"""
Event router routing events to subscribers based on topics and metadata.
"""
from typing import Dict, List, Callable, Awaitable, Optional, Set, Tuple
from app.modules.events.event_validator import EventEnvelope
from app.core.logging import get_logger

log = get_logger("app.modules.events.event_router")

class EventRouter:
    """Routes events to specific subscribers based on routing rules."""

    def __init__(self) -> None:
        """Initialize the event router."""
        # Map of (event_type, zone_id) -> list of handlers
        self._routes: Dict[Tuple[str, Optional[str]], List[Callable[[EventEnvelope], Awaitable[None]]]] = {}

    def subscribe(
        self, 
        event_type: str, 
        handler: Callable[[EventEnvelope], Awaitable[None]], 
        zone_id: Optional[str] = None
    ) -> None:
        """
        Subscribe a handler to a specific event type, optionally filtered by zone.
        
        Args:
            event_type: The type of event to subscribe to.
            handler: The async callback function.
            zone_id: Optional zone filter. If None, receives all events of event_type.
        """
        key = (event_type, zone_id)
        if key not in self._routes:
            self._routes[key] = []
        
        self._routes[key].append(handler)
        log.info(f"Subscribed handler to event_type: {event_type}, zone_id: {zone_id}")

    async def route(self, event: EventEnvelope) -> None:
        """
        Route an event to all matching subscribers.
        
        Args:
            event: The event to route.
        """
        handlers_to_invoke: Set[Callable[[EventEnvelope], Awaitable[None]]] = set()
        
        # Check global subscriptions for this event type
        global_key = (event.event_type, None)
        if global_key in self._routes:
            handlers_to_invoke.update(self._routes[global_key])
            
        # Check zone-specific subscriptions
        if event.zone_id:
            zone_key = (event.event_type, event.zone_id)
            if zone_key in self._routes:
                handlers_to_invoke.update(self._routes[zone_key])
                
        if not handlers_to_invoke:
            log.debug(f"No routes found for event {event.event_id} (type: {event.event_type})")
            return
            
        log.debug(f"Routing event {event.event_id} to {len(handlers_to_invoke)} handlers")
        
        for handler in handlers_to_invoke:
            try:
                await handler(event)
            except Exception as e:
                log.error(f"Error executing handler {handler.__name__} for event {event.event_id}: {str(e)}")

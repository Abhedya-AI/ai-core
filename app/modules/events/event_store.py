"""
Event store for append-only event log persistence and querying.
"""
from typing import List, Optional
from datetime import datetime
from app.modules.events.event_validator import EventEnvelope
from app.core.logging import get_logger

log = get_logger("app.modules.events.event_store")

class EventStore:
    """Append-only store for events."""

    def __init__(self) -> None:
        """Initialize the event store."""
        # In a real implementation, this would connect to a database
        self._events: List[EventEnvelope] = []

    async def append(self, event: EventEnvelope) -> None:
        """
        Append an event to the store.
        
        Args:
            event: The validated event envelope.
        """
        self._events.append(event)
        log.debug(f"Appended event {event.event_id} to store.")

    async def get_events(
        self,
        event_type: Optional[str] = None,
        plant_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[EventEnvelope]:
        """
        Query events based on filters.
        
        Args:
            event_type: Filter by event type.
            plant_id: Filter by plant ID.
            zone_id: Filter by zone ID.
            start_time: Filter events after this time.
            end_time: Filter events before this time.
            limit: Maximum number of events to return.
            offset: Number of events to skip.
            
        Returns:
            A list of matching EventEnvelope instances.
        """
        filtered_events = self._events
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        if plant_id:
            filtered_events = [e for e in filtered_events if e.plant_id == plant_id]
        if zone_id:
            filtered_events = [e for e in filtered_events if e.zone_id == zone_id]
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]
            
        # Apply sorting by timestamp (ascending)
        filtered_events.sort(key=lambda e: e.timestamp)
        
        log.info(f"Queried event store, found {len(filtered_events)} matching events.")
        
        # Apply pagination
        return filtered_events[offset:offset + limit]

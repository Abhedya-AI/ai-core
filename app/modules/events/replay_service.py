"""
Event replay service for replaying historical event streams.
"""
from typing import Optional, Callable, Awaitable
from datetime import datetime
from app.modules.events.event_store import EventStore
from app.modules.events.event_validator import EventEnvelope
from app.core.logging import get_logger

log = get_logger("app.modules.events.replay_service")

class EventReplayService:
    """Service to replay events from the event store."""

    def __init__(self, event_store: EventStore) -> None:
        """
        Initialize the replay service.
        
        Args:
            event_store: The event store to read historical events from.
        """
        self.event_store = event_store

    async def replay_events(
        self,
        handler: Callable[[EventEnvelope], Awaitable[None]],
        event_type: Optional[str] = None,
        plant_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        batch_size: int = 100
    ) -> int:
        """
        Replay historical events matching the criteria to a handler.
        
        Args:
            handler: Async function to process each replayed event.
            event_type: Filter by event type.
            plant_id: Filter by plant ID.
            zone_id: Filter by zone ID.
            start_time: Start time for replay.
            end_time: End time for replay.
            batch_size: Number of events to fetch per batch.
            
        Returns:
            Total number of events replayed.
        """
        log.info(f"Starting event replay for type: {event_type}, plant: {plant_id}")
        offset = 0
        total_replayed = 0
        
        while True:
            events = await self.event_store.get_events(
                event_type=event_type,
                plant_id=plant_id,
                zone_id=zone_id,
                start_time=start_time,
                end_time=end_time,
                limit=batch_size,
                offset=offset
            )
            
            if not events:
                break
                
            for event in events:
                try:
                    await handler(event)
                    total_replayed += 1
                except Exception as e:
                    log.error(f"Failed to replay event {event.event_id}: {str(e)}")
                    # For a replay service, we log and continue.
                    
            offset += batch_size
            
        log.info(f"Completed event replay. Total events replayed: {total_replayed}")
        return total_replayed

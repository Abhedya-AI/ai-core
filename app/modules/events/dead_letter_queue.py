"""
Dead letter queue for handling failed or corrupted events.
"""
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.logging import get_logger

log = get_logger("app.modules.events.dead_letter_queue")

class DLQItem(BaseModel):
    """Represents an item in the dead letter queue."""
    id: str = Field(..., description="Unique ID for the DLQ entry")
    failed_at: datetime = Field(default_factory=datetime.utcnow, description="When the failure occurred")
    event_data: Dict[str, Any] = Field(..., description="The original event data that failed")
    error_message: str = Field(..., description="Description of the error")
    retry_count: int = Field(default=0, description="Number of times this event has been retried")

class DeadLetterQueue:
    """Manages failed events that could not be processed."""

    def __init__(self) -> None:
        """Initialize the dead letter queue."""
        self._queue: List[DLQItem] = []

    async def push(self, event_data: Dict[str, Any], error_message: str, item_id: str) -> None:
        """
        Push a failed event to the DLQ.
        
        Args:
            event_data: The raw event data.
            error_message: The error that caused processing to fail.
            item_id: A unique ID for this DLQ entry.
        """
        item = DLQItem(
            id=item_id,
            event_data=event_data,
            error_message=error_message
        )
        self._queue.append(item)
        log.warning(f"Event pushed to DLQ with ID: {item_id}. Error: {error_message}")

    async def get_items(self, limit: int = 50, offset: int = 0) -> List[DLQItem]:
        """
        Retrieve items from the DLQ.
        
        Args:
            limit: Max items to return.
            offset: Number of items to skip.
            
        Returns:
            List of DLQ items.
        """
        return self._queue[offset:offset + limit]

    async def remove(self, item_id: str) -> None:
        """
        Remove an item from the DLQ.
        
        Args:
            item_id: The ID of the DLQ item to remove.
        """
        initial_length = len(self._queue)
        self._queue = [item for item in self._queue if item.id != item_id]
        if len(self._queue) < initial_length:
            log.info(f"Removed item {item_id} from DLQ.")
        else:
            log.debug(f"Item {item_id} not found in DLQ.")

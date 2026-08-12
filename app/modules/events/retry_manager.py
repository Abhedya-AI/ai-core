"""
Event retry manager implementing exponential backoff policies.
"""
import asyncio
from typing import Callable, Any, Awaitable
from app.core.logging import get_logger

log = get_logger("app.modules.events.retry_manager")

class EventRetryManager:
    """Manages retrying failed event processing with exponential backoff."""

    def __init__(self, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 60.0) -> None:
        """
        Initialize the retry manager.
        
        Args:
            max_retries: Maximum number of retry attempts.
            base_delay: Base delay in seconds for exponential backoff.
            max_delay: Maximum delay in seconds between retries.
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def execute_with_retry(
        self, 
        operation: Callable[..., Awaitable[Any]], 
        event_id: str, 
        *args: Any, 
        **kwargs: Any
    ) -> Any:
        """
        Execute an async operation with exponential backoff retries.
        
        Args:
            operation: The async function to execute.
            event_id: The ID of the event being processed.
            args: Positional arguments for the operation.
            kwargs: Keyword arguments for the operation.
            
        Returns:
            The result of the operation.
            
        Raises:
            Exception: The last exception encountered if all retries fail.
        """
        retries = 0
        while True:
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                retries += 1
                if retries > self.max_retries:
                    log.error(f"Operation failed for event {event_id} after {self.max_retries} retries: {str(e)}")
                    raise
                
                # Calculate exponential backoff
                delay = min(self.base_delay * (2 ** (retries - 1)), self.max_delay)
                log.warning(f"Operation failed for event {event_id}. Retrying in {delay} seconds (Attempt {retries}/{self.max_retries}). Error: {str(e)}")
                await asyncio.sleep(delay)

"""
Event schema registry for defining and validating event schemas.
"""
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel
from app.core.logging import get_logger

log = get_logger("app.modules.events.schema_registry")

class EventSchemaRegistry:
    """Registry for managing event schemas."""

    def __init__(self) -> None:
        """Initialize the event schema registry."""
        self._schemas: Dict[str, Type[BaseModel]] = {}

    def register_schema(self, event_type: str, schema: Type[BaseModel]) -> None:
        """
        Register a schema for a specific event type.
        
        Args:
            event_type: The type of the event.
            schema: The Pydantic model representing the schema.
        """
        self._schemas[event_type] = schema
        log.info(f"Registered schema for event type: {event_type}")

    def get_schema(self, event_type: str) -> Optional[Type[BaseModel]]:
        """
        Get the schema for a given event type.
        
        Args:
            event_type: The type of the event.
            
        Returns:
            The Pydantic model schema if found, otherwise None.
        """
        return self._schemas.get(event_type)

    def validate_payload(self, event_type: str, payload: Dict[str, Any]) -> BaseModel:
        """
        Validate an event payload against its registered schema.
        
        Args:
            event_type: The type of the event.
            payload: The event payload dictionary.
            
        Returns:
            The validated Pydantic model instance.
            
        Raises:
            ValueError: If the schema is not registered or validation fails.
        """
        schema = self.get_schema(event_type)
        if not schema:
            raise ValueError(f"No schema registered for event type: {event_type}")
        
        try:
            return schema.model_validate(payload)
        except Exception as e:
            log.error(f"Failed to validate payload for event type {event_type}: {str(e)}")
            raise ValueError(f"Schema validation failed for {event_type}: {str(e)}") from e

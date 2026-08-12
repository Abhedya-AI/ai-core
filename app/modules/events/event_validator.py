"""
Event validator for validating event envelopes.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.core.logging import get_logger

log = get_logger("app.modules.events.event_validator")

class EventEnvelope(BaseModel):
    """Base envelope for all events in the system."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    event_id: str = Field(..., description="Unique identifier for the event")
    event_type: str = Field(..., description="Type of the event")
    timestamp: datetime = Field(..., description="Time the event occurred")
    source: str = Field(..., description="Source system or component of the event")
    plant_id: str = Field(..., description="Identifier for the plant")
    zone_id: Optional[str] = Field(None, description="Identifier for the zone within the plant")
    trace_id: Optional[str] = Field(None, description="Distributed tracing identifier")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")


class EventValidator:
    """Validator for event envelopes."""

    @classmethod
    def validate_envelope(cls, event_data: Dict[str, Any]) -> EventEnvelope:
        """
        Validate raw event data against the EventEnvelope schema.
        
        Args:
            event_data: Raw dictionary containing event data.
            
        Returns:
            Validated EventEnvelope instance.
            
        Raises:
            ValueError: If validation fails.
        """
        try:
            envelope = EventEnvelope.model_validate(event_data)
            log.debug(f"Successfully validated event envelope for event_id: {envelope.event_id}")
            return envelope
        except Exception as e:
            log.error(f"Failed to validate event envelope: {str(e)}")
            raise ValueError(f"Event envelope validation failed: {str(e)}") from e

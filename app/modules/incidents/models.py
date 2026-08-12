from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class IncidentState(str, Enum):
    DETECTED = "DETECTED"
    VALIDATED = "VALIDATED"
    INVESTIGATING = "INVESTIGATING"
    EMERGENCY_ACTIVE = "EMERGENCY_ACTIVE"
    MITIGATION = "MITIGATION"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"

class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class IncidentTimelineEvent(BaseModel):
    event_id: str = Field(description="Unique identifier for the timeline event")
    incident_id: str = Field(description="Associated incident ID")
    timestamp: datetime = Field(description="Time the event occurred")
    event_type: str = Field(description="Type of event (e.g., STATE_CHANGE, NOTE_ADDED)")
    description: str = Field(description="Human readable description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

class Incident(BaseModel):
    incident_id: str = Field(description="Unique incident ID")
    title: str = Field(description="Short title")
    description: str = Field(description="Detailed description")
    state: IncidentState = Field(default=IncidentState.DETECTED, description="Current state")
    severity: IncidentSeverity = Field(default=IncidentSeverity.LOW, description="Severity level")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation time")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update time")
    timeline: List[IncidentTimelineEvent] = Field(default_factory=list, description="Timeline events")

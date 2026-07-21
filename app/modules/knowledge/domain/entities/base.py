from datetime import datetime, timezone
from typing import Any
import uuid

from pydantic import BaseModel, Field


class GraphEntity(BaseModel):
    """
    Base model for all nodes in the Industrial Safety Knowledge Graph.

    Includes temporal validity (valid_from, valid_to) for historical reasoning
    ("What was the plant state 5 minutes before the incident?").
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str = Field(default="GraphEntity")
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_graph_properties(self) -> dict[str, Any]:
        """Convert fields into flat properties suitable for Neo4j node storage."""
        data = self.model_dump()
        # Convert datetimes to ISO format strings for Neo4j compatibility
        for key, val in data.items():
            if isinstance(val, datetime):
                data[key] = val.isoformat()
            elif isinstance(val, dict):
                import json
                data[key] = json.dumps(val)
        return data


class Person(GraphEntity):
    """Base class for human personnel (Worker, Contractor, Visitor)."""

    name: str
    email: str | None = None
    phone: str | None = None
    entity_type: str = Field(default="Person")


class AssetEntity(GraphEntity):
    """Base class for physical equipment and plant infrastructure."""

    name: str
    code: str
    entity_type: str = Field(default="Asset")


class LocationEntity(GraphEntity):
    """Base class for spatial entities (Zone, Building, Floor, Plant)."""

    name: str
    code: str
    entity_type: str = Field(default="Location")


class ObservationEntity(GraphEntity):
    """Base class for monitoring devices and cameras."""

    name: str
    entity_type: str = Field(default="Observation")


class EventEntity(GraphEntity):
    """Base class for plant events, hazards, permits, and incidents."""

    title: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    entity_type: str = Field(default="Event")

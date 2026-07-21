from pydantic import Field

from app.modules.knowledge.domain.entities.base import EventEntity


class EmergencyPlan(EventEntity):
    """Emergency response plan or active evacuation event."""

    emergency_type: str = "FIRE"   # FIRE, GAS_LEAK, EXPLOSION, STRUCTURAL
    zone_ids: list[str] = Field(default_factory=list)
    evacuation_route: list[str] = Field(default_factory=list)
    active: bool = True
    assigned_responder_ids: list[str] = Field(default_factory=list)
    entity_type: str = Field(default="EmergencyPlan")

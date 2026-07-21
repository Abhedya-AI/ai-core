"""
ontology.py — Industrial Safety Ontology Registry.

Acts as the central catalogue of all entities, relationships, enums,
and rules supported by ABHEDYA. Used by graph services, RAG, and multi-agent systems
to validate and inspect ontology elements dynamically.
"""

from typing import Any, Type

from app.modules.knowledge.domain.entities import (
    Asset,
    Building,
    Camera,
    Contractor,
    Document,
    DocumentChunk,
    EmergencyPlan,
    Equipment,
    Floor,
    GraphEntity,
    Hazard,
    Incident,
    Maintenance,
    Notification,
    Permit,
    Prediction,
    Regulation,
    Sensor,
    Visitor,
    Weather,
    Worker,
    Zone,
)
from app.modules.knowledge.domain.enums import (
    EquipmentStatus,
    HazardLevel,
    IncidentStatus,
    PermitStatus,
    SensorType,
    WorkerRole,
    ZoneType,
)
from app.modules.knowledge.domain.relationships import (
    RelationshipType,
    validate_relationship,
)

# ── Catalogue Registries ───────────────────────────────────────────────────────

ENTITY_TYPES: dict[str, Type[GraphEntity]] = {
    "Worker": Worker,
    "Contractor": Contractor,
    "Visitor": Visitor,
    "Asset": Asset,
    "Equipment": Equipment,
    "Zone": Zone,
    "Building": Building,
    "Floor": Floor,
    "Sensor": Sensor,
    "Camera": Camera,
    "Permit": Permit,
    "Maintenance": Maintenance,
    "Hazard": Hazard,
    "Incident": Incident,
    "EmergencyPlan": EmergencyPlan,
    "Document": Document,
    "DocumentChunk": DocumentChunk,
    "Regulation": Regulation,
    "Weather": Weather,
    "Prediction": Prediction,
    "Notification": Notification,
}

ENUM_REGISTRY: dict[str, Type[Any]] = {
    "HazardLevel": HazardLevel,
    "SensorType": SensorType,
    "IncidentStatus": IncidentStatus,
    "PermitStatus": PermitStatus,
    "EquipmentStatus": EquipmentStatus,
    "ZoneType": ZoneType,
    "WorkerRole": WorkerRole,
}

RELATIONSHIP_TYPES: list[str] = [rel.value for rel in RelationshipType]


# ── Registry Helper Functions ─────────────────────────────────────────────────

def get_entity_class(entity_name: str) -> Type[GraphEntity] | None:
    """Look up an entity class by its name string."""
    return ENTITY_TYPES.get(entity_name)


def validate_entity_data(entity_name: str, data: dict[str, Any]) -> GraphEntity:
    """
    Instantiate and validate raw dictionary data against the registered entity model.
    """
    cls = get_entity_class(entity_name)
    if not cls:
        raise ValueError(f"Unknown entity type: {entity_name!r}")
    return cls.model_validate(data)


def validate_graph_edge(rel_type_str: str, source: GraphEntity, target: GraphEntity) -> bool:
    """
    Validate that an edge between source and target obeys ontology relationship rules.
    """
    try:
        rel_enum = RelationshipType(rel_type_str)
    except ValueError:
        return False
    return validate_relationship(rel_enum, source.entity_type, target.entity_type)


def ontology_summary() -> dict[str, Any]:
    """Return a summary metadata of the Industrial Safety Ontology."""
    return {
        "entity_count": len(ENTITY_TYPES),
        "entities": list(ENTITY_TYPES.keys()),
        "relationship_count": len(RELATIONSHIP_TYPES),
        "relationships": RELATIONSHIP_TYPES,
        "enum_count": len(ENUM_REGISTRY),
        "enums": list(ENUM_REGISTRY.keys()),
    }

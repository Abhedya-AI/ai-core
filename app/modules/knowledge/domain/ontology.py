"""
ontology.py — Industrial Safety Ontology Registry.

Acts as the central catalogue of all entities, relationships, enums,
and rules supported by ABHEDYA. Used by graph services, RAG, and multi-agent systems
to validate and inspect ontology elements dynamically.
"""

from typing import Any, Type

from app.modules.knowledge.domain.entities import (
    Alert,
    Asset,
    Building,
    Camera,
    Contractor,
    Device,
    Document,
    DocumentChunk,
    Emergency,
    EmergencyPlan,
    Equipment,
    Floor,
    GraphEntity,
    Hazard,
    Incident,
    Inspection,
    Maintenance,
    Notification,
    Permit,
    Plant,
    Policy,
    PPE,
    Prediction,
    Reading,
    Recommendation,
    Regulation,
    Risk,
    Sensor,
    Standard,
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
    # Core 20 Industrial Safety Node Types
    "Plant": Plant,
    "Building": Building,
    "Floor": Floor,
    "Zone": Zone,
    "Equipment": Equipment,
    "Sensor": Sensor,
    "Worker": Worker,
    "Reading": Reading,
    "Incident": Incident,
    "Alert": Alert,
    "Hazard": Hazard,
    "Emergency": Emergency,
    "Maintenance": Maintenance,
    "Inspection": Inspection,
    "Risk": Risk,
    "Recommendation": Recommendation,
    "Policy": Policy,
    "Standard": Standard,
    "PPE": PPE,
    "Device": Device,
    # Additional Extended Entities
    "Asset": Asset,
    "Camera": Camera,
    "Contractor": Contractor,
    "Document": Document,
    "DocumentChunk": DocumentChunk,
    "EmergencyPlan": EmergencyPlan,
    "Notification": Notification,
    "Permit": Permit,
    "Prediction": Prediction,
    "Regulation": Regulation,
    "Visitor": Visitor,
    "Weather": Weather,
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

# The 18 Primary Industrial Relationship Types (plus extended domain relationships)
RELATIONSHIP_TYPES: list[str] = [
    # 18 Core Relationship Types
    "LOCATED_IN",
    "MONITORS",
    "CONNECTED_TO",
    "GENERATED",
    "TRIGGERED",
    "AFFECTS",
    "NEAR",
    "OPERATED_BY",
    "HAS_RISK",
    "CAUSES",
    "PREVENTS",
    "PART_OF",
    "ASSOCIATED_WITH",
    "RESPONDED_BY",
    "INSPECTED_BY",
    "REQUIRES",
    "PROTECTS",
    # Extended Ontology Relationships
    "WORKS_IN",
    "OPERATES",
    "ASSIGNED_TO",
    "HAS_SENSOR",
    "LEADS_TO",
    "MITIGATES",
    "RESPONDS_TO",
    "DETECTED_BY",
    "PREDICTED_BY",
    "REFERENCES",
    "COMPLIES_WITH",
    "HAS_DOCUMENT",
    "HAS_CHUNK",
    "USES",
    "NOTIFIES",
]


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

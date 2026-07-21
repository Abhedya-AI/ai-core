from typing import NamedTuple

from app.modules.knowledge.domain.relationships.relationship_types import RelationshipType


class RelationshipRule(NamedTuple):
    """Rule defining allowed source and target entity types for a relationship."""

    rel_type: RelationshipType
    allowed_sources: set[str]
    allowed_targets: set[str]


# ── Allowed entity pairings per relationship type ──────────────────────────────
_RULES: dict[RelationshipType, RelationshipRule] = {
    RelationshipType.WORKS_IN: RelationshipRule(
        rel_type=RelationshipType.WORKS_IN,
        allowed_sources={"Worker", "Contractor", "Visitor"},
        allowed_targets={"Zone", "Building", "Floor"},
    ),
    RelationshipType.LOCATED_IN: RelationshipRule(
        rel_type=RelationshipType.LOCATED_IN,
        allowed_sources={"Equipment", "Asset", "Sensor", "Camera", "Hazard", "Incident", "Floor", "Zone"},
        allowed_targets={"Zone", "Building", "Floor"},
    ),
    RelationshipType.OPERATES: RelationshipRule(
        rel_type=RelationshipType.OPERATES,
        allowed_sources={"Worker", "Contractor"},
        allowed_targets={"Equipment", "Asset"},
    ),
    RelationshipType.ASSIGNED_TO: RelationshipRule(
        rel_type=RelationshipType.ASSIGNED_TO,
        allowed_sources={"Worker", "Contractor", "Maintenance", "Permit"},
        allowed_targets={"Maintenance", "Permit", "Equipment", "Zone", "Incident", "EmergencyPlan"},
    ),
    RelationshipType.HAS_SENSOR: RelationshipRule(
        rel_type=RelationshipType.HAS_SENSOR,
        allowed_sources={"Equipment", "Asset", "Zone"},
        allowed_targets={"Sensor", "Camera"},
    ),
    RelationshipType.MONITORS: RelationshipRule(
        rel_type=RelationshipType.MONITORS,
        allowed_sources={"Sensor", "Camera"},
        allowed_targets={"Equipment", "Asset", "Zone", "Worker"},
    ),
    RelationshipType.GENERATED: RelationshipRule(
        rel_type=RelationshipType.GENERATED,
        allowed_sources={"Sensor", "Camera", "Hazard", "Worker"},
        allowed_targets={"Prediction", "Notification", "Incident", "Hazard"},
    ),
    RelationshipType.CAUSES: RelationshipRule(
        rel_type=RelationshipType.CAUSES,
        allowed_sources={"Hazard", "Equipment", "Weather"},
        allowed_targets={"Incident", "Hazard", "Equipment"},
    ),
    RelationshipType.AFFECTS: RelationshipRule(
        rel_type=RelationshipType.AFFECTS,
        allowed_sources={"Incident", "Hazard", "Weather"},
        allowed_targets={"Worker", "Equipment", "Zone", "Asset"},
    ),
    RelationshipType.CONNECTED_TO: RelationshipRule(
        rel_type=RelationshipType.CONNECTED_TO,
        allowed_sources={"Equipment", "Asset", "Zone"},
        allowed_targets={"Equipment", "Asset", "Zone"},
    ),
    RelationshipType.PART_OF: RelationshipRule(
        rel_type=RelationshipType.PART_OF,
        allowed_sources={"Zone", "Floor", "Building", "Equipment", "DocumentChunk"},
        allowed_targets={"Building", "Floor", "Equipment", "Document"},
    ),
    RelationshipType.LEADS_TO: RelationshipRule(
        rel_type=RelationshipType.LEADS_TO,
        allowed_sources={"Hazard", "Incident"},
        allowed_targets={"Incident", "EmergencyPlan"},
    ),
    RelationshipType.MITIGATES: RelationshipRule(
        rel_type=RelationshipType.MITIGATES,
        allowed_sources={"Maintenance", "EmergencyPlan", "Regulation", "Permit"},
        allowed_targets={"Hazard", "Incident", "Equipment"},
    ),
    RelationshipType.RESPONDS_TO: RelationshipRule(
        rel_type=RelationshipType.RESPONDS_TO,
        allowed_sources={"EmergencyPlan", "Worker"},
        allowed_targets={"Incident", "Hazard"},
    ),
    RelationshipType.DETECTED_BY: RelationshipRule(
        rel_type=RelationshipType.DETECTED_BY,
        allowed_sources={"Hazard", "Incident"},
        allowed_targets={"Sensor", "Camera", "Worker"},
    ),
    RelationshipType.PREDICTED_BY: RelationshipRule(
        rel_type=RelationshipType.PREDICTED_BY,
        allowed_sources={"Hazard", "Incident", "Equipment"},
        allowed_targets={"Prediction"},
    ),
    RelationshipType.REFERENCES: RelationshipRule(
        rel_type=RelationshipType.REFERENCES,
        allowed_sources={"Document", "Permit", "Incident", "Prediction"},
        allowed_targets={"Regulation", "Document", "Equipment", "Zone"},
    ),
    RelationshipType.COMPLIES_WITH: RelationshipRule(
        rel_type=RelationshipType.COMPLIES_WITH,
        allowed_sources={"Permit", "Maintenance", "Worker", "Equipment"},
        allowed_targets={"Regulation"},
    ),
    RelationshipType.HAS_DOCUMENT: RelationshipRule(
        rel_type=RelationshipType.HAS_DOCUMENT,
        allowed_sources={"Equipment", "Zone", "Regulation"},
        allowed_targets={"Document"},
    ),
    RelationshipType.HAS_CHUNK: RelationshipRule(
        rel_type=RelationshipType.HAS_CHUNK,
        allowed_sources={"Document"},
        allowed_targets={"DocumentChunk"},
    ),
    RelationshipType.USES: RelationshipRule(
        rel_type=RelationshipType.USES,
        allowed_sources={"Worker", "Maintenance"},
        allowed_targets={"Equipment", "Permit"},
    ),
    RelationshipType.REQUIRES: RelationshipRule(
        rel_type=RelationshipType.REQUIRES,
        allowed_sources={"Maintenance", "Equipment", "Zone"},
        allowed_targets={"Permit", "Regulation"},
    ),
    RelationshipType.NOTIFIES: RelationshipRule(
        rel_type=RelationshipType.NOTIFIES,
        allowed_sources={"Notification", "Prediction"},
        allowed_targets={"Worker"},
    ),
}


def validate_relationship(rel_type: RelationshipType, source_type: str, target_type: str) -> bool:
    """
    Check if a relationship between source_type and target_type is permitted by the ontology.

    Returns True if valid, False otherwise.
    """
    rule = _RULES.get(rel_type)
    if not rule:
        return False
    return (source_type in rule.allowed_sources) and (target_type in rule.allowed_targets)

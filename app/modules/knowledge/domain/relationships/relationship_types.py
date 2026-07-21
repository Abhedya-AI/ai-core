from enum import Enum


class RelationshipType(str, Enum):
    """
    Frozen relationship names for the Industrial Safety Ontology.

    No ad-hoc relationship strings allowed in Cypher queries.
    """

    WORKS_IN = "WORKS_IN"
    LOCATED_IN = "LOCATED_IN"
    OPERATES = "OPERATES"
    ASSIGNED_TO = "ASSIGNED_TO"
    HAS_SENSOR = "HAS_SENSOR"
    MONITORS = "MONITORS"
    GENERATED = "GENERATED"
    CAUSES = "CAUSES"
    AFFECTS = "AFFECTS"
    CONNECTED_TO = "CONNECTED_TO"
    PART_OF = "PART_OF"
    LEADS_TO = "LEADS_TO"
    MITIGATES = "MITIGATES"
    RESPONDS_TO = "RESPONDS_TO"
    DETECTED_BY = "DETECTED_BY"
    PREDICTED_BY = "PREDICTED_BY"
    REFERENCES = "REFERENCES"
    COMPLIES_WITH = "COMPLIES_WITH"
    HAS_DOCUMENT = "HAS_DOCUMENT"
    HAS_CHUNK = "HAS_CHUNK"
    USES = "USES"
    REQUIRES = "REQUIRES"
    NOTIFIES = "NOTIFIES"

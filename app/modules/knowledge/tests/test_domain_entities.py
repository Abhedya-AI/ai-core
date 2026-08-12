"""
test_domain_entities.py — Domain Entity & Ontology Unit Tests.
"""
import pytest
from app.modules.knowledge.domain.entities import (
    Equipment, Hazard, Incident, Sensor, Worker, Zone, GraphEntity
)
from app.modules.knowledge.domain.enums import (
    EquipmentStatus, HazardLevel, IncidentStatus, SensorType, WorkerRole, ZoneType
)
from app.modules.knowledge.domain.ontology import (
    ENTITY_TYPES, ENUM_REGISTRY, RELATIONSHIP_TYPES, ontology_summary, validate_entity_data, get_entity_class
)
from app.modules.knowledge.domain.relationships import (
    RelationshipType, validate_relationship
)


def test_graph_entity_base_serialization():
    entity = GraphEntity(id="e-100", metadata={"floor": 2})
    props = entity.to_graph_properties()
    assert props["id"] == "e-100"
    assert props["entity_type"] == "GraphEntity"
    assert "created_at" in props


def test_worker_entity(sample_worker):
    assert sample_worker.id == "worker-test-01"
    assert sample_worker.name == "Ravi Kumar"
    assert sample_worker.badge_number == "B-101"
    assert sample_worker.role == WorkerRole.OPERATOR
    assert sample_worker.entity_type == "Worker"
    props = sample_worker.to_graph_properties()
    assert props["name"] == "Ravi Kumar"


def test_equipment_entity(sample_equipment):
    assert sample_equipment.code == "EQ-BLR3"
    assert sample_equipment.status == EquipmentStatus.OPERATIONAL
    assert sample_equipment.entity_type == "Equipment"


def test_sensor_entity(sample_sensor):
    assert sample_sensor.sensor_type == SensorType.PRESSURE
    assert sample_sensor.unit == "PSI"
    assert sample_sensor.entity_type == "Sensor"


def test_zone_entity(sample_zone):
    assert sample_zone.code == "Z-BOILER-A"
    assert sample_zone.risk_score == 75.0
    assert sample_zone.entity_type == "Zone"


def test_hazard_entity(sample_hazard):
    assert sample_hazard.severity == HazardLevel.HIGH
    assert sample_hazard.description == "Pressure exceeded safety threshold"
    assert sample_hazard.entity_type == "Hazard"


def test_incident_entity(sample_incident):
    assert sample_incident.status == IncidentStatus.OPEN
    assert sample_incident.description == "Minor steam leak detected"
    assert sample_incident.entity_type == "Incident"


def test_ontology_catalogue():
    summary = ontology_summary()
    assert summary["entity_count"] >= 30
    assert summary["relationship_count"] >= 18
    assert "Worker" in summary["entities"]
    assert "Equipment" in summary["entities"]
    assert "LOCATED_IN" in summary["relationships"]
    assert "MONITORS" in summary["relationships"]


def test_ontology_get_entity_class():
    cls = get_entity_class("Worker")
    assert cls == Worker
    assert get_entity_class("NonExistent") is None


def test_validate_entity_data():
    raw_data = {"id": "w-55", "name": "John", "badge_number": "B-55", "role": "OPERATOR", "entity_type": "Worker"}
    entity = validate_entity_data("Worker", raw_data)
    assert isinstance(entity, Worker)
    assert entity.name == "John"


def test_validate_relationship():
    assert validate_relationship(RelationshipType.MONITORS, "Sensor", "Equipment") is True
    assert validate_relationship(RelationshipType.LOCATED_IN, "Equipment", "Zone") is True
    assert validate_relationship(RelationshipType.AFFECTS, "Hazard", "Worker") is True

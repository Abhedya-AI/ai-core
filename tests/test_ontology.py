from datetime import datetime, timedelta, timezone

import pytest

from app.modules.knowledge.domain.entities import (
    Equipment,
    Hazard,
    Incident,
    Maintenance,
    Permit,
    Sensor,
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
from app.modules.knowledge.domain.ontology import (
    ENTITY_TYPES,
    RELATIONSHIP_TYPES,
    get_entity_class,
    ontology_summary,
    validate_entity_data,
    validate_graph_edge,
)
from app.modules.knowledge.domain.relationships import (
    RelationshipType,
    validate_relationship,
)
from app.modules.knowledge.domain.rules import (
    DomainValidationError,
    validate_hazard_escalation,
    validate_permit_for_maintenance,
    validate_sensor_thresholds,
    validate_worker_zone_access,
)


def test_entity_instantiation_and_inheritance():
    """Verify entity models inherit from GraphEntity and have correct defaults."""
    worker = Worker(
        badge_number="W-1001",
        name="Alex Smith",
        role=WorkerRole.OPERATOR,
        certifications=["HAZMAT"],
    )
    assert worker.entity_type == "Worker"
    assert worker.id is not None
    assert worker.created_at is not None

    props = worker.to_graph_properties()
    assert props["name"] == "Alex Smith"
    assert props["badge_number"] == "W-1001"
    assert props["entity_type"] == "Worker"


def test_permit_date_validation():
    """Verify Permit raises ValueError if end_time <= start_time."""
    now = datetime.now(tz=timezone.utc)
    with pytest.raises(ValueError, match="Permit end_time must be after start_time"):
        Permit(
            title="Hot Work Permit",
            issued_to_worker_id="W-1",
            zone_id="Z-10",
            start_time=now,
            end_time=now - timedelta(hours=1),
        )


def test_relationship_rules():
    """Verify relationship rules allow valid entity pairs and reject invalid ones."""
    assert validate_relationship(RelationshipType.WORKS_IN, "Worker", "Zone") is True
    assert validate_relationship(RelationshipType.HAS_SENSOR, "Equipment", "Sensor") is True
    assert validate_relationship(RelationshipType.MONITORS, "Sensor", "Equipment") is True

    # Invalid: Sensor cannot WORK_IN a Worker
    assert validate_relationship(RelationshipType.WORKS_IN, "Sensor", "Worker") is False

    worker = Worker(badge_number="W-1", name="John")
    zone = Zone(name="Zone A", code="ZA-1")
    assert validate_graph_edge("WORKS_IN", worker, zone) is True
    assert validate_graph_edge("MONITORS", worker, zone) is False


def test_domain_rules_worker_access():
    """Verify domain rules for hazardous zone access."""
    operator = Worker(badge_number="W-1", name="Operator Joe", role=WorkerRole.OPERATOR)
    haz_zone = Zone(name="Chemical Bay", code="HZ-9", zone_type=ZoneType.HAZARDOUS)

    # Operator without certs fails
    with pytest.raises(DomainValidationError, match="lacks authorization"):
        validate_worker_zone_access(operator, haz_zone)

    # Safety officer succeeds
    officer = Worker(badge_number="W-2", name="Officer Jane", role=WorkerRole.SAFETY_OFFICER)
    validate_worker_zone_access(officer, haz_zone)


def test_domain_rules_permit_maintenance():
    """Verify maintenance in hazardous zone requires valid permit."""
    haz_zone = Zone(name="Hazmat", code="HZ-1", zone_type=ZoneType.HAZARDOUS)
    maint = Maintenance(
        title="Valve overhaul",
        equipment_id="EQ-1",
        assigned_worker_id="W-1",
        task_description="Repair seal",
        scheduled_date=datetime.now(tz=timezone.utc),
    )

    # No permit -> fails
    with pytest.raises(DomainValidationError, match="requires a valid permit"):
        validate_permit_for_maintenance(maint, None, haz_zone)

    # Draft permit -> fails
    draft_permit = Permit(
        title="Draft",
        issued_to_worker_id="W-1",
        zone_id=haz_zone.id,
        status=PermitStatus.DRAFT,
        start_time=datetime.now(tz=timezone.utc),
        end_time=datetime.now(tz=timezone.utc) + timedelta(hours=2),
    )
    with pytest.raises(DomainValidationError, match="must be APPROVED or ACTIVE"):
        validate_permit_for_maintenance(maint, draft_permit, haz_zone)

    # Active permit -> passes
    draft_permit.status = PermitStatus.ACTIVE
    validate_permit_for_maintenance(maint, draft_permit, haz_zone)


def test_domain_rules_sensor_thresholds():
    """Verify sensor threshold domain validation."""
    invalid_sensor = Sensor(
        name="Temp Sensor 1",
        min_threshold=100.0,
        max_threshold=50.0,
    )
    with pytest.raises(DomainValidationError, match="must be less than max_threshold"):
        validate_sensor_thresholds(invalid_sensor)

    valid_sensor = Sensor(
        name="Temp Sensor 2",
        min_threshold=10.0,
        max_threshold=90.0,
    )
    validate_sensor_thresholds(valid_sensor)


def test_hazard_escalation():
    """Verify critical hazard escalation logic."""
    haz = Hazard(
        title="Gas Leak",
        description="H2S detected",
        severity=HazardLevel.CRITICAL,
        zone_id="Z-1",
        mitigated=False,
    )
    assert validate_hazard_escalation(haz) is True

    haz.mitigated = True
    assert validate_hazard_escalation(haz) is False


def test_ontology_registry():
    """Verify the central ontology registry catalogue and validation."""
    summary = ontology_summary()
    assert summary["entity_count"] == 21
    assert "Worker" in summary["entities"]
    assert "Equipment" in summary["entities"]
    assert "Hazard" in summary["entities"]
    assert len(summary["relationships"]) == 23

    cls = get_entity_class("Worker")
    assert cls is Worker

    data = {
        "badge_number": "W-99",
        "name": "Sam",
        "role": "TECHNICIAN",
    }
    entity = validate_entity_data("Worker", data)
    assert isinstance(entity, Worker)
    assert entity.role == WorkerRole.TECHNICIAN

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.kafka.producer import EventBus
from app.modules.knowledge.domain.entities import (
    Equipment,
    Hazard,
    Incident,
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
from app.modules.knowledge.domain.rules import DomainValidationError
from app.modules.knowledge.services import (
    EquipmentService,
    GraphService,
    HazardService,
    IncidentService,
    KnowledgeService,
    PermitService,
    SensorService,
    ValidationService,
    WorkerService,
)


@pytest.mark.asyncio
async def test_worker_service_and_events():
    """Verify WorkerService registers worker and publishes event."""
    mock_repo = AsyncMock()
    mock_repo.create_worker.return_value = {"id": "W-100", "badge_number": "BADGE-100"}

    svc = WorkerService(repository=mock_repo)
    worker = Worker(id="W-100", badge_number="BADGE-100", name="Frank", role=WorkerRole.TECHNICIAN)

    res = await svc.register_worker(worker)
    assert res["badge_number"] == "BADGE-100"
    mock_repo.create_worker.assert_called_once_with(worker)


@pytest.mark.asyncio
async def test_equipment_service_duplicate_sensor_prevention():
    """Verify EquipmentService rejects duplicate sensor types on equipment."""
    mock_equip_repo = AsyncMock()
    mock_sensor_repo = AsyncMock()

    # Return existing temperature sensor
    mock_sensor_repo.get_sensors_for_equipment.return_value = [
        {"id": "S-1", "sensor_type": "TEMPERATURE"}
    ]

    svc = EquipmentService(equipment_repo=mock_equip_repo, sensor_repo=mock_sensor_repo)
    new_sensor = Sensor(name="Temp 2", sensor_type=SensorType.TEMPERATURE)

    with pytest.raises(DomainValidationError, match="already has an attached telemetry sensor"):
        await svc.attach_sensor_to_equipment("EQ-1", new_sensor)


@pytest.mark.asyncio
async def test_hazard_service_critical_escalation():
    """Verify HazardService triggers emergency alert event for unmitigated critical hazard."""
    mock_repo = AsyncMock()
    mock_repo.create_hazard.return_value = {"id": "H-99", "severity": "CRITICAL"}

    svc = HazardService(repository=mock_repo)
    crit_hazard = Hazard(
        id="H-99",
        title="Gas Pressure Critical",
        description="Overpressure in Tank 4",
        severity=HazardLevel.CRITICAL,
        zone_id="Z-4",
        mitigated=False,
    )

    res = await svc.report_hazard(crit_hazard)
    assert res["severity"] == "CRITICAL"
    mock_repo.create_hazard.assert_called_once_with(crit_hazard)


@pytest.mark.asyncio
async def test_knowledge_facade_workflow():
    """Verify KnowledgeService facade orchestrates cross-domain workflow."""
    mock_hazard_svc = AsyncMock()
    mock_hazard_svc.report_hazard.return_value = {"id": "H-1"}
    mock_graph_svc = AsyncMock()
    mock_graph_svc.connect_entities.return_value = True

    facade = KnowledgeService(hazard_svc=mock_hazard_svc, graph_svc=mock_graph_svc)

    hazard = Hazard(title="High Temp", description="Engine overheating", zone_id="Z-1")
    equipment = Equipment(code="ENG-1", name="Main Engine")

    res = await facade.report_hazard_on_equipment(hazard, equipment)
    assert res["id"] == "H-1"
    mock_hazard_svc.report_hazard.assert_called_once_with(hazard)
    mock_graph_svc.connect_entities.assert_called_once()


@pytest.mark.asyncio
async def test_maintenance_emergency_notification_services():
    """Verify Maintenance, Emergency, and Notification services."""
    from app.modules.knowledge.domain.entities import EmergencyPlan, Maintenance, Notification
    from app.modules.knowledge.services import EmergencyService, MaintenanceService, NotificationService

    mock_repo = AsyncMock()
    mock_repo.create_node.return_value = {"id": "M-1"}

    m_svc = MaintenanceService(repository=mock_repo)
    maint = Maintenance(title="Valve Inspection", equipment_id="EQ-1", assigned_worker_id="W-1", task_description="Inspect valve", scheduled_date=datetime.now(tz=timezone.utc))
    m_res = await m_svc.schedule_maintenance(maint)
    assert m_res["id"] == "M-1"

    e_svc = EmergencyService(repository=mock_repo)
    plan = EmergencyPlan(title="Gas Leak Plan", emergency_type="GAS_LEAK", zone_ids=["Z-1"])
    e_res = await e_svc.trigger_emergency_plan(plan)
    assert e_res["id"] == "M-1"

    n_svc = NotificationService(repository=mock_repo)
    notif = Notification(title="Evacuation Alert", recipient_worker_id="W-1", message="Evacuate Zone 1 immediately")
    n_res = await n_svc.send_notification(notif)
    assert n_res["id"] == "M-1"


"""
rules.py — Domain rules and business invariants for Industrial Safety.

These represent business rules (not DB constraints) that must be satisfied
before entities or graph edges are persisted.
"""

from app.modules.knowledge.domain.entities.hazard import Hazard
from app.modules.knowledge.domain.entities.incident import Incident
from app.modules.knowledge.domain.entities.maintenance import Maintenance
from app.modules.knowledge.domain.entities.permit import Permit
from app.modules.knowledge.domain.entities.sensor import Sensor
from app.modules.knowledge.domain.entities.worker import Worker
from app.modules.knowledge.domain.entities.zone import Zone
from app.modules.knowledge.domain.enums import HazardLevel, PermitStatus, ZoneType


class DomainValidationError(Exception):
    """Raised when a business domain rule is violated."""


def validate_worker_zone_access(worker: Worker, zone: Zone) -> None:
    """
    Rule: Accessing HAZARDOUS zone requires SAFETY_OFFICER, TECHNICIAN, or SUPERVISOR role,
    or explicit certification.
    """
    if zone.zone_type == ZoneType.HAZARDOUS:
        authorized_roles = {"SAFETY_OFFICER", "TECHNICIAN", "SUPERVISOR", "INSPECTOR"}
        if worker.role.value not in authorized_roles and not worker.certifications:
            raise DomainValidationError(
                f"Worker {worker.name} (Role: {worker.role}) lacks authorization for HAZARDOUS zone {zone.code}"
            )


def validate_permit_for_maintenance(maintenance: Maintenance, permit: Permit | None, zone: Zone) -> None:
    """
    Rule: Maintenance in a HAZARDOUS zone requires an APPROVED or ACTIVE Permit.
    """
    if zone.zone_type == ZoneType.HAZARDOUS:
        if not permit:
            raise DomainValidationError(
                f"Maintenance task '{maintenance.title}' in HAZARDOUS zone '{zone.code}' requires a valid permit"
            )
        if permit.status not in (PermitStatus.APPROVED, PermitStatus.ACTIVE):
            raise DomainValidationError(
                f"Permit '{permit.id}' status is '{permit.status}', must be APPROVED or ACTIVE for maintenance"
            )


def validate_sensor_thresholds(sensor: Sensor) -> None:
    """
    Rule: If both min_threshold and max_threshold are set, min must be strictly less than max.
    """
    if sensor.min_threshold is not None and sensor.max_threshold is not None:
        if sensor.min_threshold >= sensor.max_threshold:
            raise DomainValidationError(
                f"Sensor '{sensor.name}' min_threshold ({sensor.min_threshold}) "
                f"must be less than max_threshold ({sensor.max_threshold})"
            )


def validate_hazard_escalation(hazard: Hazard) -> bool:
    """
    Rule: Critical hazards automatically trigger incident escalation check.
    Returns True if escalation is required.
    """
    return hazard.severity == HazardLevel.CRITICAL and not hazard.mitigated

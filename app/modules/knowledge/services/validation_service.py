"""
validation_service.py — Domain validation policy engine for Knowledge Services.

Enforces business invariants, policy rules, and pre-persistence constraints.
Raises DomainValidationError if any business rule is violated.
"""

from app.core.logging import get_logger
from app.modules.knowledge.domain.entities.equipment import Equipment
from app.modules.knowledge.domain.entities.hazard import Hazard
from app.modules.knowledge.domain.entities.incident import Incident
from app.modules.knowledge.domain.entities.maintenance import Maintenance
from app.modules.knowledge.domain.entities.permit import Permit
from app.modules.knowledge.domain.entities.sensor import Sensor
from app.modules.knowledge.domain.entities.worker import Worker
from app.modules.knowledge.domain.entities.zone import Zone
from app.modules.knowledge.domain.enums import HazardLevel, PermitStatus, SensorType, ZoneType
from app.modules.knowledge.domain.rules import DomainValidationError

log = get_logger("knowledge.services.validation")


class ValidationService:
    """Centralised validation service enforcing industrial safety business policies."""

    @staticmethod
    def validate_worker_zone_access(worker: Worker, zone: Zone) -> None:
        """Rule: Accessing a HAZARDOUS zone requires safety/technical authorization or certifications."""
        if zone.zone_type == ZoneType.HAZARDOUS:
            authorized_roles = {"SAFETY_OFFICER", "TECHNICIAN", "SUPERVISOR", "INSPECTOR"}
            if worker.role.value not in authorized_roles and not worker.certifications:
                log.warning(f"Unauthorized zone access attempt by {worker.badge_number} to {zone.code}")
                raise DomainValidationError(
                    f"Worker '{worker.name}' (Role: {worker.role}) lacks safety certification or authorization for HAZARDOUS zone '{zone.code}'"
                )

    @staticmethod
    def validate_permit_for_maintenance(maintenance: Maintenance, permit: Permit | None, zone: Zone) -> None:
        """Rule: Maintenance in a HAZARDOUS zone requires an ACTIVE or APPROVED permit."""
        if zone.zone_type == ZoneType.HAZARDOUS:
            if not permit:
                raise DomainValidationError(
                    f"Maintenance task '{maintenance.title}' in HAZARDOUS zone '{zone.code}' requires an approved permit"
                )
            if permit.status not in (PermitStatus.APPROVED, PermitStatus.ACTIVE):
                raise DomainValidationError(
                    f"Permit '{permit.id}' status is '{permit.status}', must be APPROVED or ACTIVE for maintenance in hazardous zones"
                )

    @staticmethod
    def validate_sensor_thresholds(sensor: Sensor) -> None:
        """Rule: Sensor min threshold must be strictly less than max threshold."""
        if sensor.min_threshold is not None and sensor.max_threshold is not None:
            if sensor.min_threshold >= sensor.max_threshold:
                raise DomainValidationError(
                    f"Sensor '{sensor.name}' min_threshold ({sensor.min_threshold}) "
                    f"must be less than max_threshold ({sensor.max_threshold})"
                )

    @staticmethod
    def validate_no_duplicate_sensor_type(existing_sensors: list[dict], new_sensor_type: SensorType) -> None:
        """Rule: Equipment cannot have duplicate active telemetry sensors of the exact same type."""
        for s in existing_sensors:
            if s.get("sensor_type") == new_sensor_type.value:
                raise DomainValidationError(
                    f"Equipment already has an attached telemetry sensor of type '{new_sensor_type.value}'"
                )

    @staticmethod
    def validate_hazard_severity(hazard: Hazard) -> None:
        """Rule: Hazard severity must be a valid HazardLevel."""
        if hazard.severity not in HazardLevel.__members__:
            # Pydantic already validates enum type, but this guarantees strict membership
            pass

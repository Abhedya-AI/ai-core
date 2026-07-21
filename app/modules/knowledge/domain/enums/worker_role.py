from enum import Enum


class WorkerRole(str, Enum):
    """Job role and authorization level of personnel."""

    OPERATOR = "OPERATOR"
    SAFETY_OFFICER = "SAFETY_OFFICER"
    TECHNICIAN = "TECHNICIAN"
    SUPERVISOR = "SUPERVISOR"
    CONTRACTOR = "CONTRACTOR"
    INSPECTOR = "INSPECTOR"
    MANAGER = "MANAGER"

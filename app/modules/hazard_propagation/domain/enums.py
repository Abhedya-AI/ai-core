from __future__ import annotations
from enum import Enum

class HazardType(str, Enum):
    FIRE = "FIRE"
    SMOKE = "SMOKE"
    GAS_LEAK = "GAS_LEAK"
    TOXIC_GAS = "TOXIC_GAS"
    CHEMICAL_SPILL = "CHEMICAL_SPILL"
    EXPLOSION = "EXPLOSION"
    ELECTRICAL_FAULT = "ELECTRICAL_FAULT"
    POWER_FAILURE = "POWER_FAILURE"
    STEAM_LEAK = "STEAM_LEAK"
    HIGH_PRESSURE = "HIGH_PRESSURE"
    STRUCTURAL_COLLAPSE = "STRUCTURAL_COLLAPSE"
    FLOOD = "FLOOD"
    RADIATION = "RADIATION"
    COMPOSITE = "COMPOSITE"

class PropagationState(str, Enum):
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    CONTAINED = "CONTAINED"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"

class ExposureLevel(str, Enum):
    NONE = "NONE"
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    LETHAL = "LETHAL"

    @classmethod
    def from_score(cls, score: float) -> ExposureLevel:
        if score < 0.05:
            return cls.NONE
        elif score < 0.15:
            return cls.MINIMAL
        elif score < 0.30:
            return cls.LOW
        elif score < 0.50:
            return cls.MODERATE
        elif score < 0.70:
            return cls.HIGH
        elif score < 0.90:
            return cls.CRITICAL
        else:
            return cls.LETHAL

class ContainmentStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"

class EvacuationStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    RECOMMENDED = "RECOMMENDED"
    MANDATORY = "MANDATORY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"

class CascadeStatus(str, Enum):
    NO_CASCADE = "NO_CASCADE"
    POTENTIAL = "POTENTIAL"
    DETECTED = "DETECTED"
    ACTIVE = "ACTIVE"
    CONTAINED = "CONTAINED"

class BarrierType(str, Enum):
    FIRE_DOOR = "FIRE_DOOR"
    FIREWALL = "FIREWALL"
    BLAST_WALL = "BLAST_WALL"
    CONTAINMENT_BUND = "CONTAINMENT_BUND"
    VAPOUR_BARRIER = "VAPOUR_BARRIER"
    SAFETY_VALVE = "SAFETY_VALVE"
    ISOLATION_VALVE = "ISOLATION_VALVE"
    BLAST_CURTAIN = "BLAST_CURTAIN"

    @property
    def resistance_factor(self) -> float:
        if self == BarrierType.FIREWALL:
            return 0.95
        elif self == BarrierType.BLAST_WALL:
            return 0.90
        elif self == BarrierType.SAFETY_VALVE:
            return 0.85
        elif self == BarrierType.ISOLATION_VALVE:
            return 0.80
        elif self == BarrierType.CONTAINMENT_BUND:
            return 0.75
        elif self == BarrierType.FIRE_DOOR:
            return 0.70
        elif self == BarrierType.VAPOUR_BARRIER:
            return 0.60
        elif self == BarrierType.BLAST_CURTAIN:
            return 0.50
        return 0.0

class HazardSeverity(str, Enum):
    NEGLIGIBLE = "NEGLIGIBLE"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"
    CATASTROPHIC = "CATASTROPHIC"

    @classmethod
    def from_score(cls, score: float) -> HazardSeverity:
        if score < 0.10:
            return cls.NEGLIGIBLE
        elif score < 0.25:
            return cls.MINOR
        elif score < 0.45:
            return cls.MODERATE
        elif score < 0.65:
            return cls.MAJOR
        elif score < 0.85:
            return cls.CRITICAL
        else:
            return cls.CATASTROPHIC

    @property
    def evacuation_required(self) -> bool:
        return self in (HazardSeverity.MAJOR, HazardSeverity.CRITICAL, HazardSeverity.CATASTROPHIC)

class PropagationModelType(str, Enum):
    GAUSSIAN_PLUME = "GAUSSIAN_PLUME"
    CELLULAR_AUTOMATA = "CELLULAR_AUTOMATA"
    GRAPH_DIFFUSION = "GRAPH_DIFFUSION"
    PHYSICS_ODES = "PHYSICS_ODES"
    BAYESIAN_SPREAD = "BAYESIAN_SPREAD"
    ENSEMBLE = "ENSEMBLE"

class SimulationStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class NodeType(str, Enum):
    ZONE = "ZONE"
    EQUIPMENT = "EQUIPMENT"
    WORKER = "WORKER"
    PIPELINE = "PIPELINE"
    ELECTRICAL_PANEL = "ELECTRICAL_PANEL"
    STORAGE_TANK = "STORAGE_TANK"
    BUILDING = "BUILDING"

class HazardRecommendationType(str, Enum):
    IMMEDIATE_EVACUATION = "IMMEDIATE_EVACUATION"
    PARTIAL_EVACUATION = "PARTIAL_EVACUATION"
    SHELTER_IN_PLACE = "SHELTER_IN_PLACE"
    EQUIPMENT_SHUTDOWN = "EQUIPMENT_SHUTDOWN"
    VALVE_ISOLATION = "VALVE_ISOLATION"
    FIRE_SUPPRESSION = "FIRE_SUPPRESSION"
    VENTILATION_INCREASE = "VENTILATION_INCREASE"
    CONTAINMENT_BUND = "CONTAINMENT_BUND"
    EMERGENCY_SERVICES = "EMERGENCY_SERVICES"
    MONITORING_INCREASE = "MONITORING_INCREASE"
    BARRIER_DEPLOYMENT = "BARRIER_DEPLOYMENT"
    RESOURCE_DEPLOYMENT = "RESOURCE_DEPLOYMENT"

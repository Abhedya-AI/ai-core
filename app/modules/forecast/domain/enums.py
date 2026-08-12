from __future__ import annotations
from enum import Enum

class ForecastHorizon(str, Enum):
    FIFTEEN_MIN = "15m"   # 15 minutes
    THIRTY_MIN = "30m"    # 30 minutes
    ONE_HOUR = "1h"       # 60 minutes
    SIX_HOUR = "6h"       # 360 minutes
    TWENTY_FOUR_HOUR = "24h"  # 1440 minutes
    THREE_DAY = "3d"      # 4320 minutes
    SEVEN_DAY = "7d"      # 10080 minutes
    THIRTY_DAY = "30d"    # 43200 minutes
    
    @property
    def minutes(self) -> int:
        mapping = {
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "6h": 360,
            "24h": 1440,
            "3d": 4320,
            "7d": 10080,
            "30d": 43200
        }
        return mapping[self.value]

    @property  
    def label(self) -> str:
        mapping = {
            "15m": "15 Minutes",
            "30m": "30 Minutes",
            "1h": "1 Hour",
            "6h": "6 Hours",
            "24h": "24 Hours",
            "3d": "3 Days",
            "7d": "7 Days",
            "30d": "30 Days"
        }
        return mapping[self.value]

    @property
    def days(self) -> float:
        return self.minutes / 1440.0

class ForecastType(str, Enum):
    EQUIPMENT_HEALTH = "EQUIPMENT_HEALTH"
    WORKER_SAFETY = "WORKER_SAFETY"
    HAZARD_EVOLUTION = "HAZARD_EVOLUTION"
    ENVIRONMENTAL_CONDITIONS = "ENVIRONMENTAL_CONDITIONS"
    OPERATIONAL_STABILITY = "OPERATIONAL_STABILITY"
    MAINTENANCE_DEMAND = "MAINTENANCE_DEMAND"
    RESOURCE_REQUIREMENTS = "RESOURCE_REQUIREMENTS"
    ENERGY_CONSUMPTION = "ENERGY_CONSUMPTION"
    PRODUCTION_IMPACT = "PRODUCTION_IMPACT"
    INCIDENT_PROBABILITY = "INCIDENT_PROBABILITY"
    EMERGENCY_READINESS = "EMERGENCY_READINESS"
    COMPLIANCE_TRENDS = "COMPLIANCE_TRENDS"
    PLANT_HEALTH = "PLANT_HEALTH"
    ZONE_HEALTH = "ZONE_HEALTH"
    ASSET_AVAILABILITY = "ASSET_AVAILABILITY"

class ForecastStatus(str, Enum):
    PENDING = "PENDING"
    COMPUTING = "COMPUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STALE = "STALE"

class ScenarioType(str, Enum):
    BEST_CASE = "BEST_CASE"
    EXPECTED_CASE = "EXPECTED_CASE"
    WORST_CASE = "WORST_CASE"

class ConfidenceLevel(str, Enum):
    VERY_LOW = "VERY_LOW"   # < 0.2
    LOW = "LOW"             # 0.2-0.4
    MEDIUM = "MEDIUM"       # 0.4-0.6
    HIGH = "HIGH"           # 0.6-0.8
    VERY_HIGH = "VERY_HIGH" # > 0.8
    
    @classmethod
    def from_score(cls, score: float) -> ConfidenceLevel:
        if score < 0.2:
            return cls.VERY_LOW
        elif score < 0.4:
            return cls.LOW
        elif score < 0.6:
            return cls.MEDIUM
        elif score < 0.8:
            return cls.HIGH
        return cls.VERY_HIGH

class ModelFamily(str, Enum):
    STATISTICAL = "STATISTICAL"
    NEURAL = "NEURAL"
    GRAPH = "GRAPH"
    BAYESIAN = "BAYESIAN"
    RULE_BASED = "RULE_BASED"
    ENSEMBLE = "ENSEMBLE"
    HYBRID = "HYBRID"

class ForecastTrend(str, Enum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DEGRADING = "DEGRADING"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"

class RecommendationType(str, Enum):
    PREVENTIVE_MAINTENANCE = "PREVENTIVE_MAINTENANCE"
    RESOURCE_ALLOCATION = "RESOURCE_ALLOCATION"
    WORKER_SCHEDULING = "WORKER_SCHEDULING"
    INSPECTION_PLANNING = "INSPECTION_PLANNING"
    EMERGENCY_READINESS = "EMERGENCY_READINESS"
    ENERGY_OPTIMIZATION = "ENERGY_OPTIMIZATION"
    SAFETY_IMPROVEMENT = "SAFETY_IMPROVEMENT"
    COMPLIANCE_ACTION = "COMPLIANCE_ACTION"
    OPERATIONAL_ADJUSTMENT = "OPERATIONAL_ADJUSTMENT"
    SHUTDOWN_PLANNING = "SHUTDOWN_PLANNING"

class ForecastTarget(str, Enum):
    EQUIPMENT = "EQUIPMENT"
    WORKER = "WORKER"
    ZONE = "ZONE"
    PLANT = "PLANT"
    RESOURCE = "RESOURCE"
    PROCESS = "PROCESS"
    ENVIRONMENT = "ENVIRONMENT"
    SYSTEM = "SYSTEM"

class UncertaintySource(str, Enum):
    DATA_SPARSITY = "DATA_SPARSITY"
    MODEL_UNCERTAINTY = "MODEL_UNCERTAINTY"
    ENVIRONMENTAL_VARIABILITY = "ENVIRONMENTAL_VARIABILITY"
    HUMAN_FACTOR = "HUMAN_FACTOR"
    SENSOR_NOISE = "SENSOR_NOISE"
    EXTERNAL_EVENT = "EXTERNAL_EVENT"

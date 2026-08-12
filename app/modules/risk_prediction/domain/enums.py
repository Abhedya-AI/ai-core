"""
app/modules/risk_prediction/domain/enums.py — Risk Prediction domain enumerations.

All enumerations used across the Predictive Risk Intelligence Platform.
str-based for JSON serialization consistency with the existing platform.
"""

from __future__ import annotations

from enum import Enum


class RiskLevel(str, Enum):
    """Risk severity classification.

    Maps to downstream actions:
      NEGLIGIBLE  → Log only
      LOW         → Dashboard notification
      MEDIUM      → Supervisor alert + monitoring increase
      HIGH        → Emergency notification + mitigation required
      CRITICAL    → Emergency response + supervisor escalation
      EXTREME     → Immediate evacuation + plant-wide alert
    """

    NEGLIGIBLE = "NEGLIGIBLE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EXTREME = "EXTREME"

    @classmethod
    def from_probability(cls, p: float) -> "RiskLevel":
        """Classify a raw probability into a RiskLevel."""
        if p < 0.10:
            return cls.NEGLIGIBLE
        elif p < 0.25:
            return cls.LOW
        elif p < 0.45:
            return cls.MEDIUM
        elif p < 0.65:
            return cls.HIGH
        elif p < 0.85:
            return cls.CRITICAL
        else:
            return cls.EXTREME


class RiskType(str, Enum):
    """Classification of risk event types."""

    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"
    WORKER_INJURY = "WORKER_INJURY"
    FIRE = "FIRE"
    GAS_LEAK = "GAS_LEAK"
    EXPLOSION = "EXPLOSION"
    ELECTRICAL_FAULT = "ELECTRICAL_FAULT"
    STRUCTURAL_FAILURE = "STRUCTURAL_FAILURE"
    CHEMICAL_SPILL = "CHEMICAL_SPILL"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    OPERATIONAL = "OPERATIONAL"
    COMPLIANCE = "COMPLIANCE"
    CYBER_PHYSICAL = "CYBER_PHYSICAL"
    COMPOSITE = "COMPOSITE"


class MitigationType(str, Enum):
    """Classification of recommended mitigation actions."""

    INSPECTION = "INSPECTION"
    SHUTDOWN = "SHUTDOWN"
    MAINTENANCE = "MAINTENANCE"
    WORKER_RELOCATION = "WORKER_RELOCATION"
    EVACUATION = "EVACUATION"
    PPE_RECOMMENDATION = "PPE_RECOMMENDATION"
    RESOURCE_ALLOCATION = "RESOURCE_ALLOCATION"
    MONITORING_INCREASE = "MONITORING_INCREASE"
    PROCESS_ADJUSTMENT = "PROCESS_ADJUSTMENT"
    EMERGENCY_RESPONSE = "EMERGENCY_RESPONSE"


class ForecastHorizon(str, Enum):
    """Prediction time horizon identifiers.

    Duration mapping:
      FIVE_MIN         → 5 minutes
      FIFTEEN_MIN      → 15 minutes
      THIRTY_MIN       → 30 minutes
      ONE_HOUR         → 60 minutes
      SIX_HOUR         → 360 minutes
      TWENTY_FOUR_HOUR → 1440 minutes
      SEVEN_DAY        → 10080 minutes
    """

    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN = "30m"
    ONE_HOUR = "1h"
    SIX_HOUR = "6h"
    TWENTY_FOUR_HOUR = "24h"
    SEVEN_DAY = "7d"

    @property
    def minutes(self) -> int:
        """Duration in minutes."""
        mapping = {
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "6h": 360,
            "24h": 1440,
            "7d": 10080,
        }
        return mapping[self.value]

    @property
    def label(self) -> str:
        """Human-readable label."""
        mapping = {
            "5m": "5 Minutes",
            "15m": "15 Minutes",
            "30m": "30 Minutes",
            "1h": "1 Hour",
            "6h": "6 Hours",
            "24h": "24 Hours",
            "7d": "7 Days",
        }
        return mapping[self.value]


class ModelType(str, Enum):
    """ML model backend identifiers."""

    RULE_BASED = "RULE_BASED"
    STATISTICAL = "STATISTICAL"
    XGBOOST = "XGBOOST"
    LIGHTGBM = "LIGHTGBM"
    RANDOM_FOREST = "RANDOM_FOREST"
    ISOLATION_FOREST = "ISOLATION_FOREST"
    BAYESIAN = "BAYESIAN"
    LSTM = "LSTM"
    TRANSFORMER = "TRANSFORMER"
    GNN = "GNN"
    ENSEMBLE = "ENSEMBLE"


class FeatureCategory(str, Enum):
    """Source category for risk features."""

    SENSOR = "SENSOR"
    VISION = "VISION"
    GRAPH = "GRAPH"
    GRAPHRAG = "GRAPHRAG"
    TEMPORAL = "TEMPORAL"
    HISTORICAL = "HISTORICAL"
    MAINTENANCE = "MAINTENANCE"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    OPERATIONAL = "OPERATIONAL"


class EntityType(str, Enum):
    """Target entity type for risk assessment."""

    ZONE = "ZONE"
    EQUIPMENT = "EQUIPMENT"
    WORKER = "WORKER"
    PLANT = "PLANT"
    PROCESS = "PROCESS"


class TrendDirection(str, Enum):
    """Risk trend direction."""

    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    VOLATILE = "VOLATILE"


class MitigationPriority(str, Enum):
    """Priority level for mitigation recommendations."""

    IMMEDIATE = "IMMEDIATE"
    URGENT = "URGENT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SCHEDULED = "SCHEDULED"


class AssessmentStatus(str, Enum):
    """Status of a risk assessment computation."""

    PENDING = "PENDING"
    COMPUTING = "COMPUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STALE = "STALE"

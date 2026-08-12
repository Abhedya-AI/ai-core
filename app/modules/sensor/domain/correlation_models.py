"""
sensor/domain/correlation_models.py — Correlation domain models.
"""
from __future__ import annotations
import uuid
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class CorrelationScope(str, Enum):
    """Scope of correlation evaluation."""
    SENSOR_PAIR = "SENSOR_PAIR"
    ZONE = "ZONE"
    EQUIPMENT = "EQUIPMENT"
    PLANT = "PLANT"
    GLOBAL = "GLOBAL"



class CorrelationStrength(str, Enum):
    """Strength of correlation based on Pearson's r."""
    STRONG = "STRONG"        # > 0.8
    MODERATE = "MODERATE"    # 0.5 - 0.8
    WEAK = "WEAK"            # 0.3 - 0.5
    NEGLIGIBLE = "NEGLIGIBLE" # < 0.3


class CorrelationPair(BaseModel):
    """A pair of sensors that are expected to be correlated."""
    model_config = ConfigDict(frozen=True)

    pair_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the pair")
    sensor_id_a: str = Field(description="ID of the first sensor")
    sensor_id_b: str = Field(description="ID of the second sensor")
    scope: CorrelationScope = Field(default=CorrelationScope.SENSOR_PAIR, description="Scope of the correlation")
    time_window_sec: int = Field(default=300, description="Time window in seconds to evaluate correlation")
    expected_correlation: float | None = Field(default=None, description="Expected Pearson correlation when healthy")
    enabled: bool = Field(default=True, description="Whether this correlation pair is actively monitored")


class CorrelationResult(BaseModel):
    """The result of calculating correlation between two sensors."""
    model_config = ConfigDict(frozen=True)

    pair_id: str = Field(description="ID of the correlation pair")
    sensor_id_a: str = Field(description="ID of the first sensor")
    sensor_id_b: str = Field(description="ID of the second sensor")
    pearson_r: float = Field(description="Calculated Pearson correlation coefficient")
    strength: CorrelationStrength = Field(description="Classified strength of the correlation")
    is_broken: bool = Field(description="True if correlation deviates significantly below expected")
    deviation_from_expected: float = Field(description="Difference between expected and calculated correlation")
    sample_count: int = Field(description="Number of samples used in the calculation")
    timestamp: str = Field(description="Calculation UTC timestamp")


class CorrelationAlert(BaseModel):
    """Alert triggered when expected correlation is broken."""
    model_config = ConfigDict()

    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the alert")
    pair_id: str = Field(description="ID of the correlation pair")
    result: CorrelationResult = Field(description="The underlying correlation result that caused the alert")
    severity: str = Field(description="Severity of the alert")
    description: str = Field(description="Description of the correlation break")
    recommended_action: str = Field(description="Action to take, e.g., inspect sensors")
    triggered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Trigger UTC timestamp")

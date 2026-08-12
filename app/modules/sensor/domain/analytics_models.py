"""
sensor/domain/analytics_models.py — Analytics domain models.
"""
from __future__ import annotations
import uuid
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class TrendDirection(str, Enum):
    """The direction of a data trend."""
    RISING = "RISING"
    FALLING = "FALLING"
    STABLE = "STABLE"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"


class MovingAverage(BaseModel):
    """Simple and Exponential Moving Average record."""
    model_config = ConfigDict(frozen=True)

    sensor_id: str = Field(description="ID of the sensor")
    window_size: int = Field(description="Size of the moving window")
    sma: float = Field(description="Simple Moving Average")
    ema: float = Field(description="Exponential Moving Average")
    timestamp: str = Field(description="Calculation UTC timestamp")


class PeakRecord(BaseModel):
    """Record of the highest and lowest values within a period."""
    model_config = ConfigDict(frozen=True)

    sensor_id: str = Field(description="ID of the sensor")
    peak_value: float = Field(description="Maximum value in the period")
    trough_value: float = Field(description="Minimum value in the period")
    peak_timestamp: str = Field(description="Timestamp of the peak")
    trough_timestamp: str = Field(description="Timestamp of the trough")
    range: float = Field(description="Difference between peak and trough")


class TrendAnalysis(BaseModel):
    """Analysis of a value trend over a window."""
    model_config = ConfigDict(frozen=True)

    sensor_id: str = Field(description="ID of the sensor")
    direction: TrendDirection = Field(description="Classified trend direction")
    slope: float = Field(description="Linear regression slope")
    r_squared: float = Field(description="Goodness of fit (0.0 to 1.0)")
    window_readings: int = Field(description="Number of readings analyzed")
    forecast_next_value: float = Field(description="Projected next value")
    timestamp: str = Field(description="Analysis UTC timestamp")


class SensorUptimeStats(BaseModel):
    """Uptime and statistical properties of a sensor's readings."""
    model_config = ConfigDict()

    sensor_id: str = Field(description="ID of the sensor")
    uptime_pct: float = Field(description="Percentage of time the sensor is active")
    total_readings: int = Field(description="Total number of readings in the period")
    anomalous_readings: int = Field(description="Number of anomalous readings in the period")
    anomaly_rate_pct: float = Field(description="Percentage of readings that are anomalous")
    mean_value: float = Field(description="Mean value of the readings")
    std_value: float = Field(description="Standard deviation of the readings")
    min_value: float = Field(description="Minimum reading value")
    max_value: float = Field(description="Maximum reading value")
    p95_value: float = Field(description="95th percentile value")
    p99_value: float = Field(description="99th percentile value")


class FailureProbability(BaseModel):
    """Estimated probability of failure and Remaining Useful Life (RUL)."""
    model_config = ConfigDict(frozen=True)

    sensor_id: str = Field(description="ID of the sensor")
    probability: float = Field(description="Probability of failure (0.0 to 1.0)")
    confidence: float = Field(description="Confidence in the probability (0.0 to 1.0)")
    contributing_factors: list[str] = Field(description="Factors contributing to this probability")
    estimated_rul_hours: float | None = Field(default=None, description="Estimated Remaining Useful Life in hours")
    maintenance_due: bool = Field(description="Whether maintenance is currently due based on probability")
    timestamp: str = Field(description="Calculation UTC timestamp")


class SensorAnalyticsReport(BaseModel):
    """Comprehensive analytical report for a sensor."""
    model_config = ConfigDict()

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the report")
    sensor_id: str = Field(description="ID of the sensor")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Generation UTC timestamp")
    period_hours: int = Field(description="Time period covered by the report in hours")
    moving_averages: MovingAverage = Field(description="Moving average metrics")
    peak: PeakRecord = Field(description="Peak and trough metrics")
    trend: TrendAnalysis = Field(description="Trend metrics")
    uptime: SensorUptimeStats = Field(description="Uptime and descriptive statistics")
    failure_probability: FailureProbability = Field(description="Predicted failure metrics")
    summary: str = Field(description="A human-readable summary of the report")

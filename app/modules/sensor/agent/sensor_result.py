from pydantic import Field
from app.modules.agents.core.agent_result import AgentResult
from app.modules.sensor.domain.models import SensorAnomaly, SensorHealthState

class SensorAgentResult(AgentResult):
    """Extended agent result with sensor-specific intelligence outputs."""
    anomalies: list[SensorAnomaly] = Field(default_factory=list)
    health_states: list[SensorHealthState] = Field(default_factory=list)
    threshold_violations: list[dict] = Field(default_factory=list)
    correlation_breaks: list[dict] = Field(default_factory=list)
    sensor_summary: dict = Field(default_factory=dict)
    fleet_health: dict = Field(default_factory=dict)

    @property
    def anomalies_detected(self) -> int:
        return len(self.anomalies)

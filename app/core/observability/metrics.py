"""
app/core/observability/metrics.py — Prometheus Metrics Exporter & Telemetry Collector.

Tracks agent execution metrics, risk score distributions, and system health counters.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class AgentMetricBucket:
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_latency_ms: float = 0.0

    def record(self, latency_ms: float, success: bool) -> None:
        self.total_executions += 1
        self.total_latency_ms += latency_ms
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.total_executions if self.total_executions > 0 else 0.0


class SystemMetricsRegistry:
    """Singleton registry for enterprise system metrics."""

    _instance: "SystemMetricsRegistry | None" = None

    def __init__(self) -> None:
        # agent_name → AgentMetricBucket
        self._agents: dict[str, AgentMetricBucket] = defaultdict(AgentMetricBucket)
        # severity → count
        self._risk_evaluations: dict[str, int] = defaultdict(int)

    @classmethod
    def get_instance(cls) -> "SystemMetricsRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_agent_execution(self, agent_name: str, latency_ms: float, success: bool = True) -> None:
        self._agents[agent_name].record(latency_ms, success)

    def record_risk_evaluation(self, severity: str) -> None:
        self._risk_evaluations[severity.upper()] += 1

    def to_prometheus(self) -> str:
        """Export metrics formatted for Prometheus scrapers."""
        lines = [
            "# HELP abhedya_agent_executions_total Total agent execution count",
            "# TYPE abhedya_agent_executions_total counter",
        ]
        for agent, bucket in self._agents.items():
            lines.append(f'abhedya_agent_executions_total{{agent="{agent}",status="success"}} {bucket.successful_executions}')
            lines.append(f'abhedya_agent_executions_total{{agent="{agent}",status="failed"}} {bucket.failed_executions}')

        lines.extend([
            "# HELP abhedya_agent_latency_ms Average agent execution latency in ms",
            "# TYPE abhedya_agent_latency_ms gauge",
        ])
        for agent, bucket in self._agents.items():
            lines.append(f'abhedya_agent_latency_ms{{agent="{agent}"}} {bucket.avg_latency_ms:.2f}')

        lines.extend([
            "# HELP abhedya_risk_evaluations_total Total risk evaluation events by severity",
            "# TYPE abhedya_risk_evaluations_total counter",
        ])
        for sev, count in self._risk_evaluations.items():
            lines.append(f'abhedya_risk_evaluations_total{{severity="{sev}"}} {count}')

        return "\n".join(lines)

    def summary(self) -> dict:
        return {
            "agents": {
                k: {
                    "total": v.total_executions,
                    "success": v.successful_executions,
                    "failed": v.failed_executions,
                    "avg_latency_ms": round(v.avg_latency_ms, 2),
                }
                for k, v in self._agents.items()
            },
            "risk_evaluations": dict(self._risk_evaluations),
        }

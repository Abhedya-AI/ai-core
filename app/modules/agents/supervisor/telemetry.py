"""telemetry.py — Supervisor Orchestration Telemetry Collector.

Captures performance metrics across workflow execution:
  - Planning time
  - Total execution time
  - Parallel efficiency ratio
  - Agent latencies
  - Retry & failure counts
"""

from typing import Any

from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.supervisor.models import SupervisorTelemetry


class TelemetryCollector:
    """Collects performance and execution metrics for Supervisor Agent runs."""

    def collect(
        self,
        workflow_id: str,
        planning_time_ms: int,
        execution_time_ms: int,
        results: list[AgentResult],
        stages_count: int,
        retries_count: int = 0,
        failures_count: int = 0,
        cache_hits: int = 0,
    ) -> SupervisorTelemetry:
        """
        Build SupervisorTelemetry object.

        Args:
            workflow_id: Workflow task ID.
            planning_time_ms: Milliseconds spent in planning engine.
            execution_time_ms: Total milliseconds spent executing stages.
            results: List of completed AgentResult objects.
            stages_count: Total stages in plan.
            retries_count: Retries count.
            failures_count: Failures count.
            cache_hits: Shared memory cache hits.

        Returns:
            SupervisorTelemetry object.
        """
        agent_latencies = {r.agent_name: r.execution_time_ms for r in results}
        sum_agent_time = sum(agent_latencies.values())

        # Parallel efficiency: sum of individual latencies vs actual wall-clock duration
        if execution_time_ms > 0 and sum_agent_time > 0:
            efficiency = min(round(sum_agent_time / execution_time_ms, 2), 5.0)
        else:
            efficiency = 1.0

        return SupervisorTelemetry(
            workflow_id=workflow_id,
            planning_time_ms=planning_time_ms,
            execution_time_ms=execution_time_ms,
            parallel_efficiency=min(efficiency, 1.0),
            agent_invocations=len(results),
            parallel_groups_count=stages_count,
            retries_count=retries_count,
            failures_count=failures_count,
            cache_hits=cache_hits,
            agent_latencies_ms=agent_latencies,
        )

"""memory.py — Shared Supervisor Execution Memory.

Caches graph snapshots, retrieved documents, vector embeddings, predictions,
risk assessments, and timelines across all workflow steps to eliminate redundant work.
"""

from typing import Any

from app.core.logging import get_logger

log = get_logger("agents.supervisor.memory")


class SupervisorExecutionMemory:
    """
    Central shared memory accessible to all pipeline stages during workflow execution.
    """

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        # Data caches
        self.graph_snapshots: list[dict[str, Any]] = []
        self.retrieved_documents: list[dict[str, Any]] = []
        self.embeddings_cache: dict[str, list[float]] = {}
        self.predictions_cache: list[dict[str, Any]] = []
        self.risk_assessments: list[dict[str, Any]] = []
        self.vision_observations: list[dict[str, Any]] = []
        self.timelines: list[dict[str, Any]] = []
        self.compliance_evaluations: list[dict[str, Any]] = []
        self.emergency_plans: list[dict[str, Any]] = []
        self.intermediate_outputs: dict[str, Any] = {}
        self.hits_count: int = 0

    def cache_output(self, agent_name: str, output_data: dict[str, Any]) -> None:
        """Store agent output in shared memory."""
        self.intermediate_outputs[agent_name] = output_data

        if "risk_score" in output_data:
            self.risk_assessments.append(output_data)
        if "predictions" in output_data or "failure_probability" in output_data:
            self.predictions_cache.append(output_data)
        if "vision_events" in output_data or "hazard_detected" in output_data:
            self.vision_observations.append(output_data)
        if "timeline" in output_data:
            self.timelines.append(output_data)
        if "violations" in output_data or "is_compliant" in output_data:
            self.compliance_evaluations.append(output_data)
        if "plan_id" in output_data or "execution_plan" in output_data:
            self.emergency_plans.append(output_data)

        log.debug(f"SupervisorExecutionMemory: cached output for '{agent_name}'")

    def get_output(self, agent_name: str) -> dict[str, Any] | None:
        """Retrieve cached output for an agent if available."""
        if agent_name in self.intermediate_outputs:
            self.hits_count += 1
            log.debug(f"SupervisorExecutionMemory: cache HIT for '{agent_name}'")
            return self.intermediate_outputs[agent_name]
        return None

    def build_snapshot(self) -> dict[str, Any]:
        """Build a serializable snapshot of the shared memory."""
        return {
            "task_id": self.task_id,
            "agents_executed": list(self.intermediate_outputs.keys()),
            "risk_assessments_count": len(self.risk_assessments),
            "predictions_count": len(self.predictions_cache),
            "vision_observations_count": len(self.vision_observations),
            "cache_hits": self.hits_count,
        }

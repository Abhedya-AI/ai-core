"""events.py — Supervisor Domain Event Generator.

Generates standardized domain events for the Supervisor workflow lifecycle:
  - WorkflowStarted
  - WorkflowUpdated
  - WorkflowCompleted
  - WorkflowFailed
  - HumanReviewRequested
  - AgentExecutionStarted
  - AgentExecutionCompleted
"""

from typing import Any

from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.supervisor.models import HITLCheckpoint, WorkflowState


class SupervisorEventGenerator:
    """Generates workflow lifecycle events for the EventBus."""

    @staticmethod
    def workflow_started(
        agent_name: str,
        workflow_id: str,
        intent: str,
        stages_count: int,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="WorkflowStarted",
            agent_name=agent_name,
            payload={
                "workflow_id": workflow_id,
                "intent": intent,
                "stages_count": stages_count,
            },
            trace_id=trace_id,
        )

    @staticmethod
    def workflow_updated(
        agent_name: str,
        workflow_id: str,
        state: WorkflowState,
        stage_name: str,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="WorkflowUpdated",
            agent_name=agent_name,
            payload={
                "workflow_id": workflow_id,
                "state": state.value,
                "current_stage": stage_name,
            },
            trace_id=trace_id,
        )

    @staticmethod
    def workflow_completed(
        agent_name: str,
        workflow_id: str,
        confidence: float,
        executed_agents: list[str],
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="WorkflowCompleted",
            agent_name=agent_name,
            payload={
                "workflow_id": workflow_id,
                "confidence": confidence,
                "executed_agents": executed_agents,
            },
            trace_id=trace_id,
        )

    @staticmethod
    def workflow_failed(
        agent_name: str,
        workflow_id: str,
        error_message: str,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="WorkflowFailed",
            agent_name=agent_name,
            payload={
                "workflow_id": workflow_id,
                "error": error_message,
            },
            trace_id=trace_id,
        )

    @staticmethod
    def human_review_requested(
        agent_name: str,
        checkpoint: HITLCheckpoint,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="HumanReviewRequested",
            agent_name=agent_name,
            payload={
                "checkpoint_id": checkpoint.checkpoint_id,
                "workflow_id": checkpoint.workflow_id,
                "stage_name": checkpoint.stage_name,
                "reason": checkpoint.reason,
                "required_role": checkpoint.required_role,
            },
            trace_id=trace_id,
        )

    @staticmethod
    def agent_execution_started(
        agent_name: str,
        workflow_id: str,
        target_agent: str,
        stage_name: str,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="AgentExecutionStarted",
            agent_name=agent_name,
            payload={
                "workflow_id": workflow_id,
                "target_agent": target_agent,
                "stage_name": stage_name,
            },
            trace_id=trace_id,
        )

    @staticmethod
    def agent_execution_completed(
        agent_name: str,
        workflow_id: str,
        target_agent: str,
        success: bool,
        trace_id: str,
    ) -> AgentDomainEvent:
        return AgentDomainEvent(
            event_type="AgentExecutionCompleted",
            agent_name=agent_name,
            payload={
                "workflow_id": workflow_id,
                "target_agent": target_agent,
                "success": success,
            },
            trace_id=trace_id,
        )

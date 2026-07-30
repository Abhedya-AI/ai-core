"""state_manager.py — Workflow State Manager.

Manages workflow state machine (QUEUED -> PLANNING -> RUNNING -> WAITING_FOR_APPROVAL -> COMPLETED/FAILED/CANCELLED).
Supports Human-in-the-Loop (HITL) pause/approval and dynamic replanning.
"""

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.agents.supervisor.models import HITLCheckpoint, WorkflowState

log = get_logger("agents.supervisor.state_manager")


class WorkflowStateManager:
    """
    Manages workflow lifecycle transitions and state persistence.
    """

    def __init__(self) -> None:
        # workflow_id → WorkflowState
        self._states: dict[str, WorkflowState] = {}
        # workflow_id → list[HITLCheckpoint]
        self._checkpoints: dict[str, list[HITLCheckpoint]] = {}
        # workflow_id → state history
        self._history: dict[str, list[dict[str, Any]]] = {}

    def transition_to(self, workflow_id: str, new_state: WorkflowState, reason: str = "") -> None:
        """Record a state transition for a workflow."""
        old_state = self._states.get(workflow_id, WorkflowState.QUEUED)
        self._states[workflow_id] = new_state

        entry = {
            "from": old_state.value,
            "to": new_state.value,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if workflow_id not in self._history:
            self._history[workflow_id] = []
        self._history[workflow_id].append(entry)

        log.info(f"WorkflowStateManager: '{workflow_id}' {old_state.value} → {new_state.value} ({reason})")

    def get_state(self, workflow_id: str) -> WorkflowState:
        """Get current state of a workflow."""
        return self._states.get(workflow_id, WorkflowState.QUEUED)

    # ------------------------------------------------------------------
    # Human-in-the-Loop (HITL) Checkpoints
    # ------------------------------------------------------------------

    def create_hitl_checkpoint(
        self,
        workflow_id: str,
        stage_name: str,
        reason: str = "High-impact response requires safety officer review.",
        required_role: str = "SAFETY_OFFICER",
    ) -> HITLCheckpoint:
        """Create an HITL checkpoint and pause workflow."""
        cp = HITLCheckpoint(
            workflow_id=workflow_id,
            stage_name=stage_name,
            reason=reason,
            required_role=required_role,
        )
        if workflow_id not in self._checkpoints:
            self._checkpoints[workflow_id] = []
        self._checkpoints[workflow_id].append(cp)

        self.transition_to(workflow_id, WorkflowState.WAITING_FOR_APPROVAL, f"HITL Checkpoint: {stage_name}")
        log.warning(f"HITL Checkpoint created: workflow_id='{workflow_id}', stage='{stage_name}'")
        return cp

    def approve_checkpoint(
        self,
        checkpoint_id: str,
        approved_by: str,
    ) -> bool:
        """Approve an HITL checkpoint to resume workflow."""
        for w_id, cps in self._checkpoints.items():
            for cp in cps:
                if cp.checkpoint_id == checkpoint_id:
                    cp.approved = True
                    cp.approved_by = approved_by
                    cp.approved_at = datetime.now(timezone.utc).isoformat()
                    self.transition_to(w_id, WorkflowState.RUNNING, f"Approved by {approved_by}")
                    log.info(f"HITL Checkpoint '{checkpoint_id}' APPROVED by '{approved_by}'")
                    return True
        return False

    def get_checkpoints(self, workflow_id: str) -> list[HITLCheckpoint]:
        """Return all HITL checkpoints for a workflow."""
        return self._checkpoints.get(workflow_id, [])

    def get_pending_checkpoints(self, workflow_id: str) -> list[HITLCheckpoint]:
        """Return pending unapproved HITL checkpoints."""
        return [cp for cp in self._checkpoints.get(workflow_id, []) if cp.approved is None]

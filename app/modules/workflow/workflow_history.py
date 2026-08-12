from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.logging import get_logger

log = get_logger("app.modules.workflow.workflow_history")

class WorkflowEvent(BaseModel):
    """Represents a single event in the workflow execution history."""
    execution_id: str
    step_id: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)

class WorkflowHistoryTracker:
    """Tracks and logs execution steps, status transitions, and outcomes."""

    def __init__(self) -> None:
        # In-memory store for demonstration; in production, use a database repository
        self._history: Dict[str, List[WorkflowEvent]] = {}

    async def log_event(self, execution_id: str, step_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a workflow execution event.
        
        Args:
            execution_id: The workflow execution ID.
            step_id: The specific step ID.
            status: Status of the step (e.g., STARTED, COMPLETED, FAILED).
            details: Additional execution context or results.
        """
        if execution_id not in self._history:
            self._history[execution_id] = []
            
        event = WorkflowEvent(
            execution_id=execution_id,
            step_id=step_id,
            status=status,
            details=details or {}
        )
        self._history[execution_id].append(event)
        log.info(f"[History] {execution_id} | Step: {step_id} | Status: {status}")

    async def get_history(self, execution_id: str) -> List[WorkflowEvent]:
        """
        Retrieve history for a specific execution.
        
        Args:
            execution_id: The workflow execution ID.
            
        Returns:
            List of workflow events.
        """
        return self._history.get(execution_id, [])

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum

class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class WorkflowContext(BaseModel):
    """Context holding the state of a workflow execution."""
    model_config = ConfigDict(populate_by_name=True)

    workflow_id: str = Field(..., description="ID of the workflow definition")
    execution_id: str = Field(..., description="Unique ID for this specific execution")
    plant_id: Optional[str] = Field(None, description="Plant ID context")
    zone_id: Optional[str] = Field(None, description="Zone ID context")
    trace_id: str = Field(..., description="Trace ID for distributed tracing")
    trigger_event: Optional[Dict[str, Any]] = Field(None, description="Event that triggered the workflow")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Workflow variables")
    step_outputs: Dict[str, Any] = Field(default_factory=dict, description="Outputs from completed steps")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="Current workflow status")
    started_at: Optional[datetime] = Field(None, description="Execution start time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
from app.core.logging import get_logger

log = get_logger(__name__)

class ExecutionRecord(BaseModel):
    """Record of a supervisor decision engine execution batch."""
    model_config = ConfigDict(from_attributes=True)
    
    execution_id: str = Field(description="Unique ID for the execution batch")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = Field(description="The type of event that triggered the execution")
    agent_results: Dict[str, Any] = Field(description="Results from individual agents")
    aggregated_status: str = Field(description="Final status of the decision engine")

class SupervisorExecutionHistory:
    """Records decision trails and agent execution logs."""
    
    def __init__(self) -> None:
        """Initialize the history record manager."""
        self._history: List[ExecutionRecord] = []

    async def record_execution(self, record: ExecutionRecord) -> None:
        """
        Save an execution record to the history.
        
        Args:
            record: The execution record to save.
        """
        self._history.append(record)
        log.info(f"Recorded execution {record.execution_id} with status {record.aggregated_status}")

    async def get_history(self, limit: int = 10) -> List[ExecutionRecord]:
        """
        Retrieve recent execution history.
        
        Args:
            limit: Maximum number of records to return.
            
        Returns:
            A list of execution records, ordered from most recent to oldest.
        """
        return sorted(self._history, key=lambda r: r.timestamp, reverse=True)[:limit]
        
    async def get_execution_by_id(self, execution_id: str) -> Optional[ExecutionRecord]:
        """
        Retrieve a specific execution record.
        
        Args:
            execution_id: The execution ID to search for.
            
        Returns:
            The execution record if found, else None.
        """
        for record in self._history:
            if record.execution_id == execution_id:
                return record
        return None

from typing import Dict, Any, Optional
import uuid
import asyncio
from datetime import datetime
from app.core.logging import get_logger
from app.modules.workflow.workflow_context import WorkflowContext, WorkflowStatus
from app.modules.workflow.workflow_validator import WorkflowValidator
from app.modules.workflow.workflow_registry import WorkflowRegistry
from app.modules.workflow.workflow_executor import WorkflowStepExecutor
from app.modules.workflow.workflow_history import WorkflowHistoryTracker
from app.modules.workflow.workflow_scheduler import WorkflowScheduler

log = get_logger("app.modules.workflow.workflow_engine")

class WorkflowEngine:
    """Main orchestrator coordinating validation, execution, context management, and history."""

    def __init__(self) -> None:
        self.registry = WorkflowRegistry()
        self.executor = WorkflowStepExecutor()
        self.history = WorkflowHistoryTracker()
        self.scheduler = WorkflowScheduler(self.trigger_workflow)
        self.active_contexts: Dict[str, WorkflowContext] = {}

    async def trigger_workflow(self, workflow_id: str, trigger_event: Optional[Dict[str, Any]] = None) -> WorkflowContext:
        """
        Trigger a workflow execution.
        
        Args:
            workflow_id: ID of the workflow definition.
            trigger_event: Event payload that triggered the workflow.
            
        Returns:
            The initialized WorkflowContext.
        """
        workflow_def = self.registry.get(workflow_id)
        if not workflow_def:
            raise ValueError(f"Workflow '{workflow_id}' not found in registry.")

        # Validate before execution
        await WorkflowValidator.validate(workflow_def)

        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        trace_id = f"trace_{uuid.uuid4().hex}"
        
        context = WorkflowContext(
            workflow_id=workflow_id,
            execution_id=execution_id,
            trace_id=trace_id,
            trigger_event=trigger_event or {},
            started_at=datetime.utcnow(),
            status=WorkflowStatus.RUNNING
        )
        
        self.active_contexts[execution_id] = context
        log.info(f"Starting execution {execution_id} for workflow {workflow_id}")
        
        # Execute in background (fire and forget for this example, though could be awaited)
        asyncio.create_task(self._execute_dag(workflow_def, context))
        
        return context

    async def _execute_dag(self, workflow_def: Dict[str, Any], context: WorkflowContext) -> None:
        """Internal method to execute the workflow DAG."""
        steps = workflow_def.get("steps", [])
        
        # Build dependency graph
        dependencies: Dict[str, set] = {step["id"]: set(step.get("depends_on", [])) for step in steps}
        completed: set = set()
        
        try:
            while len(completed) < len(steps):
                # Find ready steps (dependencies met and not yet completed)
                ready_steps = [
                    step for step in steps
                    if step["id"] not in completed and dependencies[step["id"]].issubset(completed)
                ]
                
                if not ready_steps:
                    raise RuntimeError("Deadlock detected or steps cannot be resolved.")

                # Execute ready steps sequentially for simplicity, but could be parallel
                for step in ready_steps:
                    step_id = step["id"]
                    await self.history.log_event(context.execution_id, step_id, "STARTED")
                    
                    result = await self.executor.execute_step(step, context)
                    
                    context.step_outputs[step_id] = result
                    context.updated_at = datetime.utcnow()
                    
                    await self.history.log_event(context.execution_id, step_id, "COMPLETED", result)
                    completed.add(step_id)

            context.status = WorkflowStatus.COMPLETED
            log.info(f"Execution {context.execution_id} completed successfully.")
        except Exception as e:
            context.status = WorkflowStatus.FAILED
            log.error(f"Execution {context.execution_id} failed: {str(e)}")
            await self.history.log_event(context.execution_id, "workflow", "FAILED", {"error": str(e)})
            
    async def get_execution_status(self, execution_id: str) -> Optional[WorkflowContext]:
        """Retrieve the current context of a workflow execution."""
        return self.active_contexts.get(execution_id)

from typing import Dict, Any, Callable
import asyncio
from app.core.logging import get_logger
from app.modules.workflow.workflow_context import WorkflowContext

log = get_logger("app.modules.workflow.workflow_executor")

class WorkflowStepExecutor:
    """Executes individual steps of a workflow."""

    def __init__(self) -> None:
        self.action_handlers: Dict[str, Callable] = {}

    def register_handler(self, action: str, handler: Callable) -> None:
        """Register an async handler for a specific action type."""
        self.action_handlers[action] = handler

    async def execute_step(self, step: Dict[str, Any], context: WorkflowContext) -> Dict[str, Any]:
        """
        Execute a single workflow step.
        
        Args:
            step: Step definition.
            context: Current workflow execution context.
            
        Returns:
            Dict containing step execution results.
        """
        step_id = step.get("id", "unknown")
        action = step.get("action", "unknown_action")
        step_type = step.get("type", "system")
        retries = step.get("retries", 0)
        timeout = step.get("timeout", 30)

        log.info(f"Executing step {step_id} of type {step_type} (action: {action}) in workflow {context.execution_id}")

        if step_type == "approval":
            log.info(f"Step {step_id} is pending human approval.")
            return {"status": "pending_approval", "action": action}

        handler = self.action_handlers.get(action)
        if not handler:
            log.warning(f"No handler registered for action '{action}'. Simulating success.")
            # Simulate a brief delay to represent async work
            await asyncio.sleep(0.1)
            return {"status": "success", "simulated": True, "action": action}

        attempt = 0
        while attempt <= retries:
            try:
                # Execute with timeout
                result = await asyncio.wait_for(handler(step, context), timeout=timeout)
                log.info(f"Step {step_id} executed successfully.")
                return {"status": "success", "result": result}
            except asyncio.TimeoutError:
                log.error(f"Step {step_id} timed out after {timeout} seconds.")
                attempt += 1
            except Exception as e:
                log.error(f"Error executing step {step_id}: {str(e)}")
                attempt += 1
                
        # Rollback logic could be invoked here
        rollback_action = step.get("rollback_action")
        if rollback_action:
            log.info(f"Invoking rollback for step {step_id} with action {rollback_action}")
            # Real implementation would call rollback handler
            
        raise RuntimeError(f"Step {step_id} failed after {retries} retries.")

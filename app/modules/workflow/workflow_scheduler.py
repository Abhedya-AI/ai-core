from typing import Dict, Any, Callable, Optional, Awaitable
import asyncio
from datetime import datetime
from app.core.logging import get_logger

log = get_logger("app.modules.workflow.workflow_scheduler")

class WorkflowScheduler:
    """Schedules recurring and event-triggered workflow runs."""

    def __init__(self, engine_dispatcher: Callable[[str, Optional[Dict[str, Any]]], Awaitable[Any]]) -> None:
        self.engine_dispatcher = engine_dispatcher
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}

    async def schedule_recurring(self, workflow_id: str, interval_seconds: int, payload: Optional[Dict[str, Any]] = None) -> str:
        """
        Schedule a workflow to run periodically.
        
        Args:
            workflow_id: ID of the workflow to run.
            interval_seconds: Delay between runs.
            payload: Optional variables to pass.
            
        Returns:
            Task ID for the scheduled job.
        """
        task_id = f"sched_{workflow_id}_{int(datetime.utcnow().timestamp())}"
        
        async def run_loop() -> None:
            log.info(f"Started recurring schedule {task_id} for workflow {workflow_id} every {interval_seconds}s")
            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    log.info(f"Triggering scheduled workflow {workflow_id}")
                    await self.engine_dispatcher(workflow_id, payload or {})
                except asyncio.CancelledError:
                    log.info(f"Scheduled task {task_id} cancelled.")
                    break
                except Exception as e:
                    log.error(f"Error in scheduled task {task_id}: {str(e)}")
                    
        task = asyncio.create_task(run_loop())
        self.scheduled_tasks[task_id] = task
        return task_id

    async def cancel_schedule(self, task_id: str) -> bool:
        """
        Cancel a scheduled recurring workflow.
        
        Args:
            task_id: The task ID to cancel.
            
        Returns:
            True if cancelled, False if not found.
        """
        task = self.scheduled_tasks.get(task_id)
        if task:
            task.cancel()
            del self.scheduled_tasks[task_id]
            return True
        return False

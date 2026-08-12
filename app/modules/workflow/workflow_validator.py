from typing import Dict, Any, List
from app.core.logging import get_logger

log = get_logger("app.modules.workflow.workflow_validator")

class WorkflowValidator:
    """Validates workflow DAG definitions, checks for cycles and valid dependencies."""

    @classmethod
    async def validate(cls, workflow_def: Dict[str, Any]) -> bool:
        """
        Validate a workflow definition for structural integrity.
        
        Args:
            workflow_def: The workflow definition dictionary.
            
        Returns:
            bool: True if valid, raises ValueError if invalid.
        """
        steps = workflow_def.get("steps", [])
        if not steps:
            raise ValueError("Workflow must contain at least one step.")
        
        step_ids = {step.get("id") for step in steps if step.get("id")}
        if len(step_ids) != len(steps):
            raise ValueError("All steps must have unique IDs.")

        # Detect cycles using Kahn's algorithm or DFS
        graph = {step["id"]: step.get("depends_on", []) for step in steps}
        
        visited = set()
        path = set()

        def visit(node: str) -> None:
            if node in path:
                raise ValueError(f"Cycle detected involving step {node}")
            if node in visited:
                return
            
            path.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in step_ids:
                    raise ValueError(f"Step {node} depends on non-existent step {neighbor}")
                visit(neighbor)
            path.remove(node)
            visited.add(node)

        for step_id in step_ids:
            visit(step_id)

        log.info(f"Workflow definition {workflow_def.get('id', 'unknown')} validated successfully.")
        return True

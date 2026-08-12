from typing import Dict, Any, Optional
from app.modules.workflow.workflow_templates import WorkflowTemplates
from app.core.logging import get_logger

log = get_logger("app.modules.workflow.workflow_registry")

class WorkflowRegistry:
    """Registry for managing and looking up workflow definitions."""

    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load pre-built templates into the registry."""
        templates = WorkflowTemplates.get_all()
        for key, template in templates.items():
            self.register(template["id"], template)
        log.info(f"Loaded {len(templates)} built-in workflow templates.")

    def register(self, workflow_id: str, workflow_def: Dict[str, Any]) -> None:
        """
        Register a new workflow definition.
        
        Args:
            workflow_id: Unique identifier for the workflow.
            workflow_def: The workflow definition dictionary.
        """
        self._registry[workflow_id] = workflow_def
        log.info(f"Workflow '{workflow_id}' registered successfully.")

    def get(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a workflow definition by ID.
        
        Args:
            workflow_id: The workflow ID.
            
        Returns:
            The workflow definition or None if not found.
        """
        return self._registry.get(workflow_id)
        
    def list_all(self) -> Dict[str, Dict[str, Any]]:
        """List all registered workflows."""
        return self._registry.copy()

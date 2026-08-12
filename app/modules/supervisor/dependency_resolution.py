from typing import Dict, List
from pydantic import BaseModel, Field
from app.core.logging import get_logger

log = get_logger(__name__)

class AgentDependency(BaseModel):
    """Model representing an agent dependency."""
    agent_id: str = Field(..., description="The ID of the dependent agent")
    depends_on: List[str] = Field(default_factory=list, description="List of agent IDs this agent depends on")

class DependencyResolver:
    """Resolves execution order and data dependencies between agents."""
    
    def __init__(self) -> None:
        """Initialize the dependency resolver."""
        self._dependencies: Dict[str, List[str]] = {}

    def register_dependency(self, agent_id: str, depends_on: List[str]) -> None:
        """
        Register a dependency for an agent.
        
        Args:
            agent_id: The ID of the agent.
            depends_on: The list of agent IDs that this agent depends on.
        """
        self._dependencies[agent_id] = depends_on

    def resolve_order(self, agents_to_run: List[str]) -> List[List[str]]:
        """
        Resolve the execution order based on dependencies.
        
        Args:
            agents_to_run: A list of agent IDs to execute.
            
        Returns:
            A list of execution batches, where agents in each batch can be run in parallel.
            
        Raises:
            ValueError: If cyclic dependencies are detected.
        """
        in_degree: Dict[str, int] = {agent: 0 for agent in agents_to_run}
        adj_list: Dict[str, List[str]] = {agent: [] for agent in agents_to_run}
        
        for agent in agents_to_run:
            deps = self._dependencies.get(agent, [])
            for dep in deps:
                if dep in agents_to_run:
                    adj_list[dep].append(agent)
                    in_degree[agent] += 1
                    
        batches: List[List[str]] = []
        queue = [agent for agent in agents_to_run if in_degree[agent] == 0]
        
        while queue:
            batch = queue.copy()
            batches.append(batch)
            queue = []
            for agent in batch:
                for neighbor in adj_list[agent]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
                        
        processed_count = sum(len(batch) for batch in batches)
        if processed_count < len(agents_to_run):
            log.error("Cycle detected in agent dependencies")
            raise ValueError("Cyclic dependencies detected in agent execution graph")
            
        return batches

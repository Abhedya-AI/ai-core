from typing import Dict, List, Set
from app.modules.agents.core.types import Capability

class CapabilityRegistry:
    """Registry to map capabilities to agents."""
    
    def __init__(self) -> None:
        """Initialize the capability registry."""
        self._capabilities: Dict[Capability, Set[str]] = {cap: set() for cap in Capability}
        self._agent_capabilities: Dict[str, Set[Capability]] = {}

    def register_agent(self, agent_id: str, capabilities: List[Capability]) -> None:
        """
        Register an agent with a set of capabilities.
        
        Args:
            agent_id: The unique identifier for the agent.
            capabilities: A list of capabilities the agent possesses.
        """
        if agent_id not in self._agent_capabilities:
            self._agent_capabilities[agent_id] = set()
            
        for cap in capabilities:
            self._capabilities[cap].add(agent_id)
            self._agent_capabilities[agent_id].add(cap)

    def get_agents_by_capability(self, capability: Capability) -> List[str]:
        """
        Get all agent IDs that have the given capability.
        
        Args:
            capability: The capability to search for.
            
        Returns:
            A list of agent IDs.
        """
        return list(self._capabilities.get(capability, set()))

    def get_agent_capabilities(self, agent_id: str) -> List[Capability]:
        """
        Get all capabilities for a given agent ID.
        
        Args:
            agent_id: The ID of the agent.
            
        Returns:
            A list of capabilities the agent possesses.
        """
        return list(self._agent_capabilities.get(agent_id, set()))

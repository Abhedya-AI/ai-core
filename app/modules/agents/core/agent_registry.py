"""agent_registry.py — Agent Discovery and Registry Management."""

from app.core.logging import get_logger
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.types import Capability

log = get_logger("agents.registry")


class AgentRegistry:
    """
    Central Agent Registry managing lookup by agent name and capability.
    """

    _instance: "AgentRegistry | None" = None

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    @classmethod
    def get_instance(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, agent: BaseAgent) -> None:
        """Register an agent instance."""
        self._agents[agent.name] = agent
        log.info(f"Registered Agent: '{agent.name}' (v{agent.version}) — Capabilities: {[c.value for c in agent.capabilities]}")

    def get(self, name: str) -> BaseAgent | None:
        """Get agent by name (case-insensitive)."""
        for k, v in self._agents.items():
            if k.lower() == name.lower() or k.lower().replace("agent", "") == name.lower():
                return v
        return None

    def find_by_capability(self, capability: Capability) -> list[BaseAgent]:
        """Find all registered agents possessing the specified capability."""
        return [a for a in self._agents.values() if capability in a.capabilities]

    def list_agents(self) -> list[BaseAgent]:
        """List all registered agent instances."""
        return list(self._agents.values())

    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()

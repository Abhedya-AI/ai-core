"""registry.py — Central Agent Registry singleton."""

from typing import Type

from app.core.logging import get_logger
from app.modules.agents.core.base_agent import BaseAgent

log = get_logger("agents.registry")


class AgentRegistry:
    """
    Central registry singleton for registering and looking up active AI Agents.
    """

    _instance: "AgentRegistry | None" = None

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    @classmethod
    def get(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, agent: BaseAgent) -> None:
        """Register an agent instance."""
        self._agents[agent.name] = agent
        log.info(f"Registered Agent: '{agent.name}' — {agent.description}")

    def get_agent(self, name: str) -> BaseAgent | None:
        """Get registered agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> list[BaseAgent]:
        """List all registered agent instances."""
        return list(self._agents.values())

    def clear(self) -> None:
        """Clear all registered agents (used in tests)."""
        self._agents.clear()

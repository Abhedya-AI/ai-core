"""registry_provider.py — Registry Provider Wrapper."""

from app.modules.agents.core.agent_registry import AgentRegistry
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.types import Capability


class RegistryProvider:
    """Wraps AgentRegistry access for Supervisor Agent."""

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or AgentRegistry.get_instance()

    def get_agent(self, name: str) -> BaseAgent | None:
        return self._registry.get(name)

    def find_by_capability(self, capability: Capability) -> list[BaseAgent]:
        return self._registry.find_by_capability(capability)

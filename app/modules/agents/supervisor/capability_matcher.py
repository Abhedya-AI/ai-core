"""capability_matcher.py — Dynamic Capability Matcher.

Queries AgentRegistry to dynamically match required Capability enums to registered BaseAgent instances.
Does NOT use hardcoded agent name strings (e.g. `if "risk"`).
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_registry import AgentRegistry
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.types import Capability

log = get_logger("agents.supervisor.capability_matcher")


class CapabilityMatcher:
    """
    Matches capability requirements to registered agents using AgentRegistry.
    Ensures extensibility: registering a new agent automatically makes it discoverable.
    """

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or AgentRegistry.get_instance()

    def match_capabilities(
        self,
        required_capabilities: list[Capability],
    ) -> dict[Capability, list[BaseAgent]]:
        """
        Find registered agents for each required capability.

        Args:
            required_capabilities: List of Capability enums.

        Returns:
            dict mapping each Capability to list of matching BaseAgent instances.
        """
        matched: dict[Capability, list[BaseAgent]] = {}

        for cap in required_capabilities:
            agents = self._registry.find_by_capability(cap)
            # Filter out SupervisorAgent itself from executing sub-tasks
            agents = [a for a in agents if a.name != "SupervisorAgent"]
            matched[cap] = agents
            log.debug(
                f"CapabilityMatcher: capability {cap.value} → "
                f"matched agents {[a.name for a in agents]}"
            )

        return matched

    def resolve_agent_names(
        self,
        required_capabilities: list[Capability],
    ) -> list[str]:
        """
        Resolve a deduplicated list of agent names covering all required capabilities.

        Args:
            required_capabilities: List of Capability enums.

        Returns:
            List of unique agent names.
        """
        matched_dict = self.match_capabilities(required_capabilities)
        agent_names: list[str] = []
        seen: set[str] = set()

        for agents in matched_dict.values():
            for agent in agents:
                if agent.name not in seen:
                    seen.add(agent.name)
                    agent_names.append(agent.name)

        return agent_names

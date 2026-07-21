"""lifecycle.py — Agent Execution Lifecycle State Tracker."""

from app.core.logging import get_logger
from app.modules.agents.core.types import AgentLifecycleState

log = get_logger("agents.lifecycle")


class LifecycleTracker:
    """Manages state transitions for agent execution lifecycle."""

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        self.state = AgentLifecycleState.INITIALIZED

    def transition_to(self, new_state: AgentLifecycleState) -> None:
        """Transition agent to a new lifecycle state."""
        log.info(f"Agent '{self.agent_name}' lifecycle state transition: {self.state.value} -> {new_state.value}")
        self.state = new_state

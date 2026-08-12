from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.events import AgentDomainEvent
from app.core.logging import get_logger

log = get_logger(__name__)

class AgentPriority(BaseModel):
    """Priority score for a resolved agent."""
    model_config = ConfigDict(frozen=True)
    
    agent_id: str = Field(description="ID of the agent")
    score: float = Field(description="Priority score")

class AgentRegistry:
    """Registry dynamically resolving and prioritizing agents based on event type."""
    
    def __init__(self) -> None:
        """Initialize the agent registry."""
        self._agents: Dict[str, BaseAgent] = {}
        self._event_subscriptions: Dict[str, List[str]] = {}

    def register(self, agent_id: str, agent: BaseAgent, event_types: List[str]) -> None:
        """
        Register an agent instance and its subscribed events.
        
        Args:
            agent_id: The ID of the agent.
            agent: The agent instance.
            event_types: The types of events the agent can handle.
        """
        self._agents[agent_id] = agent
        for event_type in event_types:
            if event_type not in self._event_subscriptions:
                self._event_subscriptions[event_type] = []
            if agent_id not in self._event_subscriptions[event_type]:
                self._event_subscriptions[event_type].append(agent_id)
                
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Retrieve an agent instance by ID.
        
        Args:
            agent_id: The ID of the agent to retrieve.
            
        Returns:
            The agent instance if found, None otherwise.
        """
        return self._agents.get(agent_id)
        
    def resolve_agents_for_event(self, event: AgentDomainEvent) -> List[AgentPriority]:
        """
        Resolve and prioritize agents based on event type and arbitrary confidence scores.
        
        Args:
            event: The domain event to resolve agents for.
            
        Returns:
            A list of agent priorities, sorted from highest to lowest score.
        """
        agent_ids = self._event_subscriptions.get(event.event_type, [])
        priorities = []
        for agent_id in agent_ids:
            score = 1.0
            agent = self._agents[agent_id]
            if hasattr(agent, "calculate_confidence"):
                try:
                    score_method = getattr(agent, "calculate_confidence")
                    score = score_method(event)
                except Exception as e:
                    log.warning(f"Failed to calculate confidence for agent {agent_id}: {e}")
                    score = 0.5
                    
            priorities.append(AgentPriority(agent_id=agent_id, score=score))
            
        priorities.sort(key=lambda p: p.score, reverse=True)
        return priorities

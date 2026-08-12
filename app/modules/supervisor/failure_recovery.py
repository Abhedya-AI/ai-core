from typing import Optional
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.base_agent import BaseAgent
from app.core.logging import get_logger

log = get_logger(__name__)

class FailureRecoveryManager:
    """Handles agent timeouts, errors, and fallbacks."""
    
    def __init__(self, max_retries: int = 3) -> None:
        """
        Initialize the recovery manager.
        
        Args:
            max_retries: Maximum number of retries before applying fallback.
        """
        self.max_retries = max_retries

    async def execute_with_recovery(self, agent: BaseAgent, context: AgentContext) -> AgentResult:
        """
        Execute an agent with built-in retry and fallback mechanisms.
        
        Args:
            agent: The agent to execute.
            context: The execution context.
            
        Returns:
            The agent result, possibly derived from a fallback.
        """
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                result = await agent.execute(context)
                if result.status != "error":
                    return result
                else:
                    last_error = result.error
                    log.warning(f"Agent {agent.name} failed with error: {last_error}, retrying ({retries}/{self.max_retries})")
            except Exception as e:
                last_error = str(e)
                log.warning(f"Agent {agent.name} threw exception: {last_error}, retrying ({retries}/{self.max_retries})")
            
            retries += 1
            
        log.error(f"Agent {agent.name} exhausted all retries. Last error: {last_error}")
        return self._apply_fallback(agent.name, last_error)

    def _apply_fallback(self, agent_id: str, error: Optional[str]) -> AgentResult:
        """
        Apply a fallback strategy when an agent completely fails.
        
        Args:
            agent_id: The ID of the failed agent.
            error: The final error encountered.
            
        Returns:
            A fallback AgentResult.
        """
        log.info(f"Applying fallback for agent {agent_id}")
        return AgentResult(
            agent_id=agent_id,
            status="error",
            data={"fallback_applied": True, "message": "Agent execution failed, using fallback data."},
            error=error or "Unknown error"
        )

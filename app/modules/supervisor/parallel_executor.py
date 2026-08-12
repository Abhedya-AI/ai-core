import asyncio
from typing import List, Dict, Tuple, Any
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.core.logging import get_logger

log = get_logger(__name__)

class ParallelAgentExecutor:
    """Dispatches multiple subagents concurrently via asyncio.gather."""
    
    def __init__(self, timeout: float = 30.0) -> None:
        """
        Initialize the parallel executor.
        
        Args:
            timeout: Maximum execution time per agent in seconds.
        """
        self.timeout = timeout

    async def execute(self, agents: List[BaseAgent], context: AgentContext) -> Dict[str, AgentResult]:
        """
        Execute a list of agents concurrently.
        
        Args:
            agents: A list of agents to execute.
            context: The execution context to pass to the agents.
            
        Returns:
            A dictionary mapping agent names to their execution results.
        """
        results: Dict[str, AgentResult] = {}
        
        async def run_agent(agent: BaseAgent) -> Tuple[str, AgentResult]:
            try:
                result = await asyncio.wait_for(agent.execute(context), timeout=self.timeout)
                return agent.name, result
            except asyncio.TimeoutError:
                log.error(f"Agent {agent.name} timed out after {self.timeout}s.")
                return agent.name, AgentResult(
                    agent_id=agent.name,
                    status="error",
                    data={},
                    error="TimeoutError"
                )
            except Exception as e:
                log.exception(f"Agent {agent.name} failed with error: {str(e)}")
                return agent.name, AgentResult(
                    agent_id=agent.name,
                    status="error",
                    data={},
                    error=str(e)
                )

        tasks = [run_agent(agent) for agent in agents]
        completed = await asyncio.gather(*tasks)
        
        for agent_name, result in completed:
            results[agent_name] = result
            
        return results

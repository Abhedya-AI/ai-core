import uuid
import asyncio
from typing import Dict, List, Any
from app.modules.supervisor.capability_registry import CapabilityRegistry
from app.modules.supervisor.agent_registry import AgentRegistry
from app.modules.supervisor.parallel_executor import ParallelAgentExecutor
from app.modules.supervisor.dependency_resolution import DependencyResolver
from app.modules.supervisor.response_aggregation import ResponseAggregator, AggregatedAssessment
from app.modules.supervisor.failure_recovery import FailureRecoveryManager
from app.modules.supervisor.execution_history import SupervisorExecutionHistory, ExecutionRecord
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.events import AgentDomainEvent
from app.core.logging import get_logger

log = get_logger(__name__)

class SupervisorDecisionEngine:
    """Main orchestrator for agent execution."""
    
    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        agent_registry: AgentRegistry,
        dependency_resolver: DependencyResolver,
        executor: ParallelAgentExecutor,
        aggregator: ResponseAggregator,
        recovery_manager: FailureRecoveryManager,
        history: SupervisorExecutionHistory
    ) -> None:
        """
        Initialize the Supervisor Decision Engine.
        """
        self.capability_registry = capability_registry
        self.agent_registry = agent_registry
        self.dependency_resolver = dependency_resolver
        self.executor = executor
        self.aggregator = aggregator
        self.recovery_manager = recovery_manager
        self.history = history

    async def process_event(self, event: AgentDomainEvent, context: AgentContext) -> AggregatedAssessment:
        """
        Process an incoming event by coordinating multiple agents.
        
        Args:
            event: The domain event that triggered the process.
            context: The execution context for the agents.
            
        Returns:
            An aggregated safety assessment.
        """
        execution_id = str(uuid.uuid4())
        log.info(f"Starting execution {execution_id} for event {event.event_type}")

        prioritized_agents = self.agent_registry.resolve_agents_for_event(event)
        if not prioritized_agents:
            log.warning(f"No agents resolved for event {event.event_type}")
            return AggregatedAssessment(status="unknown", critical_findings=["No agents available for event"])

        agent_ids = [p.agent_id for p in prioritized_agents]
        
        try:
            batches = self.dependency_resolver.resolve_order(agent_ids)
        except ValueError as e:
            log.error(f"Failed to resolve dependencies: {e}")
            return AggregatedAssessment(status="error", critical_findings=[str(e)])

        all_results = {}
        for batch in batches:
            agents_to_run = [self.agent_registry.get_agent(aid) for aid in batch if self.agent_registry.get_agent(aid) is not None]
            
            async def run_with_recovery(ag):
                return ag.name, await self.recovery_manager.execute_with_recovery(ag, context)
            
            tasks = [run_with_recovery(ag) for ag in agents_to_run]
            completed = await asyncio.gather(*tasks)
            
            for ag_id, res in completed:
                all_results[ag_id] = res
                context.update_state({f"{ag_id}_result": res.data})

        assessment = self.aggregator.aggregate(all_results)
        
        agent_results_dump = {}
        for k, v in all_results.items():
            if hasattr(v, "model_dump"):
                agent_results_dump[k] = v.model_dump()
            else:
                agent_results_dump[k] = v

        record = ExecutionRecord(
            execution_id=execution_id,
            event_type=event.event_type,
            agent_results=agent_results_dump,
            aggregated_status=assessment.status
        )
        await self.history.record_execution(record)
        
        return assessment

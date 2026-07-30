from unittest.mock import AsyncMock

import pytest

from app.modules.agents import (
    AgentContext,
    AgentDomainEvent,
    AgentExecutionMemory,
    AgentLifecycleState,
    AgentMemoryService,
    AgentOrchestrator,
    AgentRegistry,
    AgentResult,
    BaseAgent,
    Capability,
    ComplianceAgent,
    DocumentAgent,
    EmergencyAgent,
    ExecutionPlan,
    ExecutionStage,
    NonRetryableAgentException,
    NotificationAgent,
    PredictionAgent,
    RetryableAgentException,
    RiskAgent,
    RootCauseAgent,
    SupervisorAgent,
    VisionAgent,
)


class MockRetryableAgent(BaseAgent):
    """Test agent that fails twice with RetryableAgentException before succeeding."""

    name = "MockRetryableAgent"
    version = "1.0.0"
    description = "Fails then succeeds"
    capabilities = [Capability.RISK_ANALYSIS]
    max_retries = 2
    retry_backoff_sec = 0.01

    def __init__(self):
        super().__init__()
        self.attempts = 0

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        self.attempts += 1
        if self.attempts <= 2:
            raise RetryableAgentException("Transient LLM timeout")
        return AgentResult(agent_name=self.name, success=True, confidence=0.9)


class MockFailingAgent(BaseAgent):
    """Test agent that throws NonRetryableAgentException."""

    name = "MockFailingAgent"
    version = "1.0.0"
    description = "Deterministic failure"
    capabilities = [Capability.COMPLIANCE]

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        raise NonRetryableAgentException("Invalid entity ID format")


def test_agent_context_immutability():
    """Verify AgentContext is frozen/immutable."""
    ctx = AgentContext(query="A methane leak near Tank T-12", zone_id="Zone B")
    with pytest.raises(Exception):
        ctx.query = "Modified query"


def test_registry_capability_lookup():
    """Verify AgentRegistry supports discovery by capability and name."""
    registry = AgentRegistry()
    registry.clear()

    risk_agent = RiskAgent()
    vision_agent = VisionAgent()
    registry.register(risk_agent)
    registry.register(vision_agent)

    assert registry.get("RiskAgent") == risk_agent
    assert registry.get("risk") == risk_agent

    risk_capable = registry.find_by_capability(Capability.RISK_ANALYSIS)
    assert len(risk_capable) == 1
    assert risk_capable[0] == risk_agent


@pytest.mark.asyncio
async def test_agent_retries_and_lifecycle():
    """Verify BaseAgent exponential backoff retries and lifecycle state tracking."""
    agent = MockRetryableAgent()
    ctx = AgentContext(query="Test retry")

    result = await agent.execute(ctx)
    assert result.success is True
    assert agent.attempts == 3
    assert result.telemetry.retries_count == 2
    assert agent.lifecycle.state == AgentLifecycleState.COMPLETED


@pytest.mark.asyncio
async def test_non_retryable_failure():
    """Verify NonRetryableAgentException fails immediately without retrying."""
    agent = MockFailingAgent()
    ctx = AgentContext(query="Test failure")

    result = await agent.execute(ctx)
    assert result.success is False
    assert "Invalid entity ID format" in result.explanation
    assert agent.lifecycle.state == AgentLifecycleState.FAILED


@pytest.mark.asyncio
async def test_supervisor_and_orchestrator_end_to_end():
    """Verify end-to-end multi-stage parallel orchestration with memory and event publishing."""
    registry = AgentRegistry()
    registry.clear()

    registry.register(RiskAgent())
    registry.register(ComplianceAgent())
    registry.register(DocumentAgent())
    registry.register(EmergencyAgent())
    registry.register(NotificationAgent())

    # Pass the same populated registry so CapabilityMatcher can resolve agents
    supervisor = SupervisorAgent(registry=registry)
    ctx = AgentContext(query="Gas leak in Zone B", target_entity_id="TANK-T12", zone_id="ZONE-B")
    plan = await supervisor.create_plan(ctx)

    orchestrator = AgentOrchestrator(registry=registry)
    results, memory = await orchestrator.execute_plan(plan, ctx)

    # Gas leak → EMERGENCY_INVESTIGATION intent → 4+ agents (Risk, Emergency, Notification, ...)
    # Minimum: RiskAgent + NotificationAgent always present in any plan
    assert len(results) >= 2
    assert len(memory.intermediate_results) >= 2
    agent_names = [r.agent_name for r in results]
    assert "RiskAgent" in agent_names
    assert "NotificationAgent" in agent_names

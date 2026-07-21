from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.agents import (
    AgentContext,
    AgentMemoryService,
    AgentOrchestrator,
    AgentRegistry,
    AgentResult,
    ComplianceAgent,
    DocumentAgent,
    EmergencyAgent,
    NotificationAgent,
    PredictionAgent,
    RiskAgent,
    RootCauseAgent,
    SupervisorAgent,
    VisionAgent,
)


def test_agent_context_and_result_dtos():
    """Verify AgentContext and AgentResult DTOs."""
    ctx = AgentContext(query="A methane leak near Tank T-12", zone_id="Zone B")
    assert ctx.query == "A methane leak near Tank T-12"
    assert ctx.zone_id == "Zone B"
    assert ctx.task_id is not None

    res = AgentResult(
        agent_name="RiskAgent",
        success=True,
        confidence=0.95,
        evidence=["Risk propagated to 3 nodes"],
        recommendations=["Isolate Tank T-12"],
    )
    assert res.agent_name == "RiskAgent"
    assert res.success is True


@pytest.mark.asyncio
async def test_supervisor_planning():
    """Verify SupervisorAgent intent analysis and execution plan creation."""
    supervisor = SupervisorAgent()
    ctx = AgentContext(query="A methane leak has been detected near Tank T-12 in CCTV camera 1. What should we do?")
    plan = await supervisor.create_plan(ctx)

    assert len(plan.stages) >= 3
    assert "RiskAgent" in plan.stages[0].agent_names
    assert "VisionAgent" in plan.stages[0].agent_names
    assert "EmergencyAgent" in plan.stages[-2].agent_names
    assert "NotificationAgent" in plan.stages[-1].agent_names


@pytest.mark.asyncio
async def test_agent_orchestrator_execution():
    """Verify AgentOrchestrator runs registered agents across plan stages."""
    registry = AgentRegistry()
    registry.clear()

    risk_agent = RiskAgent()
    compliance_agent = ComplianceAgent()
    emergency_agent = EmergencyAgent()
    notification_agent = NotificationAgent()

    registry.register(risk_agent)
    registry.register(compliance_agent)
    registry.register(emergency_agent)
    registry.register(notification_agent)

    supervisor = SupervisorAgent()
    ctx = AgentContext(query="Gas leak in Zone B", target_entity_id="TANK-T12", zone_id="ZONE-B")
    plan = await supervisor.create_plan(ctx)

    orchestrator = AgentOrchestrator(registry=registry)
    results = await orchestrator.execute_plan(plan, ctx)

    assert len(results) >= 3
    agent_names = [r.agent_name for r in results]
    assert "RiskAgent" in agent_names
    assert "EmergencyAgent" in agent_names
    assert "NotificationAgent" in agent_names


@pytest.mark.asyncio
async def test_specialized_agents_execution():
    """Verify specialized agents return valid AgentResult outputs."""
    ctx = AgentContext(query="Analyze incident INC-01", target_entity_id="INC-01")

    # Risk Agent
    r_agent = RiskAgent()
    r_res = await r_agent.execute(ctx)
    assert r_res.success is True

    # Vision Agent
    v_agent = VisionAgent()
    v_ctx = AgentContext(query="Check camera CCTV-1", metadata={"camera_id": "CCTV-1", "detections": ["SMOKE"]})
    v_res = await v_agent.execute(v_ctx)
    assert v_res.success is True

    # Root Cause Agent
    rc_agent = RootCauseAgent()
    rc_res = await rc_agent.execute(ctx)
    assert rc_res.success is True

    # Compliance Agent
    c_agent = ComplianceAgent()
    c_res = await c_agent.execute(ctx)
    assert c_res.success is True


@pytest.mark.asyncio
async def test_agent_memory_service():
    """Verify AgentMemoryService stores and retrieves execution memory."""
    mock_cache = AsyncMock()
    mem_svc = AgentMemoryService(cache_service=mock_cache)

    result = AgentResult(agent_name="RiskAgent", success=True, confidence=0.9)
    await mem_svc.store_result("TASK-100", result)

    history = await mem_svc.get_task_history("TASK-100")
    assert len(history) == 1
    assert history[0]["agent_name"] == "RiskAgent"

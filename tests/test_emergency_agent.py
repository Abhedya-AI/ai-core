import pytest

from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.emergency import (
    EmergencyAgent,
    EmergencyAgentResult,
    EvacuationPlanner,
    HazardAwareRouter,
    IncidentAssessor,
    ResourceAllocator,
    SituationModelBuilder,
)


def test_assessor_routing_and_allocator():
    """Verify IncidentAssessor, HazardAwareRouter, and ResourceAllocator."""
    ctx = AgentContext(
        query="Emergency response in Zone B",
        target_entity_id="ZONE-B",
        metadata={
            "risk_output": {"risk_level": "CRITICAL", "hazards": ["FIRE", "GAS_LEAK"]},
            "compliance_violations": [{"type": "BLOCKED_EMERGENCY_EXIT", "location": "EXIT-A"}],
        },
    )

    state = IncidentAssessor.assess_incident(ctx)
    assert state.affected_zone == "ZONE-B"
    assert "EXIT-A" in state.blocked_exits

    situation = SituationModelBuilder.build_situation_model(state)
    assert situation.occupants == 12

    rec_exit, path = HazardAwareRouter.compute_safe_path("ZONE-B", state.blocked_exits)
    assert rec_exit != "EXIT-A"
    assert rec_exit in ("EXIT-C", "EXIT-D")

    resources = ResourceAllocator.allocate_resources(situation)
    types = [r.resource_type for r in resources]
    assert "FIRE_TEAM" in types
    assert "MEDICAL_TEAM" in types


@pytest.mark.asyncio
async def test_emergency_agent_end_to_end_execution():
    """Verify EmergencyAgent end-to-end execution returning EmergencyAgentResult."""
    agent = EmergencyAgent()
    ctx = AgentContext(
        query="What should we do right now for explosion incident in Zone B?",
        target_entity_id="ZONE-B",
        metadata={
            "risk_output": {"risk_level": "CRITICAL", "hazards": ["FIRE", "GAS_LEAK"]},
            "compliance_violations": [{"type": "BLOCKED_EMERGENCY_EXIT", "location": "EXIT-A"}],
        },
        vision_events=[{"camera_id": "CAM-01", "observation": "SMOKE_PLUME"}],
    )

    result = await agent.execute(ctx)
    assert isinstance(result, EmergencyAgentResult)
    assert result.success is True
    assert len(result.emergency_plan.actions) >= 6
    assert len(result.evacuation_routes) >= 1
    assert result.evacuation_routes[0].recommended_exit != "EXIT-A"
    assert len(result.resource_assignments) >= 2

    event_types = [e.event_type for e in result.events]
    assert "EmergencyPlanGenerated" in event_types
    assert "EvacuationInitiated" in event_types
    assert "ResourceAllocated" in event_types
    assert "Immediate (0-5 min)" in result.categorized_actions

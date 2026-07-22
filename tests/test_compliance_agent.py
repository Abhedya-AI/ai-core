import pytest

from app.modules.agents.compliance import (
    ComplianceAgent,
    ComplianceAgentResult,
    ComplianceCollector,
    PermitValidator,
    RuleEngine,
    SOPValidator,
    ViolationDetector,
)
from app.modules.agents.core.agent_context import AgentContext


def test_rule_engine_and_validators():
    """Verify RuleEngine, PermitValidator, and SOPValidator."""
    rule_engine = RuleEngine()
    rules = rule_engine.evaluate_rules("HOT_WORK")
    assert len(rules) >= 1

    permits = [{"permit_id": "PERMIT-HW-1", "expired": True, "gas_test_valid": False}]
    p_res = PermitValidator.validate_permits(permits)
    assert p_res["all_valid"] is False
    assert len(p_res["permit_violations"]) == 2

    sops = [{"sop_id": "SOP-LOTO-1", "required_sequence": ["Shutdown", "Lockout", "Verification"], "executed_sequence": ["Shutdown"]}]
    sop_res = SOPValidator.validate_sop_sequences(sops)
    assert sop_res["sequence_valid"] is False
    assert "Lockout" in sop_res["skipped_steps"]


@pytest.mark.asyncio
async def test_compliance_agent_end_to_end_execution():
    """Verify ComplianceAgent 8-phase end-to-end execution returning ComplianceAgentResult."""
    agent = ComplianceAgent()
    ctx = AgentContext(
        query="Is hot work operation compliant in Zone B?",
        target_entity_id="ZONE-B",
        metadata={
            "permits": [{"permit_id": "PERMIT-HOTWORK-102", "type": "HOT_WORK", "expired": True, "gas_test_valid": False}],
            "sops": [{"sop_id": "SOP-LOCKOUT-01", "required_sequence": ["Shutdown", "Lockout"], "executed_sequence": ["Shutdown"]}],
            "worker_certifications": [{"worker_id": "W-101", "certification": "CONFINED_SPACE", "valid": False}],
        },
        vision_events=[{"camera_id": "CAM-02", "observation": "BLOCKED_EMERGENCY_EXIT", "zone_id": "ZONE-C"}],
    )

    result = await agent.execute(ctx)
    assert isinstance(result, ComplianceAgentResult)
    assert result.success is True
    assert result.is_compliant is False
    assert result.compliance_score.overall_score < 75.0
    assert result.compliance_score.critical_violations_count >= 3

    event_types = [e.event_type for e in result.events]
    assert "PermitExpired" in event_types
    assert "SOPViolation" in event_types
    assert "CertificationMissing" in event_types
    assert "ComplianceAuditCompleted" in event_types
    assert "Immediate" in result.categorized_recommendations

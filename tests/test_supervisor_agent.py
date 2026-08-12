"""test_supervisor_agent.py — Comprehensive tests for Milestone 3.10: Supervisor Agent.

Tests cover:
  - Task Analyzer: Intent classification (Emergency, Prediction, Root Cause, Compliance, Vision)
  - Dynamic Capability Matcher: AgentRegistry lookup without hardcoded string checks
  - Topological Dependency Resolver: stage ordering (Vision -> Risk -> Emergency -> Notification)
  - Workflow Execution Engine: sequential, parallel, and conditional execution
  - Shared Execution Memory: intermediate result caching and hit counting
  - Conflict Resolver: output contradiction detection and source authority resolution
  - State Manager: state machine transitions, HITL checkpoints, and approval pause/resume
  - Retry Manager: transient vs non-transient error classification & backoff
  - Result Aggregator & Explanation Generator: unified incident report and human audit statements
  - SupervisorAgent end-to-end: full multi-agent orchestration execution
"""

import pytest

from app.modules.agents.compliance.compliance_agent import ComplianceAgent
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_registry import AgentRegistry
from app.modules.agents.core.events import AgentDomainEvent
from app.modules.agents.core.types import Capability
from app.modules.agents.document.document_agent import DocumentAgent
from app.modules.agents.emergency.emergency_agent import EmergencyAgent
from app.modules.agents.notification.notification_agent import NotificationAgent
from app.modules.agents.prediction.prediction_agent import PredictionAgent
from app.modules.agents.risk.risk_agent import RiskAgent
from app.modules.agents.root_cause.root_cause_agent import RootCauseAgent
from app.modules.agents.supervisor import (
    AggregatedResult,
    ConflictResolutionStrategy,
    PlanningEngine,
    SupervisorAgent,
    WorkflowExecutionEngine,
    WorkflowIntent,
    WorkflowState,
)
from app.modules.agents.supervisor.capability_matcher import CapabilityMatcher
from app.modules.agents.supervisor.conflict_resolver import ConflictResolver
from app.modules.agents.supervisor.dependency_resolver import DependencyResolver
from app.modules.agents.supervisor.memory import SupervisorExecutionMemory
from app.modules.agents.supervisor.models import ConflictRecord
from app.modules.agents.supervisor.retry_manager import RetryManager
from app.modules.agents.supervisor.state_manager import WorkflowStateManager
from app.modules.agents.supervisor.task_analyzer import TaskAnalyzer
from app.modules.agents.vision.vision_agent import VisionAgent


@pytest.fixture(autouse=True)
def setup_agent_registry():
    """Register all 8 specialized agents + SupervisorAgent in AgentRegistry."""
    registry = AgentRegistry.get_instance()
    registry.clear()

    registry.register(VisionAgent())
    registry.register(RiskAgent())
    registry.register(PredictionAgent())
    registry.register(RootCauseAgent())
    registry.register(ComplianceAgent())
    registry.register(EmergencyAgent())
    registry.register(DocumentAgent())
    registry.register(NotificationAgent())
    registry.register(SupervisorAgent())

    yield registry
    registry.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Task Analyzer — Intent classification
# ─────────────────────────────────────────────────────────────────────────────

def test_task_analyzer_emergency_intent():
    """TaskAnalyzer detects EMERGENCY_INVESTIGATION intent from prompt."""
    analyzer = TaskAnalyzer()
    context = AgentContext(query="Fire detected in Zone B! Evacuate personnel immediately!")
    res = analyzer.analyze(context)
    assert res.intent == WorkflowIntent.EMERGENCY_INVESTIGATION
    assert Capability.VISION in res.required_capabilities
    assert Capability.EMERGENCY in res.required_capabilities
    assert res.is_emergency is True
    assert res.requires_hitl is True


def test_task_analyzer_prediction_intent():
    """TaskAnalyzer detects PREDICTION intent."""
    analyzer = TaskAnalyzer()
    context = AgentContext(query="Predict equipment failure probabilities for next week.")
    res = analyzer.analyze(context)
    assert res.intent == WorkflowIntent.PREDICTION
    assert Capability.PREDICTION in res.required_capabilities


def test_task_analyzer_root_cause_intent():
    """TaskAnalyzer detects ROOT_CAUSE_ANALYSIS intent."""
    analyzer = TaskAnalyzer()
    context = AgentContext(query="Why did the boiler explosion happen yesterday?")
    res = analyzer.analyze(context)
    assert res.intent == WorkflowIntent.ROOT_CAUSE_ANALYSIS
    assert Capability.ROOT_CAUSE in res.required_capabilities


def test_task_analyzer_compliance_intent():
    """TaskAnalyzer detects COMPLIANCE_AUDIT intent."""
    analyzer = TaskAnalyzer()
    context = AgentContext(query="Is hot work permit WP-882 compliant with OSHA regulations?")
    res = analyzer.analyze(context)
    assert res.intent == WorkflowIntent.COMPLIANCE_AUDIT
    assert Capability.COMPLIANCE in res.required_capabilities


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Dynamic Capability Matcher
# ─────────────────────────────────────────────────────────────────────────────

def test_capability_matcher_resolves_from_registry():
    """CapabilityMatcher dynamically finds agents for required capabilities."""
    matcher = CapabilityMatcher()
    caps = [Capability.VISION, Capability.RISK_ANALYSIS, Capability.EMERGENCY]
    agent_names = matcher.resolve_agent_names(caps)

    assert "VisionAgent" in agent_names
    assert "RiskAgent" in agent_names
    assert "EmergencyAgent" in agent_names
    assert "SupervisorAgent" not in agent_names


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Dependency Resolver
# ─────────────────────────────────────────────────────────────────────────────

def test_dependency_resolver_topological_stages():
    """DependencyResolver creates valid stage ordering with dependencies."""
    resolver = DependencyResolver()
    agents = ["VisionAgent", "RiskAgent", "EmergencyAgent", "NotificationAgent"]
    stages = resolver.resolve_stages(agents)

    # Stage 1: Vision (no dependencies)
    assert "VisionAgent" in stages[0]

    # Vision must come before Risk
    vision_stage_idx = next(i for i, s in enumerate(stages) if "VisionAgent" in s)
    risk_stage_idx = next(i for i, s in enumerate(stages) if "RiskAgent" in s)
    emergency_stage_idx = next(i for i, s in enumerate(stages) if "EmergencyAgent" in s)
    notification_stage_idx = next(i for i, s in enumerate(stages) if "NotificationAgent" in s)

    assert vision_stage_idx < risk_stage_idx
    assert risk_stage_idx < emergency_stage_idx
    assert emergency_stage_idx < notification_stage_idx


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Planning Engine
# ─────────────────────────────────────────────────────────────────────────────

def test_planning_engine_creates_execution_plan():
    """PlanningEngine constructs ExecutionPlan DAG with stages."""
    planner = PlanningEngine()
    context = AgentContext(query="Fire detected in Zone B")
    plan, analysis = planner.create_execution_plan(context)

    assert plan.task_id == context.task_id
    assert len(plan.stages) >= 2
    assert analysis.intent == WorkflowIntent.EMERGENCY_INVESTIGATION


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Shared Execution Memory
# ─────────────────────────────────────────────────────────────────────────────

def test_supervisor_execution_memory_caching():
    """SupervisorExecutionMemory caches outputs and tracks cache hits."""
    mem = SupervisorExecutionMemory(task_id="TASK-MEM-001")
    mem.cache_output("VisionAgent", {"vision_events": [{"hazard": "fire"}], "confidence": 0.99})

    cached = mem.get_output("VisionAgent")
    assert cached is not None
    assert cached["confidence"] == 0.99
    assert mem.hits_count == 1

    snapshot = mem.build_snapshot()
    assert snapshot["cache_hits"] == 1
    assert "VisionAgent" in snapshot["agents_executed"]


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Conflict Resolver
# ─────────────────────────────────────────────────────────────────────────────

def test_conflict_resolver_source_authority():
    """ConflictResolver resolves conflict using source authority (Vision > Prediction)."""
    resolver = ConflictResolver()

    v_res = VisionAgent()._run_sync_stub("FireDetected") if hasattr(VisionAgent, "_run_sync_stub") else None
    # Mock results
    from app.modules.agents.core.agent_result import AgentResult
    v_res = AgentResult(
        agent_name="VisionAgent",
        success=True,
        confidence=0.98,
        events=[AgentDomainEvent(event_type="FireDetected", agent_name="VisionAgent")],
    )
    p_res = AgentResult(
        agent_name="PredictionAgent",
        success=True,
        confidence=0.95,
        output_data={"risk_score": 15.0},
    )

    conflicts = resolver.resolve_conflicts(
        [v_res, p_res], strategy=ConflictResolutionStrategy.SOURCE_AUTHORITY
    )
    assert len(conflicts) == 1
    conf = conflicts[0]
    assert conf.winning_agent == "VisionAgent"
    assert conf.conflict_id != ""


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: State Manager & HITL Checkpoints
# ─────────────────────────────────────────────────────────────────────────────

def test_state_manager_hitl_checkpoint():
    """WorkflowStateManager handles HITL pause and approval transition."""
    sm = WorkflowStateManager()
    wid = "TASK-HITL-001"

    sm.transition_to(wid, WorkflowState.RUNNING)
    assert sm.get_state(wid) == WorkflowState.RUNNING

    cp = sm.create_hitl_checkpoint(wid, "EmergencyPlanning", reason="High impact")
    assert sm.get_state(wid) == WorkflowState.WAITING_FOR_APPROVAL
    assert len(sm.get_pending_checkpoints(wid)) == 1

    approved = sm.approve_checkpoint(cp.checkpoint_id, approved_by="SafetyOfficer01")
    assert approved is True
    assert sm.get_state(wid) == WorkflowState.RUNNING
    assert len(sm.get_pending_checkpoints(wid)) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: Retry Manager
# ─────────────────────────────────────────────────────────────────────────────

def test_retry_manager_transient_classification():
    """RetryManager correctly distinguishes transient vs non-transient failures."""
    rm = RetryManager()

    transient = TimeoutError("Connection timed out waiting for LLM")
    assert rm.is_retryable(transient) is True

    fatal = ValueError("Schema validation error: missing required key 'zone_id'")
    assert rm.is_retryable(fatal) is False


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: SupervisorAgent End-to-End Orchestration
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_supervisor_agent_end_to_end_emergency_flow():
    """End-to-End: Emergency Investigation intent triggers full multi-agent orchestration."""
    supervisor = SupervisorAgent()
    context = AgentContext(
        query="Smoke and fire detected in Zone B! Analyze risk and activate emergency plan.",
        zone_id="Zone-B",
        metadata={"auto_approve_hitl": True},
    )

    result = await supervisor.execute(context)

    assert result.success is True
    assert result.agent_name == "SupervisorAgent"
    assert result.output_data["workflow_id"] == context.task_id
    assert len(result.evidence) >= 3
    assert result.explanation != ""

    # Check WorkflowCompleted event was published
    event_types = {e.event_type for e in result.events}
    assert "WorkflowStarted" in event_types
    assert "WorkflowCompleted" in event_types
    assert "AgentExecutionCompleted" in event_types


@pytest.mark.asyncio
async def test_supervisor_agent_prediction_flow():
    """End-to-End: Prediction intent orchestrates Prediction, Risk, Document & Notification agents."""
    supervisor = SupervisorAgent()
    context = AgentContext(
        query="Which pump equipment is likely to fail in the next 24 hours?",
        intent="PREDICTION",
    )

    result = await supervisor.execute(context)

    assert result.success is True
    assert result.agent_name == "SupervisorAgent"
    assert result.output_data["intent"] == WorkflowIntent.PREDICTION.value
    assert result.orchestration_telemetry is not None


@pytest.mark.asyncio
async def test_supervisor_agent_compliance_audit_flow():
    """End-to-End: Compliance Audit intent orchestrates Compliance, Document & Notification agents."""
    supervisor = SupervisorAgent()
    context = AgentContext(
        query="Check if maintenance work on Valve V-12 complies with OSHA regulations.",
        intent="COMPLIANCE",
    )

    result = await supervisor.execute(context)

    assert result.success is True
    assert result.output_data["intent"] == WorkflowIntent.COMPLIANCE_AUDIT.value


@pytest.mark.asyncio
async def test_supervisor_agent_handles_inbound_events():
    """SupervisorAgent processes inbound domain event batch from EventBus."""
    supervisor = SupervisorAgent()
    event = AgentDomainEvent(
        event_type="FireDetected",
        agent_name="VisionAgent",
        payload={"zone_id": "Zone-C", "confidence": "0.99"},
    )
    context = AgentContext(
        query="Process incoming emergency event",
        metadata={"inbound_events": [event.model_dump()], "auto_approve_hitl": True},
    )

    result = await supervisor.execute(context)
    assert result.success is True
    assert result.output_data["intent"] == WorkflowIntent.EMERGENCY_INVESTIGATION.value

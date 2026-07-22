"""
emergency_agent.py — Master Emergency Response Intelligence Agent.

Acts as the incident commander of ABHEDYA by generating dependency-aware response plans, dynamic evacuation routes, and responder resource allocations.
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.types import Capability
from app.modules.agents.emergency.confidence import EmergencyConfidenceEngine
from app.modules.agents.emergency.evacuation import EvacuationPlanner
from app.modules.agents.emergency.events import EmergencyEventGenerator
from app.modules.agents.emergency.explanation import EmergencyExplanationGenerator
from app.modules.agents.emergency.incident_assessor import IncidentAssessor
from app.modules.agents.emergency.models import EmergencyAgentResult, EmergencyPlan
from app.modules.agents.emergency.optimizer import EmergencyOptimizer
from app.modules.agents.emergency.planner import EmergencyPlanner
from app.modules.agents.emergency.prioritizer import EmergencyPrioritizer
from app.modules.agents.emergency.recommendation import EmergencyRecommendationEngine
from app.modules.agents.emergency.resource_allocator import ResourceAllocator
from app.modules.agents.emergency.responder import ResponderCoordinator
from app.modules.agents.emergency.situation_model import SituationModelBuilder

log = get_logger("agents.emergency.orchestrator")


class EmergencyAgent(BaseAgent):
    """
    Master Emergency Response Intelligence Agent.

    Orchestrates:
      Phase 1: Multi-Agent Incident Assessment
      Phase 2: Operational Situation Model Construction
      Phase 3: Dependency-Aware Emergency Action Planning
      Phase 4: Dynamic Graph-Based Evacuation Route Planning
      Phase 5: Responder Resource Allocation
      Phase 6: Life-Safety & Threat Prioritization
      Phase 7: Dynamic Replanning & Optimization
      Phase 8: Grounded XAI Explanation & Phase-Categorized Recommendations.
    """

    name: str = "EmergencyAgent"
    version: str = "1.0.0"
    description: str = "Acts as incident commander, producing dependency-aware action plans and evacuation routing."
    capabilities: list[Capability] = [Capability.EMERGENCY_RESPONSE]

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        log.info(f"Executing Emergency Response decision optimization for task '{context.task_id}'")

        # Phase 1: Incident Assessment
        incident_state = IncidentAssessor.assess_incident(context)

        # Phase 2: Situation Model Construction
        situation = SituationModelBuilder.build_situation_model(incident_state)

        # Phase 3: Emergency Action Planning
        raw_actions = EmergencyPlanner.plan_emergency_response(situation)

        # Phase 4: Evacuation Route Planning
        evac_routes = EvacuationPlanner.plan_evacuation(situation, incident_state.blocked_exits)

        # Phase 5: Resource Allocation
        resource_allocs = ResourceAllocator.allocate_resources(situation)

        # Phase 6: Prioritization
        ordered_actions = EmergencyPrioritizer.prioritize_actions(raw_actions, situation)

        # Build initial plan
        plan = EmergencyPlan(
            plan_id=f"PLAN-{situation.zone_id}",
            target_zone=situation.zone_id,
            actions=ordered_actions,
            evacuation_routes=evac_routes,
            resource_assignments=resource_allocs,
        )

        # Phase 7: Optimization (Re-planning check if new blocked exit present in context)
        new_blocked = context.metadata.get("newly_blocked_exit")
        if new_blocked:
            plan = EmergencyOptimizer.optimize_plan(plan, situation, new_blocked)

        # Phase 8: Explanation & Recommendations
        explanation = EmergencyExplanationGenerator.generate_explanation(plan, situation)
        flat_recs, categorized_recs = EmergencyRecommendationEngine.generate_recommendations(plan, situation)

        confidence = EmergencyConfidenceEngine.compute_confidence(situation)
        events = EmergencyEventGenerator.generate_events(self.name, plan, context.trace_id)

        evidence_items = [
            f"Assessed incident severity: {incident_state.severity} in {incident_state.affected_zone}",
            f"Threat score: {situation.overall_threat_score}/100 with {situation.occupants} occupants affected",
        ]
        evidence_items.extend(ResponderCoordinator.coordinate_dispatch(plan.resource_assignments))

        return EmergencyAgentResult(
            agent_name=self.name,
            success=True,
            confidence=confidence,
            evidence=evidence_items,
            recommendations=flat_recs,
            events=events,
            incident_state=incident_state,
            situation_model=situation,
            emergency_plan=plan,
            evacuation_routes=plan.evacuation_routes,
            resource_assignments=plan.resource_assignments,
            categorized_actions=categorized_recs,
            output_data={
                "incident_id": incident_state.incident_id,
                "target_zone": situation.zone_id,
                "action_count": len(plan.actions),
                "evacuation_exit": plan.evacuation_routes[0].recommended_exit if plan.evacuation_routes else "EXIT-C",
                "dispatched_teams": len(plan.resource_assignments),
                "categorized_actions": categorized_recs,
            },
            explanation=explanation,
        )

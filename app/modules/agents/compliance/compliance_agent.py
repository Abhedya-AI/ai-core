"""
compliance_agent.py — Master Compliance Intelligence Agent.

Evaluates operational governance, OSHA/ISO regulations, work permits, and SOP step sequence correctness.
"""

from app.core.logging import get_logger
from app.modules.agents.compliance.collector import ComplianceCollector
from app.modules.agents.compliance.confidence import ComplianceConfidenceEngine
from app.modules.agents.compliance.events import ComplianceEventGenerator
from app.modules.agents.compliance.explanation import ComplianceExplanationGenerator
from app.modules.agents.compliance.models import ComplianceAgentResult
from app.modules.agents.compliance.permit_validator import PermitValidator
from app.modules.agents.compliance.policy_engine import PolicyEngine
from app.modules.agents.compliance.recommendation import ComplianceRecommendationEngine
from app.modules.agents.compliance.regulation_matcher import RegulationMatcher
from app.modules.agents.compliance.rule_engine import RuleEngine
from app.modules.agents.compliance.scorer import ComplianceScorer
from app.modules.agents.compliance.sop_validator import SOPValidator
from app.modules.agents.compliance.violation_detector import ViolationDetector
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.types import Capability

log = get_logger("agents.compliance.orchestrator")


class ComplianceAgent(BaseAgent):
    """
    Master Compliance Intelligence Agent.

    Orchestrates:
      Phase 1: Multi-Source Evidence Collection
      Phase 2: Versioned Rule Engine Evaluation
      Phase 3: Permit Validation (expiry, gas tests, approvals)
      Phase 4: SOP Sequence Validation
      Phase 5: Dynamic Regulation Matching (OSHA, ISO, FS rules)
      Phase 6: Multi-Source Violation Detection
      Phase 7: Multi-Dimensional Compliance Scoring
      Phase 8: Grounded XAI Explanation & Categorized Action Recommendations.
    """

    name: str = "ComplianceAgent"
    version: str = "1.0.0"
    description: str = "Checks OSHA, ISO, and facility SOP regulatory compliance."
    capabilities: list[Capability] = [Capability.COMPLIANCE, Capability.DOCUMENT_SEARCH]

    def __init__(self) -> None:
        super().__init__()
        self.rule_engine = RuleEngine()

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        log.info(f"Running compliance evaluation for task '{context.task_id}'")

        # Phase 1: Evidence Collection
        evidence = ComplianceCollector.collect_evidence(context)

        # Phase 2: Rule Engine Evaluation
        rules = self.rule_engine.evaluate_rules(context.query)

        # Phase 3: Permit Validation
        permit_results = PermitValidator.validate_permits(evidence.permits)

        # Phase 4: SOP Sequence Validation
        sop_results = SOPValidator.validate_sop_sequences(evidence.sops)

        # Phase 5: Regulation Matching
        matched_regs = RegulationMatcher.match_regulations(context.query, [context.target_entity_id or "ENT-01"])

        # Phase 6: Violation Detection
        violations = ViolationDetector.detect_violations(evidence, permit_results, sop_results)

        # Phase 7: Multi-Dimensional Compliance Scoring
        score = ComplianceScorer.compute_score(violations)
        confidence = ComplianceConfidenceEngine.compute_confidence(evidence)
        score.confidence = confidence

        # Phase 8: Explanation & Recommendations
        explanation = ComplianceExplanationGenerator.generate_explanation(score, violations, matched_regs)
        flat_recs, categorized_recs = ComplianceRecommendationEngine.generate_recommendations(violations)

        is_authorized = PolicyEngine.evaluate_authorization(score, violations)

        # Domain Event Generation
        events = ComplianceEventGenerator.generate_events(
            agent_name=self.name,
            violations=violations,
            score=score,
            trace_id=context.trace_id,
        )

        evidence_items = [
            f"Evaluated {len(rules)} compliance rules across {len(matched_regs)} regulatory standards",
            f"Audit overall compliance score: {score.overall_score}/100",
        ]
        for v in violations:
            evidence_items.append(v.evidence_summary)

        return ComplianceAgentResult(
            agent_name=self.name,
            success=True,
            confidence=confidence,
            evidence=evidence_items,
            recommendations=flat_recs,
            events=events,
            compliance_score=score,
            is_compliant=is_authorized,
            violations=violations,
            permit_validation=permit_results,
            sop_validation=sop_results,
            categorized_recommendations=categorized_recs,
            referenced_regulations=matched_regs,
            output_data={
                "overall_score": score.overall_score,
                "is_authorized": is_authorized,
                "critical_violations": score.critical_violations_count,
                "violations_count": len(violations),
                "referenced_regulations": matched_regs,
                "categorized_recommendations": categorized_recs,
            },
            explanation=explanation,
        )

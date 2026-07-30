"""task_analyzer.py — Task Intent and Requirement Analyzer.

Extracts high-level WorkflowIntent, target entities, risk flags, and required capabilities
from user prompts or inbound domain events.
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.types import Capability
from app.modules.agents.supervisor.models import WorkflowIntent

log = get_logger("agents.supervisor.task_analyzer")


class TaskAnalysisResult:
    """Result of task intent and requirement analysis."""

    def __init__(
        self,
        intent: WorkflowIntent,
        required_capabilities: list[Capability],
        target_zone: str | None = None,
        target_entity_id: str | None = None,
        is_emergency: bool = False,
        requires_hitl: bool = False,
    ) -> None:
        self.intent = intent
        self.required_capabilities = required_capabilities
        self.target_zone = target_zone
        self.target_entity_id = target_entity_id
        self.is_emergency = is_emergency
        self.requires_hitl = requires_hitl


class TaskAnalyzer:
    """
    Analyzes task statement in AgentContext or inbound domain events
    to extract WorkflowIntent and required Capability set.
    """

    def analyze(self, context: AgentContext) -> TaskAnalysisResult:
        """
        Perform intent classification and capability requirement extraction.

        Args:
            context: Shared immutable AgentContext.

        Returns:
            TaskAnalysisResult with intent and required capabilities.
        """
        query_lower = (context.query or "").lower()
        intent_str = (context.intent or "").upper()
        metadata = context.metadata or {}
        inbound_events = metadata.get("inbound_events", [])

        # Check domain events first if present
        if inbound_events:
            first_evt = inbound_events[0]
            evt_type = first_evt.get("event_type", "") if isinstance(first_evt, dict) else getattr(first_evt, "event_type", "")
            if evt_type in ("FireDetected", "SmokeDetected", "EvacuationInitiated", "EmergencyPlanGenerated"):
                log.info(f"TaskAnalyzer: detected EMERGENCY intent from event '{evt_type}'")
                return TaskAnalysisResult(
                    intent=WorkflowIntent.EMERGENCY_INVESTIGATION,
                    required_capabilities=[
                        Capability.VISION,
                        Capability.RISK_ANALYSIS,
                        Capability.PREDICTION,
                        Capability.ROOT_CAUSE,
                        Capability.EMERGENCY,
                        Capability.NOTIFICATION,
                    ],
                    target_zone=context.zone_id or metadata.get("zone_id"),
                    is_emergency=True,
                    requires_hitl=True,
                )

        # Explicit context intent handling
        if intent_str in ("COMPLIANCE", "COMPLIANCE_AUDIT"):
            intent = WorkflowIntent.COMPLIANCE_AUDIT
            caps = [Capability.COMPLIANCE, Capability.DOCUMENT_SEARCH, Capability.RISK_ANALYSIS, Capability.NOTIFICATION]
            is_emergency, requires_hitl = False, False

        elif intent_str in ("PREDICTION", "PREDICTIVE"):
            intent = WorkflowIntent.PREDICTION
            caps = [Capability.PREDICTION, Capability.RISK_ANALYSIS, Capability.DOCUMENT_SEARCH, Capability.NOTIFICATION]
            is_emergency, requires_hitl = False, False

        elif intent_str in ("ROOT_CAUSE", "ROOT_CAUSE_ANALYSIS"):
            intent = WorkflowIntent.ROOT_CAUSE_ANALYSIS
            caps = [Capability.ROOT_CAUSE, Capability.RISK_ANALYSIS, Capability.DOCUMENT_SEARCH, Capability.GRAPH_SEARCH, Capability.NOTIFICATION]
            is_emergency, requires_hitl = False, False

        elif intent_str in ("EMERGENCY", "EMERGENCY_INVESTIGATION"):
            intent = WorkflowIntent.EMERGENCY_INVESTIGATION
            caps = [Capability.VISION, Capability.RISK_ANALYSIS, Capability.PREDICTION, Capability.ROOT_CAUSE, Capability.EMERGENCY, Capability.NOTIFICATION]
            is_emergency, requires_hitl = True, True

        # Query text keyword matching (order matters: Root Cause > Compliance > Emergency > Prediction)
        elif any(w in query_lower for w in ["why", "root cause", "reason", "why did"]):
            intent = WorkflowIntent.ROOT_CAUSE_ANALYSIS
            caps = [Capability.ROOT_CAUSE, Capability.RISK_ANALYSIS, Capability.DOCUMENT_SEARCH, Capability.GRAPH_SEARCH, Capability.NOTIFICATION]
            is_emergency, requires_hitl = False, False

        elif any(w in query_lower for w in ["compliance", "comply", "complies", "permit", "audit", "violation", "regulation", "osha"]):
            intent = WorkflowIntent.COMPLIANCE_AUDIT
            caps = [Capability.COMPLIANCE, Capability.DOCUMENT_SEARCH, Capability.RISK_ANALYSIS, Capability.NOTIFICATION]
            is_emergency, requires_hitl = False, False

        elif any(w in query_lower for w in ["fire", "smoke", "explosion", "emergency", "evacuate", "disaster", "gas leak", "gas", "leak", "toxic", "chemical spill", "spill", "hazmat"]):
            intent = WorkflowIntent.EMERGENCY_INVESTIGATION
            caps = [Capability.VISION, Capability.RISK_ANALYSIS, Capability.PREDICTION, Capability.ROOT_CAUSE, Capability.EMERGENCY, Capability.NOTIFICATION]
            is_emergency, requires_hitl = True, True

        elif any(w in query_lower for w in ["predict", "forecast", "fail", "failure", "health", "future"]):
            intent = WorkflowIntent.PREDICTION
            caps = [Capability.PREDICTION, Capability.RISK_ANALYSIS, Capability.DOCUMENT_SEARCH, Capability.NOTIFICATION]
            is_emergency, requires_hitl = False, False

        elif any(w in query_lower for w in ["see", "camera", "cctv", "vision", "video", "ppe", "detect"]):
            intent = WorkflowIntent.VISION_SURVEILLANCE
            caps = [Capability.VISION, Capability.RISK_ANALYSIS, Capability.NOTIFICATION]
            is_emergency, requires_hitl = False, False

        elif any(w in query_lower for w in ["sop", "manual", "document", "pdf", "search", "read"]):
            intent = WorkflowIntent.DOCUMENT_RESEARCH
            caps = [Capability.DOCUMENT_SEARCH, Capability.GRAPH_SEARCH]
            is_emergency, requires_hitl = False, False

        else:
            intent = WorkflowIntent.GENERAL_SAFETY
            caps = [Capability.RISK_ANALYSIS, Capability.DOCUMENT_SEARCH, Capability.NOTIFICATION]
            is_emergency, requires_hitl = False, False

        log.info(
            f"TaskAnalyzer: query='{context.query[:50]}' → intent={intent.value}, "
            f"capabilities={[c.value for c in caps]}"
        )

        return TaskAnalysisResult(
            intent=intent,
            required_capabilities=caps,
            target_zone=context.zone_id,
            target_entity_id=context.target_entity_id,
            is_emergency=is_emergency,
            requires_hitl=requires_hitl,
        )

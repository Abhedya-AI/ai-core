"""events.py — Standardized Compliance Domain Event Generator."""

from app.modules.agents.compliance.models import ComplianceScore, ComplianceViolation
from app.modules.agents.core.events import AgentDomainEvent


class ComplianceEventGenerator:
    """Generates standardized compliance domain events for the EventBus."""

    @staticmethod
    def generate_events(
        agent_name: str,
        violations: list[ComplianceViolation],
        score: ComplianceScore,
        trace_id: str,
    ) -> list[AgentDomainEvent]:
        """
        Generate compliance domain events.

        Returns:
            list of AgentDomainEvent objects (ComplianceViolationDetected, PermitExpired, SOPViolation, ComplianceAuditCompleted).
        """
        events: list[AgentDomainEvent] = []

        for v in violations:
            if v.violation_type == "EXPIRED_PERMIT":
                events.append(
                    AgentDomainEvent(
                        event_type="PermitExpired",
                        agent_name=agent_name,
                        payload=v.model_dump(),
                        trace_id=trace_id,
                    )
                )
            elif v.violation_type == "SOP_SEQUENCE_SKIPPED":
                events.append(
                    AgentDomainEvent(
                        event_type="SOPViolation",
                        agent_name=agent_name,
                        payload=v.model_dump(),
                        trace_id=trace_id,
                    )
                )
            elif v.violation_type == "MISSING_WORKER_CERTIFICATION":
                events.append(
                    AgentDomainEvent(
                        event_type="CertificationMissing",
                        agent_name=agent_name,
                        payload=v.model_dump(),
                        trace_id=trace_id,
                    )
                )
            else:
                events.append(
                    AgentDomainEvent(
                        event_type="ComplianceViolationDetected",
                        agent_name=agent_name,
                        payload=v.model_dump(),
                        trace_id=trace_id,
                    )
                )

        events.append(
            AgentDomainEvent(
                event_type="ComplianceAuditCompleted",
                agent_name=agent_name,
                payload={"overall_score": score.overall_score, "violations_count": len(violations)},
                trace_id=trace_id,
            )
        )
        return events

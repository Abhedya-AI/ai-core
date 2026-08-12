"""aggregator.py — Multi-Agent Result Aggregator.

Merges outputs from Vision, Risk, Prediction, Root Cause, Compliance, Emergency, Document, and Notification
into a single coherent AggregatedResult DTO.
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.supervisor.models import (
    AggregatedResult,
    ConflictRecord,
    HITLCheckpoint,
    WorkflowIntent,
)

log = get_logger("agents.supervisor.aggregator")


class ResultAggregator:
    """
    Merges intermediate agent outputs into a single unified report.
    """

    def aggregate(
        self,
        workflow_id: str,
        intent: WorkflowIntent,
        results: list[AgentResult],
        conflicts: list[ConflictRecord] | None = None,
        checkpoints: list[HITLCheckpoint] | None = None,
    ) -> AggregatedResult:
        """
        Synthesize individual AgentResult objects into an AggregatedResult report.

        Args:
            workflow_id: Workflow task ID.
            intent: Evaluated WorkflowIntent.
            results: List of completed AgentResult objects.
            conflicts: Optional list of resolved conflicts.
            checkpoints: Optional list of HITL checkpoints.

        Returns:
            AggregatedResult DTO.
        """
        result_map = {r.agent_name: r for r in results if r.success}

        # Calculate overall confidence as minimum or average of successful agent confidences
        confidences = [r.confidence for r in results if r.success]
        overall_conf = round(sum(confidences) / len(confidences), 4) if confidences else 1.0

        # Collect primary findings
        primary_findings: list[str] = []
        recommendations: list[str] = []
        document_evidence: list[str] = []

        for r in results:
            if r.success:
                primary_findings.extend(r.evidence[:2])
                recommendations.extend(r.recommendations[:2])

        # Vision summary
        vision_res = result_map.get("VisionAgent")
        vision_summary = vision_res.output_data if vision_res else {}

        # Risk summary
        risk_res = result_map.get("RiskAgent")
        risk_summary = risk_res.output_data if risk_res else {}

        # Prediction summary
        pred_res = result_map.get("PredictionAgent")
        prediction_summary = pred_res.output_data if pred_res else {}

        # Root Cause summary
        rc_res = result_map.get("RootCauseAgent")
        root_cause_summary = rc_res.output_data if rc_res else {}

        # Compliance summary
        comp_res = result_map.get("ComplianceAgent")
        compliance_summary = comp_res.output_data if comp_res else {}

        # Emergency plan summary
        em_res = result_map.get("EmergencyAgent")
        emergency_summary = em_res.output_data if em_res else {}

        # Document evidence
        doc_res = result_map.get("DocumentAgent")
        if doc_res:
            document_evidence = [c.get("doc_title", "Document") for c in doc_res.output_data.get("citations", [])]

        # Notifications dispatched
        notif_res = result_map.get("NotificationAgent")
        notifications_dispatched = notif_res.output_data.get("recipients", []) if notif_res else []

        log.info(f"ResultAggregator: aggregated {len(results)} agent outputs into unified report for task '{workflow_id}'")

        return AggregatedResult(
            workflow_id=workflow_id,
            intent=intent,
            overall_confidence=overall_conf,
            primary_findings=primary_findings,
            risk_summary=risk_summary,
            vision_summary=vision_summary,
            prediction_summary=prediction_summary,
            root_cause_summary=root_cause_summary,
            compliance_summary=compliance_summary,
            emergency_plan_summary=emergency_summary,
            notifications_dispatched=notifications_dispatched,
            document_evidence=document_evidence,
            recommendations=recommendations,
            conflicts_resolved=conflicts or [],
            hitl_checkpoints=checkpoints or [],
        )

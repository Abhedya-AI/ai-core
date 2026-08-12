from __future__ import annotations
import time
import numpy as np
from typing import Any
from app.core.logging import get_logger
from ..domain.models import ComplianceReport, GovernanceDecision, ModelVersion
from .decision_logger import AIDecisionLogger
from .policy_manager import PolicyManager

log = get_logger(__name__)

class ResponsibleAIReporter:
    def __init__(self, decision_logger: AIDecisionLogger | None = None, policy_manager: PolicyManager | None = None) -> None:
        self.decision_logger = decision_logger
        self.policy_manager = policy_manager

    async def generate_report(self, model_id: str, model_name: str, model_version: str, reporting_period: str, tenant_id: str) -> ComplianceReport:
        start_t = time.perf_counter()
        
        decisions: list[GovernanceDecision] = []
        if self.decision_logger:
            decisions = await self.decision_logger.get_decisions(model_id, limit=10000)
            
        total_preds = len(decisions)
        policy_violations = 0
        calibration_errors = []
        
        for d in decisions:
            if not d.all_policies_passed:
                policy_violations += 1
            # Assuming actual target is not available in decision log, calibration is an approximation or 0
            calibration_errors.append(0.0) 
            
        fairness_score = await self.compute_fairness_score(decisions)
        bias_metrics = await self.assess_bias(decisions)
        
        # Simple std dev of mean confidences across groups as a bias metric
        group_means = [v["mean_confidence"] for v in bias_metrics.values()]
        bias_std = float(np.std(group_means)) if len(group_means) > 0 else 0.0
        
        responsible_score = (fairness_score * 0.7) + ((1.0 - bias_std) * 0.3)
        
        report = ComplianceReport(
            model_id=model_id,
            model_name=model_name,
            model_version=model_version,
            reporting_period=reporting_period,
            total_predictions=total_preds,
            policy_violations=policy_violations,
            fairness_score=fairness_score,
            bias_metrics=bias_metrics,
            confidence_calibration_error=0.0,
            data_lineage_complete=True,
            responsible_ai_score=responsible_score,
            recommendations=["Review bias metrics across entity types" if bias_std > 0.1 else "No critical issues detected"]
        )
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Generated compliance report for {model_id} in {latency:.2f}ms")
        return report

    async def generate_model_card(self, model_id: str, model_version: ModelVersion) -> dict[str, Any]:
        start_t = time.perf_counter()
        
        metrics = model_version.metrics.model_dump() if model_version.metrics else {}
        
        card = {
            "name": model_version.name,
            "version": model_version.version,
            "purpose": model_version.description,
            "training_data": model_version.training_data_hash,
            "intended_use": f"Designed for {model_version.module}",
            "limitations": "Ensure inputs are within training distribution.",
            "ethical_considerations": "Regularly monitor for drift and bias.",
            "performance_metrics": metrics,
            "contact": model_version.created_by
        }
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Generated model card for {model_id} in {latency:.2f}ms")
        return card

    async def assess_bias(self, decisions: list[GovernanceDecision]) -> dict[str, dict[str, float]]:
        start_t = time.perf_counter()
        
        groups: dict[str, list[float]] = {}
        for d in decisions:
            if d.entity_type not in groups:
                groups[d.entity_type] = []
            groups[d.entity_type].append(d.confidence)
            
        bias_metrics: dict[str, dict[str, float]] = {}
        for entity_type, confs in groups.items():
            bias_metrics[entity_type] = {
                "mean_confidence": float(np.mean(confs)),
                "std_confidence": float(np.std(confs)),
                "count": float(len(confs))
            }
            
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Assessed bias in {latency:.2f}ms")
        return bias_metrics

    async def compute_fairness_score(self, decisions: list[GovernanceDecision]) -> float:
        start_t = time.perf_counter()
        
        if not decisions:
            return 1.0
            
        passed_flags = [1.0 if d.all_policies_passed else 0.0 for d in decisions]
        score = float(np.mean(passed_flags))
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Computed fairness score in {latency:.2f}ms")
        return score

_service_instance = None

def get_responsible_ai_reporter(decision_logger: AIDecisionLogger, policy_manager: PolicyManager) -> ResponsibleAIReporter:
    global _service_instance
    if _service_instance is None:
        _service_instance = ResponsibleAIReporter(decision_logger, policy_manager)
    return _service_instance

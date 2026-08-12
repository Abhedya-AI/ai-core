from __future__ import annotations
import time
from typing import Any
from app.core.logging import get_logger
from ..domain.models import GovernanceDecision

log = get_logger(__name__)

try:
    from app.modules.platform.services.audit_service import AuditService
except ImportError:
    AuditService = None  # type: ignore

class AIDecisionLogger:
    def __init__(self) -> None:
        self._decisions: dict[str, GovernanceDecision] = {}

    async def log_decision(
        self,
        model_id: str,
        model_name: str,
        model_version: str,
        entity_id: str,
        entity_type: str,
        decision_type: str,
        input_features: dict[str, Any],
        output: dict[str, Any],
        confidence: float,
        explanation: dict[str, Any],
        tenant_id: str,
        plant_id: str | None = None
    ) -> GovernanceDecision:
        start_t = time.perf_counter()
        
        policy_checks = self._check_policies(input_features, output, confidence)
        all_passed = all(check["passed"] for check in policy_checks)
        
        decision = GovernanceDecision(
            model_id=model_id,
            entity_id=entity_id,
            entity_type=entity_type,
            model_name=model_name,
            model_version=model_version,
            decision_type=decision_type,
            input_features=input_features,
            output=output,
            confidence=confidence,
            explanation=explanation,
            policy_checks=policy_checks,
            all_policies_passed=all_passed,
            tenant_id=tenant_id,
            plant_id=plant_id
        )
        self._decisions[decision.decision_id] = decision
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Decision logged: {decision.decision_id} in {latency:.2f}ms")
        return decision

    async def get_decisions(self, model_id: str, limit: int = 100, offset: int = 0) -> list[GovernanceDecision]:
        start_t = time.perf_counter()
        results = [d for d in self._decisions.values() if d.model_id == model_id]
        
        # sort by decided_at descending
        results.sort(key=lambda x: x.decided_at, reverse=True)
        results = results[offset:offset+limit]
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched {len(results)} decisions for {model_id} in {latency:.2f}ms")
        return results

    async def get_decision(self, decision_id: str) -> GovernanceDecision | None:
        start_t = time.perf_counter()
        res = self._decisions.get(decision_id)
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched decision {decision_id} in {latency:.2f}ms")
        return res

    async def get_decisions_requiring_review(self, model_id: str) -> list[GovernanceDecision]:
        start_t = time.perf_counter()
        results = [d for d in self._decisions.values() if d.model_id == model_id and d.requires_review]
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched {len(results)} review decisions for {model_id} in {latency:.2f}ms")
        return results

    def _check_policies(self, input_features: dict[str, Any], output: dict[str, Any], confidence: float) -> list[dict[str, Any]]:
        checks = []
        
        # Transparency policy
        passed_transparency = confidence >= 0.3
        checks.append({
            "policy": "TRANSPARENCY",
            "passed": passed_transparency,
            "reason": "Confidence threshold met" if passed_transparency else "Confidence below 0.3"
        })
        
        # Accountability policy
        passed_accountability = len(output.keys()) > 0
        checks.append({
            "policy": "ACCOUNTABILITY",
            "passed": passed_accountability,
            "reason": "Output keys present" if passed_accountability else "Missing output structure"
        })
        
        # Fairness policy
        passed_fairness = len(input_features.keys()) > 0
        checks.append({
            "policy": "FAIRNESS",
            "passed": passed_fairness,
            "reason": "Input features evaluated" if passed_fairness else "No input features provided"
        })
        
        return checks

_service_instance = None

def get_decision_logger() -> AIDecisionLogger:
    global _service_instance
    if _service_instance is None:
        _service_instance = AIDecisionLogger()
    return _service_instance

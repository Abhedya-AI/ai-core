from __future__ import annotations
import uuid
import time
from typing import Any
from datetime import datetime, timezone
from app.core.logging import get_logger
from ..domain.enums import GovernancePolicy

log = get_logger(__name__)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class PolicyManager:
    def __init__(self) -> None:
        self._policies: list[dict[str, Any]] = []

    async def add_policy(self, name: str, policy_type: GovernancePolicy, rule: dict[str, Any], threshold: float) -> str:
        start_t = time.perf_counter()
        
        policy_id = str(uuid.uuid4())
        policy = {
            "policy_id": policy_id,
            "name": name,
            "policy_type": policy_type,
            "rule": rule,
            "threshold": threshold,
            "created_at": _now_iso(),
            "is_active": True
        }
        self._policies.append(policy)
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Added policy {policy_id} in {latency:.2f}ms")
        return policy_id

    async def check_prediction(self, model_id: str, output: dict[str, Any], confidence: float, metadata: dict[str, Any]) -> dict[str, Any]:
        start_t = time.perf_counter()
        
        violations = []
        passed_count = 0
        total_active = 0
        
        for policy in self._policies:
            if not policy["is_active"]:
                continue
                
            total_active += 1
            rule = policy["rule"]
            metric = rule.get("metric")
            
            # Extract value to test
            test_value = None
            if metric == "confidence":
                test_value = confidence
            elif metric in output:
                test_value = output[metric]
            elif metric in metadata:
                test_value = metadata[metric]
                
            if test_value is None:
                continue
                
            passed = self._evaluate_rule(rule, test_value)
            if passed:
                passed_count += 1
            else:
                violations.append({
                    "policy_id": policy["policy_id"],
                    "policy_name": policy["name"],
                    "reason": f"Failed rule: {metric} {rule.get('operator')} {rule.get('value')} (actual: {test_value})"
                })
                
        score = passed_count / total_active if total_active > 0 else 1.0
        
        result = {
            "passed": len(violations) == 0,
            "violations": violations,
            "score": score
        }
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Checked policies for {model_id} in {latency:.2f}ms")
        return result

    async def list_policies(self, policy_type: GovernancePolicy | None = None) -> list[dict[str, Any]]:
        start_t = time.perf_counter()
        if policy_type:
            results = [p for p in self._policies if p["policy_type"] == policy_type]
        else:
            results = list(self._policies)
            
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Listed {len(results)} policies in {latency:.2f}ms")
        return results

    async def get_policy(self, policy_id: str) -> dict[str, Any] | None:
        start_t = time.perf_counter()
        for p in self._policies:
            if p["policy_id"] == policy_id:
                latency = (time.perf_counter() - start_t) * 1000
                log.info(f"Fetched policy {policy_id} in {latency:.2f}ms")
                return p
        return None

    async def update_policy(self, policy_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        start_t = time.perf_counter()
        for p in self._policies:
            if p["policy_id"] == policy_id:
                p.update(updates)
                p["updated_at"] = _now_iso()
                latency = (time.perf_counter() - start_t) * 1000
                log.info(f"Updated policy {policy_id} in {latency:.2f}ms")
                return p
        return None

    async def delete_policy(self, policy_id: str) -> bool:
        start_t = time.perf_counter()
        for i, p in enumerate(self._policies):
            if p["policy_id"] == policy_id:
                self._policies.pop(i)
                latency = (time.perf_counter() - start_t) * 1000
                log.info(f"Deleted policy {policy_id} in {latency:.2f}ms")
                return True
        return False

    def _evaluate_rule(self, rule: dict[str, Any], value: Any) -> bool:
        op = rule.get("operator")
        target = rule.get("value")
        
        try:
            if op == ">": return float(value) > float(target)
            if op == "<": return float(value) < float(target)
            if op == "==": return str(value) == str(target)
            if op == ">=": return float(value) >= float(target)
            if op == "<=": return float(value) <= float(target)
        except (ValueError, TypeError):
            pass
            
        return False

_service_instance = None

def get_policy_manager() -> PolicyManager:
    global _service_instance
    if _service_instance is None:
        _service_instance = PolicyManager()
    return _service_instance

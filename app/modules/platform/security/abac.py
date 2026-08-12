from __future__ import annotations

import time
import asyncio
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict
from app.core.logging import get_logger

log = get_logger(__name__)

class ABACPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)
    policy_id: str
    priority: int
    subjects: dict
    resources: dict
    actions: list[str]
    conditions: dict
    effect: str = "ALLOW"
    is_active: bool = True

class ABACPolicyEngine:
    def __init__(self) -> None:
        self._policies: list[ABACPolicy] = []

    async def evaluate(self, subject: dict, resource: dict, action: str, environment: dict = {}) -> dict:
        start_time = time.perf_counter()
        try:
            active_policies = sorted([p for p in self._policies if p.is_active], key=lambda x: x.priority)
            evaluated_count = 0

            for policy in active_policies:
                evaluated_count += 1
                if not self._matches_subject(policy, subject):
                    continue
                if not self._matches_resource(policy, resource):
                    continue
                if not self._matches_action(policy, action):
                    continue
                if not self._evaluate_conditions(policy, subject, resource, environment):
                    continue

                return {
                    "decision": policy.effect,
                    "matched_policy": policy.policy_id,
                    "reason": f"Matched policy {policy.policy_id} with effect {policy.effect}",
                    "evaluated_policies": evaluated_count
                }

            return {
                "decision": "DENY",
                "matched_policy": None,
                "reason": "Default deny, no policy matched",
                "evaluated_policies": evaluated_count
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"evaluate executed in {latency:.4f}s")

    async def add_policy(self, policy: ABACPolicy) -> None:
        start_time = time.perf_counter()
        try:
            self._policies.append(policy)
            self._policies.sort(key=lambda x: x.priority)
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"add_policy executed in {latency:.4f}s")

    async def remove_policy(self, policy_id: str) -> bool:
        start_time = time.perf_counter()
        try:
            initial_length = len(self._policies)
            self._policies = [p for p in self._policies if p.policy_id != policy_id]
            return len(self._policies) < initial_length
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"remove_policy executed in {latency:.4f}s")

    async def list_policies(self, active_only: bool = True) -> list[ABACPolicy]:
        start_time = time.perf_counter()
        try:
            if active_only:
                return [p for p in self._policies if p.is_active]
            return list(self._policies)
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"list_policies executed in {latency:.4f}s")

    async def get_policy(self, policy_id: str) -> ABACPolicy | None:
        start_time = time.perf_counter()
        try:
            for p in self._policies:
                if p.policy_id == policy_id:
                    return p
            return None
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_policy executed in {latency:.4f}s")

    def _matches_subject(self, policy: ABACPolicy, subject: dict) -> bool:
        p_sub = policy.subjects
        if not p_sub:
            return True
        if "user_id" in p_sub and p_sub["user_id"] != subject.get("user_id"):
            return False
        if "role" in p_sub and p_sub["role"] not in subject.get("roles", []):
            return False
        return True

    def _matches_resource(self, policy: ABACPolicy, resource: dict) -> bool:
        p_res = policy.resources
        if not p_res:
            return True
        p_type = p_res.get("resource_type")
        if p_type and p_type != "*" and p_type != resource.get("resource_type"):
            return False
        return True

    def _matches_action(self, policy: ABACPolicy, action: str) -> bool:
        if "*" in policy.actions:
            return True
        return action in policy.actions

    def _evaluate_conditions(self, policy: ABACPolicy, subject: dict, resource: dict, environment: dict) -> bool:
        conditions = policy.conditions
        if not conditions:
            return True

        if conditions.get("same_tenant") is True:
            if subject.get("tenant_id") != resource.get("tenant_id"):
                return False
                
        if conditions.get("same_plant") is True:
            if subject.get("plant_id") != resource.get("plant_id"):
                return False

        if "time_range" in conditions:
            hour = environment.get("hour_of_day", -1)
            tr = conditions["time_range"]
            if hour < tr.get("start", 0) or hour > tr.get("end", 24):
                return False

        if "ip_whitelist" in conditions:
            ip = environment.get("ip_address")
            if ip not in conditions["ip_whitelist"]:
                return False

        return True

    async def bulk_evaluate(self, requests: list[dict]) -> list[dict]:
        start_time = time.perf_counter()
        try:
            tasks = [
                self.evaluate(
                    req.get("subject", {}),
                    req.get("resource", {}),
                    req.get("action", ""),
                    req.get("environment", {})
                )
                for req in requests
            ]
            return await asyncio.gather(*tasks)
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"bulk_evaluate executed in {latency:.4f}s for {len(requests)} requests")

_service_instance = None
def get_service() -> ABACPolicyEngine:
    global _service_instance
    if _service_instance is None:
        _service_instance = ABACPolicyEngine()
    return _service_instance

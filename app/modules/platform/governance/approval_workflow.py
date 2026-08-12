from __future__ import annotations
import time
from typing import Any
from datetime import datetime, timezone
from app.core.logging import get_logger

log = get_logger(__name__)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ModelApprovalWorkflow:
    def __init__(self) -> None:
        # State machine: DRAFT → REVIEW → APPROVED/REJECTED, APPROVED → DEPLOYED → RETIRED
        # model_id -> workflow state dict
        self._store: dict[str, dict[str, Any]] = {}

    async def submit_for_review(self, model_id: str, submitted_by: str, justification: str) -> dict[str, Any]:
        start_t = time.perf_counter()
        
        state = {
            "model_id": model_id,
            "status": "PENDING",
            "submitted_by": submitted_by,
            "submitted_at": _now_iso(),
            "justification": justification,
            "approvals": [],
            "rejections": []
        }
        self._store[model_id] = state
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Submitted {model_id} for review in {latency:.2f}ms")
        return state

    async def approve(self, model_id: str, approver_id: str, comments: str) -> dict[str, Any] | None:
        start_t = time.perf_counter()
        
        state = self._store.get(model_id)
        if not state:
            log.warning(f"No workflow found for {model_id}")
            return None
            
        if not self._valid_transition(state["status"], "APPROVED"):
            log.warning(f"Invalid transition from {state['status']} to APPROVED")
            return state
            
        state["approvals"].append({
            "approver_id": approver_id,
            "comments": comments,
            "approved_at": _now_iso()
        })
        
        if len(state["approvals"]) >= 2:
            state["status"] = "APPROVED"
            
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Approved {model_id} by {approver_id} in {latency:.2f}ms")
        return state

    async def reject(self, model_id: str, rejector_id: str, reason: str) -> dict[str, Any] | None:
        start_t = time.perf_counter()
        
        state = self._store.get(model_id)
        if not state:
            return None
            
        if not self._valid_transition(state["status"], "REJECTED"):
            return state
            
        state["rejections"].append({
            "rejector_id": rejector_id,
            "reason": reason,
            "rejected_at": _now_iso()
        })
        state["status"] = "REJECTED"
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Rejected {model_id} by {rejector_id} in {latency:.2f}ms")
        return state

    async def get_workflow(self, model_id: str) -> dict[str, Any] | None:
        start_t = time.perf_counter()
        res = self._store.get(model_id)
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched workflow for {model_id} in {latency:.2f}ms")
        return res

    async def list_pending(self, tenant_id: str) -> list[dict[str, Any]]:
        # For simplicity, assuming all in store belong to tenant_id if we aren't tracking it explicitly
        start_t = time.perf_counter()
        results = [w for w in self._store.values() if w["status"] == "PENDING"]
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Listed {len(results)} pending workflows in {latency:.2f}ms")
        return results

    async def revoke(self, model_id: str, revoked_by: str, reason: str) -> dict[str, Any] | None:
        start_t = time.perf_counter()
        
        state = self._store.get(model_id)
        if not state:
            return None
            
        if state["status"] not in ["APPROVED", "DEPLOYED"]:
            return state
            
        state["status"] = "REVIEW" # Reverts to review conceptually
        state["revoked_by"] = revoked_by
        state["revoke_reason"] = reason
        state["revoked_at"] = _now_iso()
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Revoked {model_id} by {revoked_by} in {latency:.2f}ms")
        return state

    def _valid_transition(self, from_status: str, to_status: str) -> bool:
        valid_transitions = {
            "PENDING": ["APPROVED", "REJECTED"],
            "APPROVED": ["REJECTED", "DEPLOYED"],
            "DEPLOYED": ["RETIRED"]
        }
        return to_status in valid_transitions.get(from_status, [])

_service_instance = None

def get_approval_workflow() -> ModelApprovalWorkflow:
    global _service_instance
    if _service_instance is None:
        _service_instance = ModelApprovalWorkflow()
    return _service_instance

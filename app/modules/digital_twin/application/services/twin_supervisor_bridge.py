from __future__ import annotations

import time
import asyncio
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.modules.supervisor.services.supervisor_service import SupervisorService
except ImportError:
    SupervisorService = None


class TwinSupervisorBridge:
    def __init__(self) -> None:
        if SupervisorService:
            self._supervisor = SupervisorService()
        else:
            self._supervisor = None

    async def notify_state_changed(
        self, twin_id: str, entity_id: str, old_status: str, new_status: str, risk_score: float
    ) -> None:
        t0 = time.perf_counter()
        if not self._supervisor:
            log.warning("SupervisorService not available, skipping notify_state_changed")
            return

        try:
            if risk_score > 0.8 or new_status in ["CRITICAL", "FAILED"]:
                await self._supervisor.notify(
                    event_type="TWIN_STATE_CRITICAL",
                    payload={
                        "twin_id": twin_id,
                        "entity_id": entity_id,
                        "old_status": old_status,
                        "new_status": new_status,
                        "risk_score": risk_score,
                        "timestamp": time.time(),
                    },
                )
        except Exception as e:
            log.warning(f"Failed to notify supervisor of state change: {e}")
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"notify_state_changed completed in {latency_ms:.2f}ms")

    async def notify_simulation_completed(
        self, twin_id: str, simulation_id: str, simulation_type: str, has_critical_findings: bool
    ) -> None:
        t0 = time.perf_counter()
        if not self._supervisor:
            log.warning("SupervisorService not available, skipping notify_simulation_completed")
            return

        try:
            if has_critical_findings:
                await self._supervisor.notify(
                    event_type="TWIN_SIMULATION_CRITICAL_FINDINGS",
                    payload={
                        "twin_id": twin_id,
                        "simulation_id": simulation_id,
                        "simulation_type": simulation_type,
                        "timestamp": time.time(),
                    },
                )
        except Exception as e:
            log.warning(f"Failed to notify supervisor of simulation completion: {e}")
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"notify_simulation_completed completed in {latency_ms:.2f}ms")

    async def notify_optimization_completed(
        self, twin_id: str, optimization_id: str, target: str, improvement_score: float
    ) -> None:
        t0 = time.perf_counter()
        if not self._supervisor:
            log.warning("SupervisorService not available, skipping notify_optimization_completed")
            return

        try:
            await self._supervisor.notify(
                event_type="TWIN_OPTIMIZATION_COMPLETED",
                payload={
                    "twin_id": twin_id,
                    "optimization_id": optimization_id,
                    "target": target,
                    "improvement_score": improvement_score,
                    "timestamp": time.time(),
                },
            )
        except Exception as e:
            log.warning(f"Failed to notify supervisor of optimization completion: {e}")
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"notify_optimization_completed completed in {latency_ms:.2f}ms")

    async def notify_planning_generated(
        self, twin_id: str, plan_id: str, plan_type: str, urgency: str
    ) -> None:
        t0 = time.perf_counter()
        if not self._supervisor:
            log.warning("SupervisorService not available, skipping notify_planning_generated")
            return

        try:
            await self._supervisor.notify(
                event_type="TWIN_PLAN_GENERATED",
                payload={
                    "twin_id": twin_id,
                    "plan_id": plan_id,
                    "plan_type": plan_type,
                    "urgency": urgency,
                    "timestamp": time.time(),
                },
            )
        except Exception as e:
            log.warning(f"Failed to notify supervisor of plan generation: {e}")
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"notify_planning_generated completed in {latency_ms:.2f}ms")

    async def request_emergency_workflow(
        self, twin_id: str, entity_id: str, emergency_type: str, risk_score: float
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        result = {"status": "failed", "workflow_id": None}
        if not self._supervisor:
            log.warning("SupervisorService not available, skipping request_emergency_workflow")
            return result

        try:
            response = await self._supervisor.initiate_workflow(
                workflow_type="EMERGENCY_RESPONSE",
                context={
                    "twin_id": twin_id,
                    "entity_id": entity_id,
                    "emergency_type": emergency_type,
                    "risk_score": risk_score,
                    "timestamp": time.time(),
                },
            )
            result = {"status": "success", "workflow_id": response.get("workflow_id")}
        except Exception as e:
            log.warning(f"Failed to request emergency workflow from supervisor: {e}")
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"request_emergency_workflow completed in {latency_ms:.2f}ms")
        return result

from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class TwinEventPublisher:
    def __init__(self):
        try:
            from app.core.events.event_bus import EventBus
            self._event_bus = EventBus()
        except Exception:
            self._event_bus = None

    def _publish(self, event: dict[str, Any]) -> None:
        if self._event_bus:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._event_bus.publish(event))
                else:
                    loop.run_until_complete(self._event_bus.publish(event))
            except Exception as exc:
                log.warning(f"Event publish failed: {exc}")

    async def publish_twin_created(self, twin_id: str, plant_id: str, plant_name: str, sync_mode: str) -> None:
        event = {
            "type": "TwinCreated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "plant_id": plant_id,
                "plant_name": plant_name,
                "sync_mode": sync_mode
            }
        }
        self._publish(event)

    async def publish_twin_updated(self, twin_id: str, updated_fields: list[str], version_number: int) -> None:
        event = {
            "type": "TwinUpdated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "updated_fields": updated_fields,
                "version_number": version_number
            }
        }
        self._publish(event)

    async def publish_snapshot_created(self, twin_id: str, snapshot_id: str, version_number: int, entity_count: int, description: str) -> None:
        event = {
            "type": "SnapshotCreated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "snapshot_id": snapshot_id,
                "version_number": version_number,
                "entity_count": entity_count,
                "description": description
            }
        }
        self._publish(event)

    async def publish_state_changed(self, twin_id: str, entity_id: str, entity_type: str, old_status: str, new_status: str, reason: str, risk_score: float, health_score: float) -> None:
        event = {
            "type": "StateChanged",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
                "risk_score": risk_score,
                "health_score": health_score
            }
        }
        self._publish(event)

    async def publish_simulation_started(self, twin_id: str, simulation_id: str, simulation_type: str, title: str) -> None:
        event = {
            "type": "SimulationStarted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "simulation_id": simulation_id,
                "simulation_type": simulation_type,
                "title": title
            }
        }
        self._publish(event)

    async def publish_simulation_completed(self, twin_id: str, simulation_id: str, simulation_type: str, status: str, confidence: float, latency_ms: float) -> None:
        event = {
            "type": "SimulationCompleted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "simulation_id": simulation_id,
                "simulation_type": simulation_type,
                "status": status,
                "confidence": confidence,
                "latency_ms": latency_ms
            }
        }
        self._publish(event)

    async def publish_scenario_generated(self, twin_id: str, scenario_id: str, scenario_type: str, probability: float, confidence: float) -> None:
        event = {
            "type": "ScenarioGenerated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "scenario_id": scenario_id,
                "scenario_type": scenario_type,
                "probability": probability,
                "confidence": confidence
            }
        }
        self._publish(event)

    async def publish_optimization_completed(self, twin_id: str, optimization_id: str, target: str, improvement_pct: float, latency_ms: float) -> None:
        event = {
            "type": "OptimizationCompleted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "optimization_id": optimization_id,
                "target": target,
                "improvement_pct": improvement_pct,
                "latency_ms": latency_ms
            }
        }
        self._publish(event)

    async def publish_replay_started(self, twin_id: str, replay_id: str, start_timestamp: str, end_timestamp: str, replay_by: str) -> None:
        event = {
            "type": "ReplayStarted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "replay_id": replay_id,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "replay_by": replay_by
            }
        }
        self._publish(event)

    async def publish_replay_completed(self, twin_id: str, replay_id: str, total_frames: int, events_replayed_count: int, duration_seconds: float) -> None:
        event = {
            "type": "ReplayCompleted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "replay_id": replay_id,
                "total_frames": total_frames,
                "events_replayed_count": events_replayed_count,
                "duration_seconds": duration_seconds
            }
        }
        self._publish(event)

    async def publish_planning_generated(self, twin_id: str, plan_id: str, plan_type: str, entity_id: str, action_count: int, confidence: float) -> None:
        event = {
            "type": "PlanningGenerated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "twin_id": twin_id,
                "plan_id": plan_id,
                "plan_type": plan_type,
                "entity_id": entity_id,
                "action_count": action_count,
                "confidence": confidence
            }
        }
        self._publish(event)

from __future__ import annotations

import time
import uuid
from typing import Any, List, Optional
from app.core.logging import get_logger

log = get_logger(__name__)

class TwinStateManager:
    def __init__(self):
        self.states = {}
    async def get_state(self, twin_id: str, entity_id: str = None, entity_type: str = None) -> dict:
        return {"entities": {}, "total_count": 0, "snapshot_version": 1}
    async def update_state(self, twin_id: str, updates: dict) -> None:
        pass
    async def override_state(self, twin_id: str, entity_id: str, entity_type: str, overrides: dict, by: str) -> None:
        pass

class TwinSnapshotManager:
    async def create_snapshot(self, twin_id: str, description: str, created_by: str) -> dict:
        return {"snapshot_id": str(uuid.uuid4()), "twin_id": twin_id, "version": 2}


class DigitalTwinOrchestrationService:
    def __init__(
        self,
        repository=None,
        event_publisher=None,
        graphrag_service=None,
        knowledge_service=None,
    ):
        try:
            from app.modules.digital_twin.application.repositories.twin_repository import InMemoryTwinRepository
        except ImportError:
            class InMemoryTwinRepository:
                def __init__(self): self.store = {}
                async def save_twin(self, twin_id, data): self.store[twin_id] = data
                async def get_twin(self, twin_id): return self.store.get(twin_id)
                async def save_simulation(self, sim): pass
                async def get_simulation(self, sid): return None
                async def list_simulations(self, tid, l, o): return []
                async def save_optimization(self, opt): pass
                async def save_plan(self, plan): pass
                async def save_snapshot(self, snap): pass
                async def get_snapshot(self, sid): return None
                async def list_snapshots(self, tid, l, o): return []
                
        try:
            from app.modules.digital_twin.application.events.twin_event_publisher import TwinEventPublisher
        except ImportError:
            class TwinEventPublisher:
                async def publish(self, event_type, payload): pass

        self.repository = repository or InMemoryTwinRepository()
        self.event_publisher = event_publisher or TwinEventPublisher()
        self.graphrag_service = graphrag_service
        self.knowledge_service = knowledge_service
        
        # Lazy init placeholders
        self._sync_service = None
        self._simulation_service = None
        self._scenario_service = None
        self._optimization_service = None
        self._replay_service = None
        self._planning_service = None
        self._analytics_service = None
        self._supervisor_bridge = None
        self._state_manager = TwinStateManager()
        self._snapshot_manager = TwinSnapshotManager()

    def _get_sync_service(self):
        if not self._sync_service:
            from app.modules.digital_twin.application.services.twin_sync_service import TwinSyncService
            self._sync_service = TwinSyncService(self.graphrag_service)
        return self._sync_service

    def _get_simulation_service(self):
        if not self._simulation_service:
            from app.modules.digital_twin.application.services.twin_simulation_service import TwinSimulationService
            self._simulation_service = TwinSimulationService(self.graphrag_service)
        return self._simulation_service

    def _get_scenario_service(self):
        if not self._scenario_service:
            from app.modules.digital_twin.application.services.twin_scenario_service import TwinScenarioService
            self._scenario_service = TwinScenarioService(self.graphrag_service)
        return self._scenario_service

    def _get_optimization_service(self):
        if not self._optimization_service:
            from app.modules.digital_twin.application.services.twin_optimization_service import TwinOptimizationService
            self._optimization_service = TwinOptimizationService(self.graphrag_service)
        return self._optimization_service

    def _get_replay_service(self):
        if not self._replay_service:
            from app.modules.digital_twin.application.services.twin_replay_service import TwinReplayService
            self._replay_service = TwinReplayService(self._snapshot_manager)
        return self._replay_service

    def _get_planning_service(self):
        if not self._planning_service:
            from app.modules.digital_twin.application.services.twin_planning_service import TwinPlanningService
            self._planning_service = TwinPlanningService(self.graphrag_service)
        return self._planning_service

    async def initialize_twin(self, plant_id: str, plant_name: str, sync_mode: str, description: str, created_by: str) -> dict:
        t0 = time.perf_counter()
        try:
            twin_id = str(uuid.uuid4())
            twin_data = {
                "id": twin_id,
                "plant_id": plant_id,
                "plant_name": plant_name,
                "sync_mode": sync_mode,
                "description": description,
                "status": "INITIALIZING",
                "created_at": time.time(),
                "created_by": created_by
            }
            
            await self.repository.save_twin(twin_id, twin_data)
            await self._snapshot_manager.create_snapshot(twin_id, "Initial Snapshot", created_by)
            
            sync_res = await self._get_sync_service().sync_all(twin_id)
            twin_data["status"] = "ACTIVE"
            await self.repository.save_twin(twin_id, twin_data)
            
            await self.event_publisher.publish("TwinCreated", {"twin_id": twin_id, "plant_id": plant_id})
            return {"twin": twin_data, "sync_results": sync_res, "latency_ms": (time.perf_counter() - t0) * 1000}
        except Exception as e:
            log.error(f"Twin initialization failed: {e}")
            raise
        finally:
            log.info(f"initialize_twin completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def get_twin(self, twin_id: str) -> Optional[dict]:
        t0 = time.perf_counter()
        try:
            return await self.repository.get_twin(twin_id)
        finally:
            log.info(f"get_twin completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def get_twin_health(self, twin_id: str) -> dict:
        t0 = time.perf_counter()
        try:
            statuses = self._get_sync_service().get_sync_statuses()
            state = await self._state_manager.get_state(twin_id)
            return {
                "twin_id": twin_id,
                "status": "HEALTHY",
                "sync_statuses": statuses,
                "active_simulations": 0,
                "entity_count": state.get("total_count", 0),
                "latency_ms": (time.perf_counter() - t0) * 1000
            }
        finally:
            log.info(f"get_twin_health completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def synchronize(self, twin_id: str, sources: List[str] = None, context: dict = None) -> dict:
        t0 = time.perf_counter()
        context = context or {}
        try:
            if sources:
                res = {}
                for s in sources:
                    res[s] = await self._get_sync_service().sync_source(twin_id, s, context)
                sync_res = {"sources": res, "total_updates": sum(r.get("updates", 0) for r in res.values())}
            else:
                sync_res = await self._get_sync_service().sync_all(twin_id, context)

            await self._state_manager.update_state(twin_id, sync_res)
            if not sources:
                await self._snapshot_manager.create_snapshot(twin_id, "Auto Sync Snapshot", "system")
            
            await self.event_publisher.publish("TwinUpdated", {"twin_id": twin_id})
            await self.event_publisher.publish("TwinStateChanged", {"twin_id": twin_id})
            
            sync_res["latency_ms"] = (time.perf_counter() - t0) * 1000
            return sync_res
        finally:
            log.info(f"synchronize completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def get_state(self, twin_id: str, entity_id: str = None, entity_type: str = None) -> dict:
        t0 = time.perf_counter()
        try:
            state = await self._state_manager.get_state(twin_id, entity_id, entity_type)
            state["latency_ms"] = (time.perf_counter() - t0) * 1000
            return state
        finally:
            log.info(f"get_state completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def override_state(self, twin_id: str, entity_id: str, entity_type: str, overrides: dict, overridden_by: str) -> dict:
        t0 = time.perf_counter()
        try:
            await self._state_manager.override_state(twin_id, entity_id, entity_type, overrides, overridden_by)
            await self.event_publisher.publish("TwinStateChanged", {"twin_id": twin_id, "entity_id": entity_id, "reason": "MANUAL_OVERRIDE"})
            return {"status": "SUCCESS", "latency_ms": (time.perf_counter() - t0) * 1000}
        finally:
            log.info(f"override_state completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def create_snapshot(self, twin_id: str, description: str, created_by: str) -> dict:
        t0 = time.perf_counter()
        try:
            snap = await self._snapshot_manager.create_snapshot(twin_id, description, created_by)
            await self.repository.save_snapshot(snap)
            await self.event_publisher.publish("TwinSnapshotCreated", {"twin_id": twin_id, "snapshot_id": snap["snapshot_id"]})
            snap["latency_ms"] = (time.perf_counter() - t0) * 1000
            return snap
        finally:
            log.info(f"create_snapshot completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def list_snapshots(self, twin_id: str, limit: int = 20, offset: int = 0) -> List[dict]:
        t0 = time.perf_counter()
        try:
            return await self.repository.list_snapshots(twin_id, limit, offset)
        finally:
            log.info(f"list_snapshots completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def get_snapshot(self, snapshot_id: str) -> Optional[dict]:
        t0 = time.perf_counter()
        try:
            return await self.repository.get_snapshot(snapshot_id)
        finally:
            log.info(f"get_snapshot completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def restore_snapshot(self, twin_id: str, snapshot_id: str) -> dict:
        t0 = time.perf_counter()
        try:
            snap = await self.get_snapshot(snapshot_id)
            if not snap:
                raise ValueError("Snapshot not found")
            await self._state_manager.update_state(twin_id, snap.get("data", {}))
            await self.event_publisher.publish("TwinStateChanged", {"twin_id": twin_id, "reason": "RESTORE"})
            return {"status": "RESTORED", "snapshot_id": snapshot_id, "latency_ms": (time.perf_counter() - t0) * 1000}
        finally:
            log.info(f"restore_snapshot completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def run_simulation(self, twin_id: str, simulation_type: str, parameters: dict, title: str, description: str) -> dict:
        t0 = time.perf_counter()
        try:
            state = await self.get_state(twin_id)
            sim = await self._get_simulation_service().run(twin_id, simulation_type, state, parameters)
            sim.update({"title": title, "description": description})
            await self.repository.save_simulation(sim)
            await self.event_publisher.publish("SimulationStarted", {"simulation_id": sim["simulation_id"]})
            await self.event_publisher.publish("SimulationCompleted", {"simulation_id": sim["simulation_id"]})
            sim["latency_ms"] = (time.perf_counter() - t0) * 1000
            return sim
        finally:
            log.info(f"run_simulation completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def get_simulation(self, simulation_id: str) -> Optional[dict]:
        t0 = time.perf_counter()
        try:
            return await self.repository.get_simulation(simulation_id)
        finally:
            log.info(f"get_simulation completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def list_simulations(self, twin_id: str, limit: int, offset: int) -> List[dict]:
        t0 = time.perf_counter()
        try:
            return await self.repository.list_simulations(twin_id, limit, offset)
        finally:
            log.info(f"list_simulations completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def generate_scenarios(self, twin_id: str, entity_id: str, entity_type: str, context: dict = None) -> List[dict]:
        t0 = time.perf_counter()
        context = context or {}
        try:
            state = await self.get_state(twin_id, entity_id, entity_type)
            scenarios = await self._get_scenario_service().generate(twin_id, state, entity_id, entity_type, context)
            for sc in scenarios:
                await self.event_publisher.publish("ScenarioGenerated", {"scenario_id": sc["scenario_id"]})
            return scenarios
        finally:
            log.info(f"generate_scenarios completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def compare_scenarios(self, twin_id: str, scenario_ids: List[str]) -> dict:
        t0 = time.perf_counter()
        try:
            return await self._get_scenario_service().compare([{"id": sid} for sid in scenario_ids])
        finally:
            log.info(f"compare_scenarios completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def run_optimization(self, twin_id: str, target: str, constraints: dict = None) -> dict:
        t0 = time.perf_counter()
        constraints = constraints or {}
        try:
            state = await self.get_state(twin_id)
            opt = await self._get_optimization_service().optimize(twin_id, target, state, constraints)
            await self.repository.save_optimization(opt)
            await self.event_publisher.publish("OptimizationCompleted", {"optimization_id": opt["optimization_id"]})
            opt["latency_ms"] = (time.perf_counter() - t0) * 1000
            return opt
        finally:
            log.info(f"run_optimization completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def start_replay(self, twin_id: str, replay_by: str, start_timestamp: float, end_timestamp: float, speed_multiplier: float = 1.0) -> dict:
        t0 = time.perf_counter()
        try:
            return await self._get_replay_service().start(twin_id, replay_by, start_timestamp, end_timestamp, speed_multiplier)
        finally:
            log.info(f"start_replay completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def get_replay_frame(self, replay_id: str, frame_index: int) -> dict:
        t0 = time.perf_counter()
        try:
            return await self._get_replay_service().get_frame(replay_id, frame_index)
        finally:
            log.info(f"get_replay_frame completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def control_replay(self, replay_id: str, action: str, speed_multiplier: float = None) -> dict:
        t0 = time.perf_counter()
        try:
            return await self._get_replay_service().control(replay_id, action, speed_multiplier)
        finally:
            log.info(f"control_replay completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def generate_plan(self, twin_id: str, plan_type: str, entity_id: str, horizon_days: int = 30, context: dict = None) -> dict:
        t0 = time.perf_counter()
        context = context or {}
        try:
            state = await self.get_state(twin_id, entity_id)
            plan = await self._get_planning_service().generate(twin_id, plan_type, state, entity_id, horizon_days, context)
            await self.repository.save_plan(plan)
            await self.event_publisher.publish("PlanningGenerated", {"plan_id": plan["plan_id"]})
            plan["latency_ms"] = (time.perf_counter() - t0) * 1000
            return plan
        finally:
            log.info(f"generate_plan completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def get_analytics(self, twin_id: str) -> dict:
        t0 = time.perf_counter()
        try:
            return {"twin_id": twin_id, "health_score": 0.95, "uptime": 99.9}
        finally:
            log.info(f"get_analytics completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def get_state_trends(self, twin_id: str, entity_id: str, limit: int = 50) -> dict:
        t0 = time.perf_counter()
        try:
            return {"entity_id": entity_id, "trends": []}
        finally:
            log.info(f"get_state_trends completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def explain_entity(self, twin_id: str, entity_id: str) -> dict:
        t0 = time.perf_counter()
        try:
            state = await self.get_state(twin_id, entity_id)
            res = {"entity_id": entity_id, "state": state, "reasoning": "Normal operations", "recommendations": []}
            
            if self.knowledge_service:
                try:
                    res["kg_neighbors"] = await self.knowledge_service.get_neighbors(entity_id)
                except Exception as e:
                    log.warning(f"Failed to fetch KG neighbors: {e}")

            if self.graphrag_service:
                try:
                    gr_res = await self.graphrag_service.answer(f"Explain the state of entity {entity_id} in twin {twin_id}")
                    res["explanation"] = gr_res.answer
                    res["citations"] = getattr(gr_res, "citations", [])
                except Exception as e:
                    log.warning(f"GraphRAG explain failed: {e}")
                    
            res["latency_ms"] = (time.perf_counter() - t0) * 1000
            return res
        finally:
            log.info(f"explain_entity completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def get_version(self, twin_id: str) -> dict:
        t0 = time.perf_counter()
        try:
            return {"version": "1.0.0", "twin_id": twin_id}
        finally:
            log.info(f"get_version completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

    async def get_history(self, twin_id: str, entity_id: str, limit: int, offset: int) -> List[dict]:
        t0 = time.perf_counter()
        try:
            return []
        finally:
            log.info(f"get_history completed in {(time.perf_counter() - t0) * 1000:.2f}ms")

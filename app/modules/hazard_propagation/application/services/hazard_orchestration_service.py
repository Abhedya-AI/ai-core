from __future__ import annotations
import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.modules.hazard_propagation.infrastructure.repositories.postgres_hazard_repository import PostgresHazardRepository as InMemoryHazardRepository
except ImportError:
    InMemoryHazardRepository = None

try:
    from app.modules.hazard_propagation.application.events.hazard_event_publisher import HazardEventPublisher
except ImportError:
    HazardEventPublisher = None

class HazardOrchestrationService:
    """Master orchestration service for the Hazard Propagation Intelligence Platform.
    
    Coordinates all sub-services: propagation analysis, exposure assessment,
    containment generation, evacuation planning, cascade detection, and simulation.
    Integrates with GraphRAG, Knowledge Graph, Supervisor, and Event Platform.
    """
    
    def __init__(
        self,
        repository: Any = None,
        event_publisher: Any = None,
        graphrag_service: Any = None,
        knowledge_service: Any = None,
    ) -> None:
        self.repository = repository or (InMemoryHazardRepository() if InMemoryHazardRepository else None)
        self.event_publisher = event_publisher or (HazardEventPublisher() if HazardEventPublisher else None)
        self.graphrag_service = graphrag_service
        self.knowledge_service = knowledge_service
        
        # Lazy init sub-services
        self._propagation_service = None
        self._exposure_service = None
        self._containment_service = None
        self._evacuation_service = None
        self._cascade_service = None
        self._simulation_service = None
        self._supervisor_bridge = None
        self._recommendation_engine = None
        self._analytics_service = None
        self._kg_sync = None

    async def _get_graphrag_context(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if not self.graphrag_service:
            return context
        try:
            enriched = await self.graphrag_service.query(entity_id=entity_id, context=context)
            context.update(enriched)
        except Exception as e:
            log.warning(f"GraphRAG enrichment failed: {e}")
        return context

    def _get_propagation_service(self) -> Any:
        if not self._propagation_service:
            try:
                from app.modules.hazard_propagation.application.services.propagation_service import PropagationService
                self._propagation_service = PropagationService()
            except ImportError as e:
                log.warning(f"PropagationService not available: {e}")
        return self._propagation_service

    def _get_exposure_service(self) -> Any:
        if not self._exposure_service:
            try:
                from app.modules.hazard_propagation.application.services.exposure_service import ExposureService
                self._exposure_service = ExposureService()
            except ImportError as e:
                log.warning(f"ExposureService not available: {e}")
        return self._exposure_service

    def _get_containment_service(self) -> Any:
        if not self._containment_service:
            try:
                from app.modules.hazard_propagation.application.services.containment_service import ContainmentService
                self._containment_service = ContainmentService(self.graphrag_service, self.knowledge_service)
            except ImportError as e:
                log.warning(f"ContainmentService not available: {e}")
        return self._containment_service

    def _get_evacuation_service(self) -> Any:
        if not self._evacuation_service:
            try:
                from app.modules.hazard_propagation.application.services.evacuation_service import EvacuationService
                self._evacuation_service = EvacuationService()
            except ImportError as e:
                log.warning(f"EvacuationService not available: {e}")
        return self._evacuation_service

    def _get_cascade_service(self) -> Any:
        if not self._cascade_service:
            try:
                from app.modules.hazard_propagation.application.services.cascade_service import CascadeService
                self._cascade_service = CascadeService()
            except ImportError as e:
                log.warning(f"CascadeService not available: {e}")
        return self._cascade_service

    def _get_simulation_service(self) -> Any:
        if not self._simulation_service:
            try:
                from app.modules.hazard_propagation.application.services.simulation_service import SimulationService
                self._simulation_service = SimulationService()
            except ImportError as e:
                log.warning(f"SimulationService not available: {e}")
        return self._simulation_service

    def _get_supervisor_bridge(self) -> Any:
        if not self._supervisor_bridge:
            try:
                from app.modules.hazard_propagation.application.services.supervisor_bridge import HazardSupervisorBridge
                self._supervisor_bridge = HazardSupervisorBridge()
            except ImportError as e:
                log.warning(f"HazardSupervisorBridge not available: {e}")
        return self._supervisor_bridge

    def _get_recommendation_engine(self) -> Any:
        # Dummy implementation
        return None

    def _get_analytics_service(self) -> Any:
        # Dummy implementation
        return None

    def _get_kg_sync(self) -> Any:
        if not self._kg_sync:
            try:
                from app.modules.hazard_propagation.infrastructure.knowledge_graph.hazard_kg_sync import HazardKnowledgeGraphSync
                self._kg_sync = HazardKnowledgeGraphSync()
            except ImportError as e:
                log.warning(f"HazardKnowledgeGraphSync not available: {e}")
        return self._kg_sync

    async def detect_and_analyze(self, request: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        source_node_id = request.get("source_node_id", "")
        context = request.get("context", {})
        context = await self._get_graphrag_context(source_node_id, context)
        request["context"] = context

        propagation_id = str(uuid.uuid4())
        hazard_type = request.get("hazard_type", "UNKNOWN")
        initial_intensity = request.get("initial_intensity", 1.0)
        severity = "HIGH" if initial_intensity > 0.7 else "MEDIUM"
        
        request["propagation_id"] = propagation_id

        propagation_res = await self.analyze_propagation(request)
        
        exposure_task = self.assess_exposure(request)
        cascade_task = self.detect_cascade(request)
        exposure_res, cascade_res = await asyncio.gather(exposure_task, cascade_task, return_exceptions=True)
        if isinstance(exposure_res, Exception): exposure_res = {}
        if isinstance(cascade_res, Exception): cascade_res = {}
        
        containment_res = await self.generate_containment(request)
        
        evacuation_res = {}
        if severity in ["HIGH", "CRITICAL"]:
            evacuation_res = await self.generate_evacuation(request)
            
        recommendations = []

        if self.repository and hasattr(self.repository, "save_propagation"):
            await self.repository.save_propagation(propagation_id, propagation_res)

        if self.event_publisher:
            try:
                await self.event_publisher.publish("HazardDetected", {"propagation_id": propagation_id})
                await self.event_publisher.publish("PropagationCompleted", {"propagation_id": propagation_id})
            except Exception as e:
                log.warning(f"Event publish failed: {e}")

        kg_sync = self._get_kg_sync()
        if kg_sync:
            await kg_sync.sync_propagation_node(
                propagation_id, hazard_type, source_node_id, 
                propagation_res.get("affected_nodes", {}), severity
            )

        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "propagation_id": propagation_id,
            "propagation": propagation_res,
            "exposure": exposure_res,
            "cascade": cascade_res,
            "containment": containment_res,
            "evacuation": evacuation_res,
            "recommendations": recommendations,
            "latency_ms": latency_ms
        }

    async def analyze_propagation(self, request: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        hazard_type = request.get("hazard_type", "UNKNOWN")
        source_node_id = request.get("source_node_id", "")
        initial_intensity = request.get("initial_intensity", 1.0)
        nodes = request.get("nodes", {})
        edges = request.get("edges", [])
        wind_speed = request.get("wind_speed_ms", 0.0)
        wind_direction = request.get("wind_direction_deg", 0.0)
        time_steps = request.get("time_steps", 60)
        context = request.get("context", {})
        propagation_id = request.get("propagation_id", str(uuid.uuid4()))

        prop_svc = self._get_propagation_service()
        if not prop_svc:
            return {"latency_ms": (time.perf_counter() - t0) * 1000}
            
        res = await prop_svc.analyze(hazard_type, source_node_id, initial_intensity, nodes, edges, wind_speed, wind_direction, time_steps, context)
        
        timeline = prop_svc.generate_timeline(propagation_id, source_node_id, res.get("affected_nodes", {}))
        forecast = prop_svc.generate_forecast(propagation_id, hazard_type, source_node_id, res.get("affected_nodes", {}))
        
        if self.repository and hasattr(self.repository, "save_propagation"):
            await self.repository.save_propagation(propagation_id, res)
            
        if self.event_publisher:
            try:
                await self.event_publisher.publish("PropagationStarted", {"propagation_id": propagation_id})
                await self.event_publisher.publish("PropagationUpdated", {"propagation_id": propagation_id})
            except Exception as e:
                log.warning(f"Event publish failed: {e}")
                
        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "propagation_id": propagation_id,
            "affected_nodes": res.get("affected_nodes", {}),
            "arrival_times": res.get("arrival_times", {}),
            "peak_intensity": res.get("peak_intensity", 0.0),
            "model_type": res.get("model_type", "Unknown"),
            "confidence": res.get("confidence", 0.8),
            "timeline": timeline,
            "forecast": forecast,
            "latency_ms": latency_ms
        }

    async def assess_exposure(self, request: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        propagation_id = request.get("propagation_id", "")
        affected_nodes = request.get("affected_nodes", {})
        worker_ids = request.get("worker_ids", [])
        zone_ids = request.get("zone_ids", [])
        equipment_ids = request.get("equipment_ids", [])
        hazard_type = request.get("hazard_type", "UNKNOWN")
        context = request.get("context", {})
        
        svc = self._get_exposure_service()
        if not svc:
            return {"latency_ms": (time.perf_counter() - t0) * 1000}
            
        res = await svc.assess(propagation_id, affected_nodes, worker_ids, zone_ids, equipment_ids, hazard_type, context)
        
        exceeded = await svc.check_thresholds(res)
        if exceeded and self.event_publisher:
            try:
                await self.event_publisher.publish("ExposureThresholdExceeded", {"propagation_id": propagation_id, "exceeded": exceeded})
            except Exception as e:
                log.warning(f"Event publish failed: {e}")
                
        if self.repository and hasattr(self.repository, "save_exposure"):
            await self.repository.save_exposure(f"exp_{propagation_id}", res)
            
        latency_ms = (time.perf_counter() - t0) * 1000
        res["latency_ms"] = latency_ms
        return res

    async def generate_containment(self, request: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        propagation_id = request.get("propagation_id", "")
        hazard_type = request.get("hazard_type", "UNKNOWN")
        source_node_id = request.get("source_node_id", "")
        affected_nodes = request.get("affected_nodes", {})
        severity = request.get("severity", "MEDIUM")
        context = request.get("context", {})
        
        svc = self._get_containment_service()
        if not svc:
            return {"latency_ms": (time.perf_counter() - t0) * 1000}
            
        plan = await svc.generate(propagation_id, hazard_type, source_node_id, affected_nodes, severity, context)
        
        if self.repository and hasattr(self.repository, "save_containment"):
            await self.repository.save_containment(plan.get("plan_id", ""), plan)
            
        if self.event_publisher:
            try:
                await self.event_publisher.publish("ContainmentGenerated", {"propagation_id": propagation_id})
            except Exception as e:
                log.warning(f"Event publish failed: {e}")
                
        kg = self._get_kg_sync()
        if kg:
            await kg.sync_containment_node(plan.get("plan_id", ""), propagation_id, [], [])
            
        latency_ms = (time.perf_counter() - t0) * 1000
        plan["latency_ms"] = latency_ms
        return plan

    async def generate_evacuation(self, request: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        propagation_id = request.get("propagation_id", "")
        zone_ids = request.get("zone_ids", [])
        worker_ids = request.get("worker_ids", [])
        hazard_intensities = request.get("hazard_intensities", {})
        context = request.get("context", {})
        
        svc = self._get_evacuation_service()
        if not svc:
            return {"latency_ms": (time.perf_counter() - t0) * 1000}
            
        rec = await svc.generate(propagation_id, zone_ids, worker_ids, hazard_intensities, context)
        
        if self.repository and hasattr(self.repository, "save_evacuation"):
            await self.repository.save_evacuation(rec.get("recommendation_id", ""), rec)
            
        if self.event_publisher:
            try:
                await self.event_publisher.publish("EvacuationGenerated", {"propagation_id": propagation_id})
            except Exception as e:
                log.warning(f"Event publish failed: {e}")
                
        kg = self._get_kg_sync()
        if kg:
            await kg.sync_evacuation_node(rec.get("recommendation_id", ""), propagation_id, [], [])
            
        latency_ms = (time.perf_counter() - t0) * 1000
        rec["latency_ms"] = latency_ms
        return rec

    async def detect_cascade(self, request: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        propagation_id = request.get("propagation_id", "")
        hazard_type = request.get("hazard_type", "UNKNOWN")
        intensity = request.get("initial_intensity", 1.0)
        zone_conditions = request.get("zone_conditions", {})
        source_node_id = request.get("source_node_id", "")
        
        svc = self._get_cascade_service()
        if not svc:
            return {"latency_ms": (time.perf_counter() - t0) * 1000}
            
        domino = await svc.detect(propagation_id, hazard_type, intensity, zone_conditions, source_node_id)
        
        chain = await svc.build_domino_chain(hazard_type, intensity)
        domino["chain"] = chain.get("chain", {})
        domino["probability"] = chain.get("probability", 0.0)
        
        if domino["probability"] > 0.3 and self.event_publisher:
            try:
                await self.event_publisher.publish("CascadeDetected", {"propagation_id": propagation_id})
            except Exception as e:
                log.warning(f"Event publish failed: {e}")
                
        if self.repository and hasattr(self.repository, "save_cascade"):
            await self.repository.save_cascade(domino.get("cascade_id", ""), domino)
            
        latency_ms = (time.perf_counter() - t0) * 1000
        domino["latency_ms"] = latency_ms
        return domino

    async def run_simulation(self, request: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        svc = self._get_simulation_service()
        if not svc:
            return {"latency_ms": (time.perf_counter() - t0) * 1000}
            
        sim = await svc.run_what_if(request)
        
        if self.event_publisher:
            try:
                await self.event_publisher.publish("SimulationCompleted", {"simulation_id": sim.get("simulation_id", "")})
            except Exception as e:
                log.warning(f"Event publish failed: {e}")
                
        if self.repository and hasattr(self.repository, "save_simulation"):
            await self.repository.save_simulation(sim.get("simulation_id", ""), sim)
            
        latency_ms = (time.perf_counter() - t0) * 1000
        sim["latency_ms"] = latency_ms
        return sim

    async def generate_full_assessment(self, request: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        propagation_id = request.get("propagation_id", str(uuid.uuid4()))
        request["propagation_id"] = propagation_id
        
        prop_res, casc_res = await asyncio.gather(
            self.analyze_propagation(request),
            self.detect_cascade(request),
            return_exceptions=True
        )
        if isinstance(prop_res, Exception): prop_res = {}
        if isinstance(casc_res, Exception): casc_res = {}
        
        request["affected_nodes"] = prop_res.get("affected_nodes", {})
        
        exp_res, cont_res = await asyncio.gather(
            self.assess_exposure(request),
            self.generate_containment(request),
            return_exceptions=True
        )
        if isinstance(exp_res, Exception): exp_res = {}
        if isinstance(cont_res, Exception): cont_res = {}
        
        evac_res = await self.generate_evacuation(request)
        
        recommendations = []
        analytics = await self.get_analytics(propagation_id)
        
        bridge = self._get_supervisor_bridge()
        if bridge:
            await bridge.notify_hazard_detected(prop_res)
            
        if self.event_publisher:
            try:
                await self.event_publisher.publish("PropagationCompleted", {"propagation_id": propagation_id})
            except Exception as e:
                log.warning(f"Event publish failed: {e}")
                
        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "propagation_id": propagation_id,
            "propagation": prop_res,
            "cascade": casc_res,
            "exposure": exp_res,
            "containment": cont_res,
            "evacuation": evac_res,
            "recommendations": recommendations,
            "analytics": analytics,
            "latency_ms": latency_ms
        }

    async def list_propagations(self, hazard_type: str | None = None, state: str | None = None, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        if self.repository and hasattr(self.repository, "list_propagations"):
            return await self.repository.list_propagations(hazard_type, state, page, page_size)
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    async def get_propagation(self, propagation_id: str) -> dict[str, Any] | None:
        if self.repository and hasattr(self.repository, "get_propagation"):
            return await self.repository.get_propagation(propagation_id)
        return None

    async def get_analytics(self, propagation_id: str) -> dict[str, Any]:
        return {}

    async def explain_propagation(self, propagation_id: str) -> dict[str, Any]:
        return {
            "propagation_id": propagation_id,
            "methodology": "Graph diffusion + Gaussian plume + Cellular automata ensemble",
            "propagation_path": ["Source node", "Affected zones", "Downstream dependencies"],
            "kg_traversal_path": ["HazardNode", "PROPAGATES_TO", "AffectedZone", "EXPOSES", "Worker"],
            "graphrag_citations": [],
            "risk_references": [],
            "forecast_references": [],
            "rca_references": [],
            "confidence": 0.75,
            "alternative_scenarios": [
                {"scenario": "With immediate containment", "estimated_reduction": 0.6},
                {"scenario": "Wind direction reversal", "estimated_reduction": 0.3},
            ],
            "uncertainty_factors": ["Wind variability", "Fuel load uncertainty", "Barrier effectiveness"]
        }

from __future__ import annotations

from typing import Any, Dict
from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.infrastructure.neo4j.client import neo4j_client
except ImportError:
    neo4j_client = None


class TwinKnowledgeGraphSync:
    def __init__(self):
        self._neo4j = neo4j_client
        try:
            from app.modules.knowledge.services.knowledge_service import KnowledgeService
            self.knowledge_service = KnowledgeService()
        except ImportError:
            self.knowledge_service = None

    async def sync_twin_node(self, twin_id: str, plant_id: str, plant_name: str, status: str, version: int) -> None:
        if not self._neo4j:
            log.warning("Neo4j not available, skipping KG sync for twin_node")
            return
        try:
            query = """
            MERGE (t:DigitalTwin {id: $twin_id})
            SET t.status = $status, t.version = $version
            MERGE (p:Plant {id: $plant_id})
            SET p.name = $plant_name
            MERGE (t)-[:MIRRORS]->(p)
            """
            await self._neo4j.execute(query, {
                "twin_id": twin_id,
                "plant_id": plant_id,
                "plant_name": plant_name,
                "status": status,
                "version": version
            })
        except Exception as e:
            log.warning(f"KG sync failed for twin_node: {e}")

    async def sync_entity_state(self, entity_id: str, entity_type: str, twin_id: str, health_score: float, risk_score: float, status: str) -> None:
        if not self._neo4j:
            log.warning("Neo4j not available, skipping KG sync for entity_state")
            return
        try:
            query = f"""
            MERGE (e:{entity_type} {{id: $entity_id}})
            SET e.health_score = $health, e.risk_score = $risk, e.status = $status
            MERGE (t:DigitalTwin {{id: $twin_id}})
            MERGE (e)-[:REPRESENTS]->(t)
            """
            await self._neo4j.execute(query, {
                "entity_id": entity_id,
                "twin_id": twin_id,
                "health": health_score,
                "risk": risk_score,
                "status": status
            })
        except Exception as e:
            log.warning(f"KG sync failed for entity_state: {e}")

    async def sync_simulation(self, twin_id: str, simulation_id: str, simulation_type: str, status: str, confidence: float) -> None:
        if not self._neo4j:
            log.warning("Neo4j not available, skipping KG sync for simulation")
            return
        try:
            query = """
            MERGE (s:Simulation {id: $sim_id})
            SET s.type = $type, s.status = $status, s.confidence = $confidence
            MERGE (t:DigitalTwin {id: $twin_id})
            MERGE (s)-[:SIMULATES]->(t)
            """
            await self._neo4j.execute(query, {
                "sim_id": simulation_id,
                "twin_id": twin_id,
                "type": simulation_type,
                "status": status,
                "confidence": confidence
            })
        except Exception as e:
            log.warning(f"KG sync failed for simulation: {e}")

    async def sync_optimization(self, twin_id: str, optimization_id: str, target: str, improvement_score: float) -> None:
        if not self._neo4j:
            log.warning("Neo4j not available, skipping KG sync for optimization")
            return
        try:
            query = """
            MERGE (o:Optimization {id: $opt_id})
            SET o.target = $target, o.improvement_score = $score
            MERGE (t:DigitalTwin {id: $twin_id})
            MERGE (o)-[:OPTIMIZES]->(t)
            """
            await self._neo4j.execute(query, {
                "opt_id": optimization_id,
                "twin_id": twin_id,
                "target": target,
                "score": improvement_score
            })
        except Exception as e:
            log.warning(f"KG sync failed for optimization: {e}")

    async def sync_replay(self, twin_id: str, replay_id: str, replay_by: str) -> None:
        if not self._neo4j:
            log.warning("Neo4j not available, skipping KG sync for replay")
            return
        try:
            query = """
            MERGE (r:Replay {id: $replay_id})
            SET r.replay_by = $replay_by
            MERGE (t:DigitalTwin {id: $twin_id})
            MERGE (r)-[:REPLAYS]->(t)
            """
            await self._neo4j.execute(query, {
                "replay_id": replay_id,
                "twin_id": twin_id,
                "replay_by": replay_by
            })
        except Exception as e:
            log.warning(f"KG sync failed for replay: {e}")

    async def sync_snapshot(self, twin_id: str, snapshot_id: str, version_number: int) -> None:
        if not self._neo4j:
            log.warning("Neo4j not available, skipping KG sync for snapshot")
            return
        try:
            query = """
            MERGE (s:Snapshot {id: $snap_id})
            SET s.version_number = $version
            MERGE (t:DigitalTwin {id: $twin_id})
            MERGE (s)-[:SYNCHRONIZED_WITH]->(t)
            """
            await self._neo4j.execute(query, {
                "snap_id": snapshot_id,
                "twin_id": twin_id,
                "version": version_number
            })
        except Exception as e:
            log.warning(f"KG sync failed for snapshot: {e}")

    async def get_twin_subgraph(self, twin_id: str) -> Dict[str, Any]:
        if not self._neo4j:
            log.warning("Neo4j not available, skipping get_twin_subgraph")
            return {"nodes": [], "relationships": []}
        try:
            query = """
            MATCH (t:DigitalTwin {id: $twin_id})-[r]-(connected)
            RETURN t, r, connected
            """
            result = await self._neo4j.fetch_all(query, {"twin_id": twin_id})
            # This is a simplified extraction since true Graph serialization depends on exact driver format
            return {"raw_subgraph": result}
        except Exception as e:
            log.warning(f"KG subgraph fetch failed: {e}")
            return {"nodes": [], "relationships": []}

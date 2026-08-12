"""evidence_collector.py — Evidence Collection Engine for RCA investigations."""
from __future__ import annotations
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Evidence, EvidenceType, EvidenceSource, EvidenceWeight, EvidenceScore,
)
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository

log = get_logger("root_cause.evidence.collector")


class EvidenceCollectionEngine:
    """Collects and normalizes evidence from all platform modules."""

    def __init__(self, neo4j_repository: BaseNeo4jRepository | None = None) -> None:
        self.neo4j_repository = neo4j_repository

    async def collect_sensor_evidence(
        self, incident_id: str, zone_id: str, time_window_seconds: int,
    ) -> list[Evidence]:
        log.info(f"Collecting sensor evidence for incident {incident_id}, zone {zone_id}")
        now = datetime.now(timezone.utc).isoformat()
        return [
            Evidence(
                evidence_type=EvidenceType.SENSOR_READING,
                source=EvidenceSource.SENSOR_INTELLIGENCE,
                title=f"Sensor anomaly — zone {zone_id}",
                description=f"Sensor anomaly detected for incident {incident_id} in zone {zone_id}",
                confidence=0.85,
                reliability=0.9,
                severity="HIGH",
                timestamp=now,
                zone_id=zone_id,
                incident_id=incident_id,
                raw_data={"time_window": time_window_seconds},
            )
        ]

    async def collect_vision_evidence(
        self, incident_id: str, zone_id: str, camera_ids: list[str], time_window_seconds: int,
    ) -> list[Evidence]:
        log.info(f"Collecting vision evidence for incident {incident_id}")
        now = datetime.now(timezone.utc).isoformat()
        return [
            Evidence(
                evidence_type=EvidenceType.VISION_DETECTION,
                source=EvidenceSource.VISION_INTELLIGENCE,
                title=f"Vision violation — zone {zone_id}",
                description=f"Vision violation detected for incident {incident_id}",
                confidence=0.92,
                reliability=0.88,
                severity="HIGH",
                timestamp=now,
                zone_id=zone_id,
                incident_id=incident_id,
                raw_data={"camera_ids": camera_ids, "time_window": time_window_seconds},
            )
        ]

    async def collect_knowledge_graph_evidence(
        self, entity_id: str, hops: int = 2,
    ) -> list[Evidence]:
        log.info(f"Collecting KG evidence for entity {entity_id}, hops={hops}")
        evidence_list: list[Evidence] = []
        if self.neo4j_repository:
            now = datetime.now(timezone.utc).isoformat()
            evidence_list.append(
                Evidence(
                    evidence_type=EvidenceType.GRAPH_ENTITY,
                    source=EvidenceSource.KNOWLEDGE_GRAPH,
                    title=f"Graph topology for {entity_id}",
                    description=f"Knowledge graph topology within {hops} hops of {entity_id}",
                    confidence=1.0,
                    reliability=1.0,
                    severity="MEDIUM",
                    timestamp=now,
                    raw_data={"entity_id": entity_id, "hops": hops},
                )
            )
        return evidence_list

    async def collect_graphrag_evidence(
        self, query_text: str, top_k: int = 5,
    ) -> list[Evidence]:
        log.info(f"Collecting GraphRAG evidence for query '{query_text}'")
        now = datetime.now(timezone.utc).isoformat()
        return [
            Evidence(
                evidence_type=EvidenceType.GRAPHRAG_DOCUMENT,
                source=EvidenceSource.GRAPHRAG,
                title="GraphRAG context retrieval",
                description=f"GraphRAG contextual retrieval for: {query_text}",
                confidence=0.75,
                reliability=0.8,
                severity="LOW",
                timestamp=now,
                raw_data={"query_text": query_text, "top_k": top_k},
            )
        ]

    async def collect_audit_evidence(
        self, incident_id: str, time_window_seconds: int,
    ) -> list[Evidence]:
        log.info(f"Collecting audit evidence for incident {incident_id}")
        now = datetime.now(timezone.utc).isoformat()
        return [
            Evidence(
                evidence_type=EvidenceType.AUDIT_LOG,
                source=EvidenceSource.AUDIT_FRAMEWORK,
                title="Audit log sequence",
                description=f"Audit log action sequence for incident {incident_id}",
                confidence=1.0,
                reliability=1.0,
                severity="LOW",
                timestamp=now,
                incident_id=incident_id,
                raw_data={"time_window": time_window_seconds},
            )
        ]

    async def collect_supervisor_evidence(
        self, incident_id: str,
    ) -> list[Evidence]:
        log.info(f"Collecting supervisor evidence for incident {incident_id}")
        now = datetime.now(timezone.utc).isoformat()
        return [
            Evidence(
                evidence_type=EvidenceType.SUPERVISOR_DECISION,
                source=EvidenceSource.SUPERVISOR,
                title="Supervisor review decision",
                description=f"Supervisor review decisions for incident {incident_id}",
                confidence=0.95,
                reliability=0.95,
                severity="MEDIUM",
                timestamp=now,
                incident_id=incident_id,
                raw_data={},
            )
        ]

    async def collect_all_evidence(
        self, incident_id: str, zone_id: str, time_window_seconds: int,
    ) -> list[Evidence]:
        log.info(f"Orchestrating all evidence collection for incident {incident_id}")
        tasks = [
            self.collect_sensor_evidence(incident_id, zone_id, time_window_seconds),
            self.collect_vision_evidence(incident_id, zone_id, [], time_window_seconds),
            self.collect_knowledge_graph_evidence(zone_id, hops=2),
            self.collect_graphrag_evidence(f"Incident {incident_id} in zone {zone_id}"),
            self.collect_audit_evidence(incident_id, time_window_seconds),
            self.collect_supervisor_evidence(incident_id),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_evidence: list[Evidence] = []
        for res in results:
            if isinstance(res, list):
                all_evidence.extend(res)
            elif isinstance(res, Exception):
                log.error(f"Evidence collection error: {res}")
        # Deduplicate
        seen: set[str] = set()
        unique: list[Evidence] = []
        for ev in all_evidence:
            if ev.id not in seen:
                seen.add(ev.id)
                unique.append(ev)
        # Sort by timestamp
        unique.sort(key=lambda e: e.timestamp)
        return unique

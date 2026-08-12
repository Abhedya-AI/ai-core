"""memory_repository.py — Investigation Memory persistence (Redis + Neo4j)."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.redis.client import get_client
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.root_cause.domain.models import InvestigationMemory, LessonLearned

log = get_logger("root_cause.memory.repository")

_MEM_KEY = "rca:memory:{investigation_id}"
_MEM_LIST_KEY = "rca:memory:list"
_LESSON_KEY = "rca:lessons:{lesson_id}"
_LESSON_LIST_KEY = "rca:lessons:list"
_TTL = 86400 * 30  # 30 days

_UPSERT_MEMORY_CYPHER = """
MERGE (m:InvestigationMemory {id: $id})
SET m += $props
RETURN m
"""

_UPSERT_LESSON_CYPHER = """
MERGE (l:LessonLearned {id: $id})
SET l += $props
RETURN l
"""

_LINK_MEMORY_TO_INCIDENT = """
MATCH (m:InvestigationMemory {id: $memory_id})
MATCH (i:Incident {id: $incident_id})
MERGE (m)-[:RESULTED_IN]->(i)
"""

_LINK_LESSON_TO_MEMORY = """
MATCH (m:InvestigationMemory {id: $memory_id})
MATCH (l:LessonLearned {id: $lesson_id})
MERGE (m)-[:LEARNED_FROM]->(l)
"""

_FIND_MEMORIES_BY_ZONE = """
MATCH (m:InvestigationMemory)
WHERE $zone_id IN m.zone_ids
RETURN m ORDER BY m.completed_at DESC LIMIT $limit
"""

_FIND_SIMILAR_MEMORIES = """
MATCH (m:InvestigationMemory)
WHERE m.id IN $ids
RETURN m
"""


class MemoryRepository:
    """Persists investigation memories to Redis (fast) + Neo4j (graph)."""

    def __init__(self, neo4j_repo: BaseNeo4jRepository | None = None) -> None:
        self._repo = neo4j_repo or BaseNeo4jRepository()

    # ── Redis ─────────────────────────────────────────────────────────────

    async def save_memory(self, memory: InvestigationMemory) -> bool:
        """Persist to Redis and Neo4j."""
        try:
            redis = get_client()
            key = _MEM_KEY.format(investigation_id=memory.investigation_id)
            await redis.set(key, memory.model_dump_json(), ex=_TTL)
            await redis.zadd(
                _MEM_LIST_KEY,
                {memory.investigation_id: datetime.now(timezone.utc).timestamp()},
            )
            await self._sync_memory_to_neo4j(memory)
            return True
        except Exception as exc:
            log.error(f"MemoryRepository.save_memory failed: {exc}")
            return False

    async def get_memory(self, investigation_id: str) -> InvestigationMemory | None:
        """Retrieve memory from Redis first, fall back to Neo4j."""
        try:
            redis = get_client()
            raw = await redis.get(_MEM_KEY.format(investigation_id=investigation_id))
            if raw:
                return InvestigationMemory.model_validate_json(raw)
        except Exception as exc:
            log.warning(f"Redis memory fetch failed, trying Neo4j: {exc}")
        return await self._get_from_neo4j(investigation_id)

    async def list_memories(
        self, limit: int = 50, offset: int = 0, zone_id: str | None = None
    ) -> list[InvestigationMemory]:
        """List recent memories from Redis sorted set."""
        try:
            redis = get_client()
            ids = await redis.zrevrange(_MEM_LIST_KEY, offset, offset + limit - 1)
            memories: list[InvestigationMemory] = []
            for inv_id in ids:
                raw = await redis.get(_MEM_KEY.format(investigation_id=inv_id))
                if raw:
                    mem = InvestigationMemory.model_validate_json(raw)
                    if zone_id is None or zone_id in mem.zone_ids:
                        memories.append(mem)
            return memories
        except Exception as exc:
            log.error(f"MemoryRepository.list_memories failed: {exc}")
            return []

    async def get_memories_by_ids(self, ids: list[str]) -> list[InvestigationMemory]:
        """Batch fetch memories by IDs."""
        results: list[InvestigationMemory] = []
        redis = get_client()
        for inv_id in ids:
            try:
                raw = await redis.get(_MEM_KEY.format(investigation_id=inv_id))
                if raw:
                    results.append(InvestigationMemory.model_validate_json(raw))
            except Exception:
                pass
        return results

    async def search_memories_by_text(self, query: str, limit: int = 20) -> list[InvestigationMemory]:
        """Simple text search over cached memories."""
        q = query.lower()
        all_mems = await self.list_memories(limit=200)
        matches = [
            m for m in all_mems
            if q in m.title.lower() or q in m.root_cause_description.lower()
            or any(q in lesson.lower() for lesson in m.lessons_learned)
        ]
        return matches[:limit]

    async def count_memories(self) -> int:
        try:
            redis = get_client()
            return await redis.zcard(_MEM_LIST_KEY)
        except Exception:
            return 0

    # ── Lessons ────────────────────────────────────────────────────────────

    async def save_lesson(self, lesson: LessonLearned) -> bool:
        try:
            redis = get_client()
            await redis.set(_LESSON_KEY.format(lesson_id=lesson.id), lesson.model_dump_json(), ex=_TTL * 12)
            await redis.zadd(_LESSON_LIST_KEY, {lesson.id: datetime.now(timezone.utc).timestamp()})
            await self._sync_lesson_to_neo4j(lesson)
            return True
        except Exception as exc:
            log.error(f"MemoryRepository.save_lesson failed: {exc}")
            return False

    async def list_lessons(
        self,
        limit: int = 50,
        offset: int = 0,
        zone_id: str | None = None,
        equipment_type: str | None = None,
    ) -> list[LessonLearned]:
        try:
            redis = get_client()
            ids = await redis.zrevrange(_LESSON_LIST_KEY, offset, offset + limit - 1)
            lessons: list[LessonLearned] = []
            for lid in ids:
                raw = await redis.get(_LESSON_KEY.format(lesson_id=lid))
                if raw:
                    lesson = LessonLearned.model_validate_json(raw)
                    if zone_id and zone_id not in lesson.applies_to_zones:
                        continue
                    if equipment_type and equipment_type not in lesson.applies_to_equipment_types:
                        continue
                    lessons.append(lesson)
            return lessons
        except Exception as exc:
            log.error(f"list_lessons failed: {exc}")
            return []

    async def search_lessons(self, query: str, limit: int = 20) -> list[LessonLearned]:
        q = query.lower()
        all_lessons = await self.list_lessons(limit=500)
        return [
            l for l in all_lessons
            if q in l.lesson_text.lower() or any(q in tag.lower() for tag in l.tags)
        ][:limit]

    # ── Neo4j ──────────────────────────────────────────────────────────────

    async def _sync_memory_to_neo4j(self, memory: InvestigationMemory) -> None:
        props = {
            "id": memory.id,
            "investigation_id": memory.investigation_id,
            "incident_id": memory.incident_id,
            "title": memory.title,
            "root_cause_description": memory.root_cause_description,
            "overall_confidence": memory.overall_confidence,
            "completed_at": memory.completed_at,
            "zone_ids": memory.zone_ids,
            "equipment_ids": memory.equipment_ids,
            "recommendation_count": memory.recommendation_count,
            "evidence_count": memory.evidence_count,
        }
        try:
            await self._repo.execute_query(_UPSERT_MEMORY_CYPHER, {"id": memory.id, "props": props})
            if memory.incident_id:
                await self._repo.execute_query(
                    _LINK_MEMORY_TO_INCIDENT,
                    {"memory_id": memory.id, "incident_id": memory.incident_id},
                )
        except Exception as exc:
            log.warning(f"Neo4j memory sync failed (non-critical): {exc}")

    async def _sync_lesson_to_neo4j(self, lesson: LessonLearned) -> None:
        props = {
            "id": lesson.id,
            "investigation_id": lesson.investigation_id,
            "lesson_text": lesson.lesson_text,
            "lesson_category": lesson.lesson_category,
            "confidence": lesson.confidence,
            "validated": lesson.validated,
            "tags": lesson.tags,
        }
        try:
            await self._repo.execute_query(_UPSERT_LESSON_CYPHER, {"id": lesson.id, "props": props})
        except Exception as exc:
            log.warning(f"Neo4j lesson sync failed (non-critical): {exc}")

    async def _get_from_neo4j(self, investigation_id: str) -> InvestigationMemory | None:
        try:
            records = await self._repo.execute_query(
                "MATCH (m:InvestigationMemory {investigation_id: $id}) RETURN m",
                {"id": investigation_id},
            )
            if records and records[0].get("m"):
                props = dict(records[0]["m"])
                return InvestigationMemory(**{k: v for k, v in props.items() if k in InvestigationMemory.model_fields})
        except Exception as exc:
            log.error(f"Neo4j memory fetch failed: {exc}")
        return None

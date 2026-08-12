"""memory_service.py — Investigation Memory orchestration service."""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    Investigation, InvestigationReport, InvestigationMemory, LessonLearned,
)
from app.modules.root_cause.memory.investigation_memory import InvestigationMemoryBuilder
from app.modules.root_cause.memory.memory_index import MemoryIndex, build_fingerprint
from app.modules.root_cause.memory.memory_repository import MemoryRepository

log = get_logger("root_cause.memory.service")


class MemoryService:
    """Orchestrates investigation memory: persist, search, retrieve, recurrence analysis."""

    def __init__(
        self,
        repository: MemoryRepository | None = None,
        index: MemoryIndex | None = None,
        builder: InvestigationMemoryBuilder | None = None,
    ) -> None:
        self.repository = repository or MemoryRepository()
        self.index = index or MemoryIndex()
        self.builder = builder or InvestigationMemoryBuilder()

    async def memorize(
        self,
        investigation: Investigation,
        report: InvestigationReport,
    ) -> InvestigationMemory:
        """Persist investigation to memory and update the similarity index."""
        log.info(f"Memorizing investigation {investigation.id}")
        memory = self.builder.build(investigation, report)
        lessons = self.builder.extract_lessons(investigation, report)

        # Persist memory
        await self.repository.save_memory(memory)

        # Index fingerprint for similarity search
        if memory.fingerprint:
            await self.index.index_fingerprint(investigation.id, memory.fingerprint)

        # Persist lessons
        for lesson in lessons:
            await self.repository.save_lesson(lesson)
        memory.lesson_ids = [l.id for l in lessons]

        log.info(f"Memorized investigation {investigation.id} with {len(lessons)} lessons")
        return memory

    async def find_similar(
        self,
        investigation: Investigation,
        report: InvestigationReport,
        top_k: int = 5,
        min_similarity: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Find historically similar investigations by evidence fingerprint."""
        fingerprint = build_fingerprint(report.evidence_list)
        similar_ids = await self.index.find_similar(fingerprint, top_k=top_k, min_similarity=min_similarity)
        if not similar_ids:
            return []
        ids = [s["investigation_id"] for s in similar_ids]
        memories = await self.repository.get_memories_by_ids(ids)
        mem_map = {m.investigation_id: m for m in memories}
        results = []
        for entry in similar_ids:
            mem = mem_map.get(entry["investigation_id"])
            if mem:
                results.append({
                    "investigation_id": mem.investigation_id,
                    "title": mem.title,
                    "similarity": entry["similarity"],
                    "root_cause": mem.root_cause_description,
                    "confidence": mem.overall_confidence,
                    "completed_at": mem.completed_at,
                })
        return results

    async def detect_recurrence(
        self,
        investigation: Investigation,
        report: InvestigationReport,
        similarity_threshold: float = 0.7,
    ) -> dict[str, Any]:
        """Detect if this incident is a recurrence of a past investigated pattern."""
        similar = await self.find_similar(investigation, report, top_k=10, min_similarity=similarity_threshold)
        is_recurrence = len(similar) > 0
        return {
            "is_recurrence": is_recurrence,
            "similar_count": len(similar),
            "most_similar": similar[0] if similar else None,
            "recurrence_risk": "HIGH" if len(similar) >= 3 else ("MEDIUM" if is_recurrence else "LOW"),
        }

    async def get_memory(self, investigation_id: str) -> InvestigationMemory | None:
        return await self.repository.get_memory(investigation_id)

    async def list_memories(
        self, limit: int = 50, offset: int = 0, zone_id: str | None = None
    ) -> list[InvestigationMemory]:
        return await self.repository.list_memories(limit=limit, offset=offset, zone_id=zone_id)

    async def search_memories(self, query: str, limit: int = 20) -> list[InvestigationMemory]:
        return await self.repository.search_memories_by_text(query, limit=limit)

    async def list_lessons(
        self, limit: int = 50, offset: int = 0,
        zone_id: str | None = None, equipment_type: str | None = None,
    ) -> list[LessonLearned]:
        return await self.repository.list_lessons(limit=limit, offset=offset, zone_id=zone_id, equipment_type=equipment_type)

    async def search_lessons(self, query: str, limit: int = 20) -> list[LessonLearned]:
        return await self.repository.search_lessons(query=query, limit=limit)

    async def count_memories(self) -> int:
        return await self.repository.count_memories()

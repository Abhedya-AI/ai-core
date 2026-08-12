"""investigation_analytics.py — Cross-investigation analytics and metrics engine.

Computes:
  - Total/completed investigation counts
  - Average confidence and duration
  - Top root causes and patterns by frequency
  - Zone and equipment incident frequency
  - Recommendation effectiveness rates
  - Mean Time to Resolve (MTTR)
  - False positive rate estimation
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.root_cause.domain.models import (
    InvestigationMemory, InvestigationStatus, InvestigationAnalytics,
)
from app.modules.root_cause.memory.memory_service import MemoryService
from app.modules.root_cause.feedback.feedback_repository import FeedbackRepository

log = get_logger("root_cause.analytics")


class InvestigationAnalyticsEngine:
    """Computes cross-investigation analytics from Investigation Memory."""

    def __init__(
        self,
        memory_service: MemoryService | None = None,
        feedback_repo: FeedbackRepository | None = None,
    ) -> None:
        self.memory = memory_service or MemoryService()
        self.feedback = feedback_repo or FeedbackRepository()

    async def compute_summary(
        self,
        limit: int = 1000,
        period_days: int = 90,
    ) -> InvestigationAnalytics:
        """Compute a comprehensive analytics summary."""
        log.info("Computing investigation analytics summary")
        memories = await self.memory.list_memories(limit=limit)

        total = len(memories)
        completed = sum(1 for m in memories if m.status == InvestigationStatus.COMPLETED)
        avg_confidence = sum(m.overall_confidence for m in memories) / total if total else 0.0
        avg_duration = sum(m.duration_seconds for m in memories) / total if total else 0.0

        # Root cause frequency
        root_causes = Counter(
            m.root_cause_description[:60] for m in memories if m.root_cause_description
        )
        top_root_causes = [
            {"root_cause": rc, "count": cnt}
            for rc, cnt in root_causes.most_common(10)
        ]

        # Pattern frequency
        all_patterns: list[str] = []
        for m in memories:
            all_patterns.extend(m.matched_pattern_ids)
        pattern_counts = Counter(all_patterns)
        top_patterns = [
            {"pattern_id": pid, "count": cnt}
            for pid, cnt in pattern_counts.most_common(10)
        ]

        # Zone + Equipment incident counts
        zone_counts: Counter = Counter()
        equip_counts: Counter = Counter()
        for m in memories:
            for z in m.zone_ids:
                zone_counts[z] += 1
            for e in m.equipment_ids:
                equip_counts[e] += 1

        # MTTR
        durations = [m.duration_seconds for m in memories if m.duration_seconds > 0]
        mttr = sum(durations) / len(durations) if durations else 0.0

        # Recommendation effectiveness
        effectiveness_rate = await self.feedback.compute_effectiveness_rate()

        # False positive rate heuristic: investigations completed with very low confidence
        low_conf = sum(1 for m in memories if m.overall_confidence < 0.3)
        false_positive_rate = low_conf / total if total > 0 else 0.0

        now = datetime.now(timezone.utc)
        return InvestigationAnalytics(
            total_investigations=total,
            completed_investigations=completed,
            avg_confidence=round(avg_confidence, 4),
            avg_duration_seconds=round(avg_duration, 2),
            top_root_causes=top_root_causes,
            top_patterns=top_patterns,
            zone_incident_counts=dict(zone_counts.most_common(20)),
            equipment_incident_counts=dict(equip_counts.most_common(20)),
            recommendation_effectiveness_rate=round(effectiveness_rate, 4),
            false_positive_rate=round(false_positive_rate, 4),
            mttr_seconds=round(mttr, 2),
            period_start=(now.isoformat()),
            period_end=now.isoformat(),
        )

    async def get_zone_hotspots(
        self, top_n: int = 5
    ) -> list[dict[str, Any]]:
        """Return zones with highest incident frequency."""
        analytics = await self.compute_summary()
        sorted_zones = sorted(
            analytics.zone_incident_counts.items(),
            key=lambda x: x[1], reverse=True,
        )
        return [{"zone_id": z, "incident_count": c} for z, c in sorted_zones[:top_n]]

    async def get_equipment_risk_ranking(
        self, top_n: int = 10
    ) -> list[dict[str, Any]]:
        """Return equipment ranked by incident involvement frequency."""
        analytics = await self.compute_summary()
        sorted_equip = sorted(
            analytics.equipment_incident_counts.items(),
            key=lambda x: x[1], reverse=True,
        )
        return [{"equipment_id": e, "incident_count": c} for e, c in sorted_equip[:top_n]]

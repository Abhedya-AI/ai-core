"""feedback_repository.py — RecommendationFeedback Redis + Neo4j persistence."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.redis.client import get_client
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.root_cause.domain.models import RecommendationFeedback

log = get_logger("root_cause.feedback.repository")

_FB_KEY = "rca:feedback:{feedback_id}"
_FB_BY_INVESTIGATION = "rca:feedback:by_investigation:{investigation_id}"
_FB_LIST = "rca:feedback:list"
_TTL = 86400 * 365  # 1 year

_UPSERT_FB = """
MERGE (f:RecommendationFeedback {id: $id})
SET f += $props
RETURN f
"""

_LINK_FB_TO_INVESTIGATION = """
MATCH (f:RecommendationFeedback {id: $feedback_id})
MATCH (m:InvestigationMemory {investigation_id: $investigation_id})
MERGE (f)-[:EVALUATED_BY]->(m)
"""


class FeedbackRepository:
    """Persists recommendation feedback to Redis + Neo4j."""

    def __init__(self, repo: BaseNeo4jRepository | None = None) -> None:
        self._repo = repo or BaseNeo4jRepository()

    async def save(self, feedback: RecommendationFeedback) -> bool:
        try:
            redis = get_client()
            await redis.set(
                _FB_KEY.format(feedback_id=feedback.id),
                feedback.model_dump_json(), ex=_TTL,
            )
            await redis.zadd(
                _FB_LIST,
                {feedback.id: datetime.now(timezone.utc).timestamp()},
            )
            await redis.lpush(
                _FB_BY_INVESTIGATION.format(investigation_id=feedback.investigation_id),
                feedback.id,
            )
            await self._sync_to_neo4j(feedback)
            return True
        except Exception as exc:
            log.error(f"FeedbackRepository.save failed: {exc}")
            return False

    async def get(self, feedback_id: str) -> RecommendationFeedback | None:
        try:
            redis = get_client()
            raw = await redis.get(_FB_KEY.format(feedback_id=feedback_id))
            if raw:
                return RecommendationFeedback.model_validate_json(raw)
        except Exception as exc:
            log.warning(f"Feedback Redis get failed: {exc}")
        return None

    async def list_by_investigation(
        self, investigation_id: str
    ) -> list[RecommendationFeedback]:
        try:
            redis = get_client()
            key = _FB_BY_INVESTIGATION.format(investigation_id=investigation_id)
            ids = await redis.lrange(key, 0, -1)
            results: list[RecommendationFeedback] = []
            for fid in ids:
                raw = await redis.get(_FB_KEY.format(feedback_id=fid))
                if raw:
                    results.append(RecommendationFeedback.model_validate_json(raw))
            return results
        except Exception as exc:
            log.error(f"FeedbackRepository.list_by_investigation failed: {exc}")
            return []

    async def list_recent(self, limit: int = 50) -> list[RecommendationFeedback]:
        try:
            redis = get_client()
            ids = await redis.zrevrange(_FB_LIST, 0, limit - 1)
            results = []
            for fid in ids:
                raw = await redis.get(_FB_KEY.format(feedback_id=fid))
                if raw:
                    results.append(RecommendationFeedback.model_validate_json(raw))
            return results
        except Exception as exc:
            log.error(f"FeedbackRepository.list_recent failed: {exc}")
            return []

    async def compute_effectiveness_rate(self) -> float:
        """Compute overall recommendation effectiveness rate from feedback."""
        try:
            all_feedback = await self.list_recent(limit=500)
            if not all_feedback:
                return 0.0
            successful = sum(1 for f in all_feedback if f.outcome.value in ("SUCCESSFUL", "EXECUTED"))
            return round(successful / len(all_feedback), 4)
        except Exception:
            return 0.0

    async def _sync_to_neo4j(self, feedback: RecommendationFeedback) -> None:
        props = {
            "id": feedback.id,
            "recommendation_id": feedback.recommendation_id,
            "investigation_id": feedback.investigation_id,
            "outcome": feedback.outcome.value,
            "effectiveness_score": feedback.effectiveness_score,
            "executed_at": feedback.executed_at,
        }
        try:
            await self._repo.execute_query(_UPSERT_FB, {"id": feedback.id, "props": props})
        except Exception as exc:
            log.warning(f"Neo4j feedback sync failed (non-critical): {exc}")

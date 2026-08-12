"""pattern_repository.py — FailurePattern Redis + Neo4j persistence."""
from __future__ import annotations

from app.core.logging import get_logger
from app.infrastructure.redis.client import get_client
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.root_cause.domain.models import FailurePattern

log = get_logger("root_cause.patterns.repository")

_PATTERN_KEY = "rca:pattern:{pattern_id}"
_PATTERN_LIST = "rca:pattern:list"
_TTL = 86400 * 90  # 90 days

_UPSERT_PATTERN = """
MERGE (p:FailurePattern {id: $id})
SET p += $props
RETURN p
"""


class PatternRepository:
    """Persists failure patterns to Redis + Neo4j."""

    def __init__(self, neo4j_repo: BaseNeo4jRepository | None = None) -> None:
        self._repo = neo4j_repo or BaseNeo4jRepository()

    async def save(self, pattern: FailurePattern) -> bool:
        try:
            redis = get_client()
            await redis.set(
                _PATTERN_KEY.format(pattern_id=pattern.id),
                pattern.model_dump_json(), ex=_TTL,
            )
            await redis.sadd(_PATTERN_LIST, pattern.id)
            await self._sync_to_neo4j(pattern)
            return True
        except Exception as exc:
            log.error(f"PatternRepository.save failed: {exc}")
            return False

    async def get(self, pattern_id: str) -> FailurePattern | None:
        try:
            redis = get_client()
            raw = await redis.get(_PATTERN_KEY.format(pattern_id=pattern_id))
            if raw:
                return FailurePattern.model_validate_json(raw)
        except Exception as exc:
            log.warning(f"Redis pattern fetch failed: {exc}")
        return None

    async def _sync_to_neo4j(self, pattern: FailurePattern) -> None:
        props = {
            "id": pattern.id,
            "name": pattern.name,
            "pattern_type": pattern.pattern_type.value,
            "description": pattern.description,
            "confidence_score": pattern.confidence_score,
            "prior_probability": pattern.prior_probability,
            "historical_matches": pattern.historical_matches,
            "typical_severity": pattern.typical_severity
        }
        try:
            await self._repo.execute_query(_UPSERT_PATTERN, {"id": pattern.id, "props": props})
        except Exception as exc:
            log.warning(f"Neo4j pattern sync failed: {exc}")

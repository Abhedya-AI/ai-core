"""counterfactual_engine.py — Counterfactual Analysis Engine facade."""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.redis.client import get_client
from app.modules.knowledge.infrastructure.repositories.base_repository import BaseNeo4jRepository
from app.modules.root_cause.domain.models import (
    Investigation, InvestigationReport,
    CounterfactualScenario, ScenarioType,
)
from app.modules.root_cause.counterfactual.scenario_builder import ScenarioBuilder
from app.modules.root_cause.counterfactual.what_if_analyzer import WhatIfAnalyzer

log = get_logger("root_cause.counterfactual.engine")

_CF_KEY = "rca:counterfactual:{investigation_id}"
_TTL = 86400 * 14

_UPSERT_CF = """
MERGE (c:CounterfactualScenario {id: $id})
SET c += $props
RETURN c
"""


class CounterfactualEngine:
    """Facade for counterfactual analysis: build, cache, persist, retrieve."""

    def __init__(
        self,
        analyzer: WhatIfAnalyzer | None = None,
        repo: BaseNeo4jRepository | None = None,
    ) -> None:
        self.analyzer = analyzer or WhatIfAnalyzer(ScenarioBuilder())
        self._repo = repo or BaseNeo4jRepository()

    async def analyze(
        self,
        investigation: Investigation,
        report: InvestigationReport,
        scenario_types: list[ScenarioType] | None = None,
    ) -> list[CounterfactualScenario]:
        """Generate, cache, and persist counterfactual scenarios."""
        scenarios = self.analyzer.analyze(investigation, report, scenario_types)
        ranked = self.analyzer.rank_by_impact(scenarios)
        await self._cache(investigation.id, ranked)
        await self._persist(ranked)
        return ranked

    async def get_scenarios(
        self, investigation_id: str
    ) -> list[CounterfactualScenario]:
        """Retrieve cached scenarios for an investigation."""
        try:
            redis = get_client()
            raw = await redis.get(_CF_KEY.format(investigation_id=investigation_id))
            if raw:
                import json
                data = json.loads(raw)
                return [CounterfactualScenario(**s) for s in data]
        except Exception as exc:
            log.warning(f"Counterfactual cache miss for {investigation_id}: {exc}")
        return []

    def summarize(
        self, scenarios: list[CounterfactualScenario]
    ) -> dict[str, Any]:
        return self.analyzer.summarize(scenarios)

    async def _cache(
        self, investigation_id: str, scenarios: list[CounterfactualScenario]
    ) -> None:
        try:
            import json
            redis = get_client()
            data = [s.model_dump() for s in scenarios]
            # Convert non-serialisable types to strings
            payload = json.dumps(data, default=str)
            await redis.set(
                _CF_KEY.format(investigation_id=investigation_id), payload, ex=_TTL
            )
        except Exception as exc:
            log.warning(f"Counterfactual cache write failed: {exc}")

    async def _persist(
        self, scenarios: list[CounterfactualScenario]
    ) -> None:
        for scenario in scenarios:
            props = {
                "id": scenario.id,
                "investigation_id": scenario.investigation_id,
                "scenario_type": scenario.scenario_type.value,
                "intervention_description": scenario.intervention_description,
                "risk_reduction_pct": scenario.risk_reduction_pct,
                "confidence": scenario.confidence,
                "impact_summary": scenario.impact_summary,
            }
            try:
                await self._repo.execute_query(_UPSERT_CF, {"id": scenario.id, "props": props})
            except Exception as exc:
                log.warning(f"Neo4j counterfactual sync failed (non-critical): {exc}")

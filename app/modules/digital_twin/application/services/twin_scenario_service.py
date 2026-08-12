from __future__ import annotations

import time
import uuid
from typing import Any, List
from app.core.logging import get_logger

log = get_logger(__name__)


class TwinScenarioGenerator:
    async def generate(self, twin_id: str, state: dict, entity_id: str, entity_type: str, context: dict) -> List[dict]:
        return [
            {
                "scenario_id": str(uuid.uuid4()),
                "twin_id": twin_id,
                "title": f"Scenario for {entity_id}",
                "description": "Auto-generated scenario based on current state",
                "probability": 0.75,
            }
        ]


class ScenarioComparator:
    async def compare(self, scenarios: List[dict]) -> dict:
        return {"comparison_id": str(uuid.uuid4()), "differences": "mock_diff_data"}


class BranchingTimeline:
    async def generate(self, twin_id: str, base_snapshot: dict, scenario_configs: List[dict]) -> dict:
        return {"branches": scenario_configs, "comparison": {"summary": "branch comparison"}}


class TwinScenarioService:
    def __init__(self, graphrag_service: Any = None) -> None:
        self.graphrag_service = graphrag_service
        self._generator = TwinScenarioGenerator()
        self._comparator = ScenarioComparator()
        self._branching = BranchingTimeline()

    async def generate(
        self, twin_id: str, twin_state: dict[str, Any], entity_id: str, entity_type: str, context: dict[str, Any]
    ) -> List[dict[str, Any]]:
        t0 = time.perf_counter()
        try:
            scenarios = await self._generator.generate(twin_id, twin_state, entity_id, entity_type, context)
            
            if self.graphrag_service:
                for scenario in scenarios:
                    try:
                        q = f"What are the implications of scenario {scenario['title']} for twin {twin_id}?"
                        gr_res = await self.graphrag_service.answer(q)
                        scenario["graphrag_analysis"] = gr_res.answer
                    except Exception as e:
                        log.warning(f"GraphRAG analysis failed for scenario: {e}")
            
            return scenarios
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinScenarioService.generate completed in {latency_ms:.2f}ms")

    async def compare(self, scenario_data_list: List[dict[str, Any]]) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            return await self._comparator.compare(scenario_data_list)
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinScenarioService.compare completed in {latency_ms:.2f}ms")

    async def generate_branching_timeline(
        self, twin_id: str, base_snapshot: dict[str, Any], scenario_configs: List[dict[str, Any]]
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            return await self._branching.generate(twin_id, base_snapshot, scenario_configs)
        finally:
            latency_ms = (time.perf_counter() - t0) * 1000
            log.info(f"TwinScenarioService.generate_branching_timeline completed in {latency_ms:.2f}ms")

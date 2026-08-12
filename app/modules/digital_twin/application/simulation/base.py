from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from app.core.logging import get_logger
log = get_logger(__name__)

@dataclass
class SimulationResult:
    simulation_id: str
    simulation_type: str
    status: str
    timeline: list[dict]
    summary: dict[str, Any]
    assumptions: list[str]
    kg_paths: list[str]
    graphrag_citations: list[str]
    risk_references: list[str]
    forecast_references: list[str]
    hazard_references: list[str]
    confidence: float
    alternative_scenarios: list[str]
    recommended_actions: list[str]
    latency_ms: float
    error: str | None

@runtime_checkable
class AbstractSimulation(Protocol):
    async def run(self, twin_state: dict[str, Any], parameters: dict[str, Any], graphrag_service: Any) -> SimulationResult:
        ...

    def get_type(self) -> str:
        ...

    def get_assumptions(self) -> list[str]:
        ...

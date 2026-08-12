from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any, runtime_checkable

@dataclass
class OptimizationResult:
    optimization_id: str
    target: str
    status: str
    objective: str
    solution: dict[str, Any]
    improvement_score: float  # 0-1
    baseline_score: float
    optimized_score: float
    optimization_steps: list[dict]  # [{step, action, score_delta, rationale}]
    graphrag_citations: list[str]
    risk_references: list[str]
    reasoning: str
    recommended_actions: list[str]
    latency_ms: float
    error: str | None

@runtime_checkable
class AbstractOptimizer(Protocol):
    async def optimize(self, twin_state: dict[str, Any], constraints: dict[str, Any], graphrag_service: Any) -> OptimizationResult: ...
    def get_target(self) -> str: ...
    def get_objective(self) -> str: ...

class OptimizationRegistry:
    def __init__(self):
        self._optimizers: dict[str, AbstractOptimizer] = {}

    def register(self, optimizer: AbstractOptimizer) -> None:
        self._optimizers[optimizer.get_target()] = optimizer

    def get(self, target: str) -> AbstractOptimizer | None:
        return self._optimizers.get(target)

    def list_targets(self) -> list[str]:
        return list(self._optimizers.keys())

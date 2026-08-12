from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Any

@dataclass
class PropagationResult:
    """Result of a hazard propagation model execution."""
    affected_nodes: dict[str, float]  # node_id -> intensity (0-1)
    arrival_times_minutes: dict[str, float]  # node_id -> minutes to reach intensity
    peak_intensity: float
    confidence: float
    model_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

@runtime_checkable
class AbstractPropagationModel(Protocol):
    """Protocol for all hazard propagation models."""
    async def propagate(
        self,
        source_node_id: str,
        initial_intensity: float,
        graph_nodes: list[dict],
        graph_edges: list[dict],
        context: dict[str, Any],
        time_steps: int,
    ) -> PropagationResult: ...
    def model_type(self) -> str: ...
    def applicable_hazard_types(self) -> list[str]: ...

class ModelRegistry:
    """Registry for propagation model instances."""
    def __init__(self) -> None:
        self._models: dict[str, AbstractPropagationModel] = {}

    def register(self, hazard_type: str, model: AbstractPropagationModel) -> None:
        self._models[hazard_type] = model

    def get(self, hazard_type: str) -> AbstractPropagationModel | None:
        return self._models.get(hazard_type)

    def get_all(self) -> dict[str, AbstractPropagationModel]:
        return dict(self._models)

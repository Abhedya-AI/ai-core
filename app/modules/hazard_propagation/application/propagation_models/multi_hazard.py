from __future__ import annotations
import asyncio
from typing import Any
from app.core.logging import get_logger
from app.modules.hazard_propagation.application.propagation_models.base import PropagationResult

log = get_logger(__name__)

class MultiHazardCompositeModel:
    """Orchestrates multiple hazard propagation models."""
    
    def __init__(self) -> None:
        self._models: dict[str, Any] = {}
        self._load_models()
    
    def _load_models(self) -> None:
        from app.modules.hazard_propagation.application.propagation_models.fire import FirePropagationModel
        from app.modules.hazard_propagation.application.propagation_models.gas_dispersion import GasDispersionModel
        from app.modules.hazard_propagation.application.propagation_models.heat import HeatPropagationModel
        self._models = {
            "FIRE": FirePropagationModel(),
            "GAS_LEAK": GasDispersionModel(),
            "HEAT": HeatPropagationModel()
        }

    async def propagate(
        self,
        source_node_id: str,
        initial_intensity: float,
        graph_nodes: list[dict],
        graph_edges: list[dict],
        context: dict[str, Any],
        time_steps: int,
    ) -> PropagationResult:
        log.debug(f"MultiHazardCompositeModel.propagate: source={source_node_id}")
        
        hazard_type = context.get("hazard_type", "COMPOSITE")
        tasks = []
        model_names = []
        
        for name, model in self._models.items():
            if hazard_type == name or hazard_type == "COMPOSITE" or hazard_type in model.applicable_hazard_types():
                tasks.append(model.propagate(source_node_id, initial_intensity, graph_nodes, graph_edges, context, time_steps))
                model_names.append(name)
                
        if not tasks:
            return PropagationResult({}, {}, 0.0, 0.9, self.model_type())
            
        results = await asyncio.gather(*tasks)
        
        combined_intensities = {}
        combined_arrival = {}
        contributions = {}
        
        for name, result in zip(model_names, results):
            contributions[name] = result.affected_nodes
            for nid, intensity in result.affected_nodes.items():
                combined_intensities[nid] = max(combined_intensities.get(nid, 0.0), intensity)
                if nid in result.arrival_times_minutes:
                    combined_arrival[nid] = min(combined_arrival.get(nid, float('inf')), result.arrival_times_minutes[nid])
                    
        peak = max(combined_intensities.values()) if combined_intensities else 0.0
        
        return PropagationResult(
            affected_nodes=combined_intensities,
            arrival_times_minutes=combined_arrival,
            peak_intensity=peak,
            confidence=0.75,
            model_type=self.model_type(),
            metadata={"model_contributions": contributions}
        )

    def model_type(self) -> str:
        return "ENSEMBLE"

    def applicable_hazard_types(self) -> list[str]:
        # Represents all types implicitly through delegation
        from app.modules.hazard_propagation.domain.enums import HazardType
        return [h.value for h in HazardType]

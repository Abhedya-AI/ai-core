from __future__ import annotations
from typing import Any
import time
from app.core.logging import get_logger

log = get_logger(__name__)

class PropagationService:
    def __init__(self, model_registry: dict[str, Any] | None = None) -> None:
        self._models = model_registry or {}
        self._load_default_models()
    
    def _load_default_models(self) -> None:
        try:
            from app.modules.hazard_propagation.application.propagation_models.fire import FirePropagationModel
            from app.modules.hazard_propagation.application.propagation_models.smoke import SmokePropagationModel
            from app.modules.hazard_propagation.application.propagation_models.gas_dispersion import GasDispersionModel
            from app.modules.hazard_propagation.application.propagation_models.toxic_cloud import ToxicCloudModel
            from app.modules.hazard_propagation.application.propagation_models.chemical_spill import ChemicalSpillModel
            from app.modules.hazard_propagation.application.propagation_models.flood import FloodPropagationModel
            from app.modules.hazard_propagation.application.propagation_models.heat import HeatPropagationModel
            from app.modules.hazard_propagation.application.propagation_models.pressure_wave import PressureWavePropagationModel
            from app.modules.hazard_propagation.application.propagation_models.structural_failure import StructuralFailurePropagationModel
            from app.modules.hazard_propagation.application.propagation_models.equipment_failure import EquipmentFailurePropagationModel
            from app.modules.hazard_propagation.application.propagation_models.multi_hazard import MultiHazardCompositeModel
            
            self._models = {
                "FIRE": FirePropagationModel(),
                "SMOKE": SmokePropagationModel(),
                "GAS_LEAK": GasDispersionModel(),
                "TOXIC_GAS": ToxicCloudModel(),
                "CHEMICAL_SPILL": ChemicalSpillModel(),
                "FLOOD": FloodPropagationModel(),
                "STEAM_LEAK": GasDispersionModel(),
                "HIGH_PRESSURE": PressureWavePropagationModel(),
                "EXPLOSION": PressureWavePropagationModel(),
                "STRUCTURAL_COLLAPSE": StructuralFailurePropagationModel(),
                "POWER_FAILURE": EquipmentFailurePropagationModel(),
                "ELECTRICAL_FAULT": EquipmentFailurePropagationModel(),
                "COMPOSITE": MultiHazardCompositeModel(),
                "RADIATION": GasDispersionModel(),  # approximate
            }
        except ImportError as e:
            log.warning(f"Could not load all propagation models: {e}")

    def select_model(self, hazard_type: str) -> Any:
        if hazard_type in self._models:
            return self._models[hazard_type]
        if self._models:
            return next(iter(self._models.values()))
        return None

    async def analyze(self, hazard_type: str, source_node_id: str, initial_intensity: float, nodes: dict[str, Any], edges: list[dict[str, Any]], wind_speed: float, wind_direction: float, time_steps: int, context: dict[str, Any]) -> dict[str, Any]:
        t0 = time.perf_counter()
        model = self.select_model(hazard_type)
        affected_nodes = {}
        arrival_times = {}
        peak_intensity = 0.0
        confidence = 0.8
        timeline_entries = []
        
        if model and hasattr(model, "propagate"):
            try:
                res = await model.propagate(source_node_id, initial_intensity, nodes, edges, wind_speed, wind_direction, time_steps, context)
                affected_nodes = res.get("affected_nodes", {})
                arrival_times = res.get("arrival_times", {})
                peak_intensity = res.get("peak_intensity", 0.0)
                confidence = res.get("confidence", 0.8)
                timeline_entries = res.get("timeline_entries", [])
            except Exception as e:
                log.warning(f"Error during propagation analysis: {e}")
        
        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "affected_nodes": affected_nodes,
            "arrival_times": arrival_times,
            "peak_intensity": peak_intensity,
            "model_type": model.__class__.__name__ if model else "Unknown",
            "confidence": confidence,
            "timeline_entries": timeline_entries,
            "latency_ms": latency_ms
        }
        
    def generate_timeline(self, propagation_id: str, source_node_id: str, affected_nodes: dict[str, Any]) -> dict[str, Any]:
        events = []
        for node_id, data in affected_nodes.items():
            events.append({
                "node_id": node_id,
                "intensity": data.get("intensity", 0.0),
                "arrival_time": data.get("arrival_time", 0)
            })
        events.sort(key=lambda x: x["arrival_time"])
        return {
            "propagation_id": propagation_id,
            "source_node_id": source_node_id,
            "events": events
        }

    def generate_forecast(self, propagation_id: str, hazard_type: str, source_node_id: str, affected_nodes: dict[str, Any]) -> dict[str, Any]:
        horizons = {
            "15m": {"affected_count": len([n for n, d in affected_nodes.items() if d.get("arrival_time", 0) <= 15])},
            "30m": {"affected_count": len([n for n, d in affected_nodes.items() if d.get("arrival_time", 0) <= 30])},
            "60m": {"affected_count": len([n for n, d in affected_nodes.items() if d.get("arrival_time", 0) <= 60])},
            "120m": {"affected_count": len([n for n, d in affected_nodes.items() if d.get("arrival_time", 0) <= 120])},
            "240m": {"affected_count": len([n for n, d in affected_nodes.items() if d.get("arrival_time", 0) <= 240])}
        }
        return {
            "propagation_id": propagation_id,
            "hazard_type": hazard_type,
            "source_node_id": source_node_id,
            "horizons": horizons
        }

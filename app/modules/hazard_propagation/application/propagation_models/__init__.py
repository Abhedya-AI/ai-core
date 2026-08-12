from __future__ import annotations

from app.modules.hazard_propagation.application.propagation_models.base import AbstractPropagationModel, ModelRegistry, PropagationResult
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

__all__ = [
    "AbstractPropagationModel",
    "ModelRegistry",
    "PropagationResult",
    "FirePropagationModel",
    "SmokePropagationModel",
    "GasDispersionModel",
    "ToxicCloudModel",
    "ChemicalSpillModel",
    "FloodPropagationModel",
    "HeatPropagationModel",
    "PressureWavePropagationModel",
    "StructuralFailurePropagationModel",
    "EquipmentFailurePropagationModel",
    "MultiHazardCompositeModel"
]

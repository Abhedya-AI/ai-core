from __future__ import annotations

from app.modules.digital_twin.domain.enums import EntityType
from app.modules.digital_twin.application.twin_models.base import TwinBuilderRegistry, AbstractTwinBuilder
from app.modules.digital_twin.application.twin_models.sensor_twin import SensorTwinBuilder
from app.modules.digital_twin.application.twin_models.camera_twin import CameraTwinBuilder
from app.modules.digital_twin.application.twin_models.equipment_twin import EquipmentTwinBuilder
from app.modules.digital_twin.application.twin_models.worker_twin import WorkerTwinBuilder
from app.modules.digital_twin.application.twin_models.zone_twin import ZoneTwinBuilder
from app.modules.digital_twin.application.twin_models.floor_twin import FloorTwinBuilder
from app.modules.digital_twin.application.twin_models.building_twin import BuildingTwinBuilder
from app.modules.digital_twin.application.twin_models.plant_twin import PlantTwinBuilder
from app.modules.digital_twin.application.twin_models.hazard_twin import HazardTwinBuilder
from app.modules.digital_twin.application.twin_models.resource_twin import ResourceTwinBuilder

def init_registry() -> None:
    TwinBuilderRegistry.register(EntityType.SENSOR, SensorTwinBuilder())
    TwinBuilderRegistry.register(EntityType.CAMERA, CameraTwinBuilder())
    TwinBuilderRegistry.register(EntityType.EQUIPMENT, EquipmentTwinBuilder())
    TwinBuilderRegistry.register(EntityType.WORKER, WorkerTwinBuilder())
    TwinBuilderRegistry.register(EntityType.ZONE, ZoneTwinBuilder())
    TwinBuilderRegistry.register(EntityType.FLOOR, FloorTwinBuilder())
    TwinBuilderRegistry.register(EntityType.BUILDING, BuildingTwinBuilder())
    TwinBuilderRegistry.register(EntityType.PLANT, PlantTwinBuilder())
    TwinBuilderRegistry.register(EntityType.HAZARD, HazardTwinBuilder())
    TwinBuilderRegistry.register(EntityType.RESOURCE, ResourceTwinBuilder())

init_registry()

__all__ = [
    "TwinBuilderRegistry",
    "AbstractTwinBuilder"
]

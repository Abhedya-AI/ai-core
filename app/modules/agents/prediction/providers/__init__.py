from app.modules.agents.prediction.providers.environmental import EnvironmentalRiskModel
from app.modules.agents.prediction.providers.equipment_failure import EquipmentFailureModel
from app.modules.agents.prediction.providers.incident_prediction import IncidentPredictionModel
from app.modules.agents.prediction.providers.maintenance import MaintenanceForecastModel
from app.modules.agents.prediction.providers.occupancy import OccupancyForecastModel

__all__ = [
    "EquipmentFailureModel",
    "IncidentPredictionModel",
    "MaintenanceForecastModel",
    "OccupancyForecastModel",
    "EnvironmentalRiskModel",
]

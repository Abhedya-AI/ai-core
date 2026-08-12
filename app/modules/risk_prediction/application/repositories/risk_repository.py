from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
from app.modules.risk_prediction.domain.enums import EntityType, RiskLevel
from app.modules.risk_prediction.domain.models import (
    RiskAssessment, RiskForecast, MitigationPlan, RiskScenario, RiskTimeline
)

class IRiskRepository(ABC):
    @abstractmethod
    async def save_assessment(self, assessment: RiskAssessment) -> None: ...
    
    @abstractmethod
    async def get_assessment(self, assessment_id: str) -> Optional[RiskAssessment]: ...
    
    @abstractmethod
    async def get_latest_assessment(
        self, entity_id: str, entity_type: EntityType
    ) -> Optional[RiskAssessment]: ...
    
    @abstractmethod
    async def list_assessments(
        self,
        entity_type: Optional[EntityType] = None,
        entity_id: Optional[str] = None,
        hours: int = 24,
        min_risk_level: Optional[RiskLevel] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[RiskAssessment], int]: ...
    
    @abstractmethod
    async def save_forecast(self, forecast: RiskForecast) -> None: ...
    
    @abstractmethod
    async def get_forecast(
        self, entity_id: str, entity_type: EntityType
    ) -> Optional[RiskForecast]: ...
    
    @abstractmethod
    async def save_mitigation_plan(self, plan: MitigationPlan) -> None: ...
    
    @abstractmethod
    async def get_mitigation_plan(self, plan_id: str) -> Optional[MitigationPlan]: ...
    
    @abstractmethod
    async def save_scenario(self, scenario: RiskScenario) -> None: ...
    
    @abstractmethod
    async def list_scenarios(
        self, entity_id: str, entity_type: EntityType
    ) -> List[RiskScenario]: ...
    
    @abstractmethod
    async def get_risk_history(
        self, entity_id: str, entity_type: EntityType, hours: int = 24
    ) -> RiskTimeline: ...
    
    @abstractmethod
    async def get_analytics_summary(
        self, entity_type: Optional[EntityType], hours: int = 24
    ) -> Dict[str, Any]: ...

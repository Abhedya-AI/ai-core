from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
import numpy as np
from app.modules.risk_prediction.domain.enums import ModelType

@dataclass
class ModelPrediction:
    probability: float          # 0.0-1.0
    confidence: float           # 0.0-1.0
    uncertainty: float          # std of ensemble
    feature_importance: dict[str, float]  # feature_name → importance
    explanation: str
    model_type: str
    raw_scores: dict[str, float]

class ModelNotAvailableError(Exception):
    pass

class RiskModel(ABC):
    model_type: ModelType
    
    @abstractmethod
    async def predict(self, features: np.ndarray, feature_names: list[str]) -> ModelPrediction: ...
    
    @abstractmethod
    async def predict_proba(self, features: np.ndarray) -> np.ndarray: ...
    
    @abstractmethod
    def explain(self, features: np.ndarray, feature_names: list[str]) -> dict[str, float]: ...
    
    def serialize(self) -> dict[str, Any]:
        return {"model_type": self.model_type.value}
    
    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> 'RiskModel':
        raise NotImplementedError("Deserialize not implemented for base class")
    
    def is_available(self) -> bool:
        return True

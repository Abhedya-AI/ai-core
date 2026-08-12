import numpy as np
from typing import Any
from app.modules.risk_prediction.domain.enums import ModelType
from app.modules.risk_prediction.application.risk_models.base_model import RiskModel, ModelPrediction, ModelNotAvailableError

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

class XGBoostRiskModel(RiskModel):
    model_type = ModelType.XGBOOST
    
    def __init__(self):
        self.model = None

    def is_available(self) -> bool:
        return HAS_XGBOOST and self.model is not None

    def load_model(self, path: str):
        if not HAS_XGBOOST:
            raise ModelNotAvailableError("XGBoost is not installed.")
        self.model = xgb.Booster()
        self.model.load_model(path)
        
    def save_model(self, path: str):
        if self.model is not None:
            self.model.save_model(path)

    async def predict(self, features: np.ndarray, feature_names: list[str]) -> ModelPrediction:
        if not self.is_available():
            raise ModelNotAvailableError("XGBoost model is not loaded or available.")
            
        dmatrix = xgb.DMatrix(features.reshape(1, -1), feature_names=feature_names)
        preds = self.model.predict(dmatrix)
        prob = float(preds[0])
        
        importances = self.explain(features, feature_names)
        
        return ModelPrediction(
            probability=prob,
            confidence=0.85,
            uncertainty=0.1,
            feature_importance=importances,
            explanation=f"XGBoost predicted probability: {prob:.4f}",
            model_type=self.model_type.value,
            raw_scores={"xgb_score": prob}
        )

    async def predict_proba(self, features: np.ndarray) -> np.ndarray:
        if not self.is_available():
            raise ModelNotAvailableError("XGBoost model is not loaded or available.")
        dmatrix = xgb.DMatrix(features)
        return self.model.predict(dmatrix)

    def explain(self, features: np.ndarray, feature_names: list[str]) -> dict[str, float]:
        if not self.is_available():
            return {}
        score_dict = self.model.get_score(importance_type='gain')
        # Return matched importances
        return {name: float(score_dict.get(name, 0.0)) for name in feature_names}

import numpy as np
from typing import Any
from app.modules.risk_prediction.domain.enums import ModelType
from app.modules.risk_prediction.application.risk_models.base_model import RiskModel, ModelPrediction, ModelNotAvailableError

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

class LightGBMRiskModel(RiskModel):
    model_type = ModelType.LIGHTGBM
    
    def __init__(self):
        self.model = None

    def is_available(self) -> bool:
        return HAS_LIGHTGBM and self.model is not None

    def load_model(self, path: str):
        if not HAS_LIGHTGBM:
            raise ModelNotAvailableError("LightGBM is not installed.")
        self.model = lgb.Booster(model_file=path)
        
    def save_model(self, path: str):
        if self.model is not None:
            self.model.save_model(path)

    async def predict(self, features: np.ndarray, feature_names: list[str]) -> ModelPrediction:
        if not self.is_available():
            raise ModelNotAvailableError("LightGBM model is not loaded or available.")
            
        preds = self.model.predict(features.reshape(1, -1))
        prob = float(preds[0])
        
        importances = self.explain(features, feature_names)
        
        return ModelPrediction(
            probability=prob,
            confidence=0.85,
            uncertainty=0.1,
            feature_importance=importances,
            explanation=f"LightGBM predicted probability: {prob:.4f}",
            model_type=self.model_type.value,
            raw_scores={"lgb_score": prob}
        )

    async def predict_proba(self, features: np.ndarray) -> np.ndarray:
        if not self.is_available():
            raise ModelNotAvailableError("LightGBM model is not loaded or available.")
        return self.model.predict(features)

    def explain(self, features: np.ndarray, feature_names: list[str]) -> dict[str, float]:
        if not self.is_available():
            return {}
        importance_vals = self.model.feature_importance(importance_type='gain')
        # Map back to names
        model_features = self.model.feature_name()
        importances = {name: float(val) for name, val in zip(model_features, importance_vals)}
        return {name: importances.get(name, 0.0) for name in feature_names}

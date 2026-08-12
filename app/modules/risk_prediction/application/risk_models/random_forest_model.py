import numpy as np
from typing import Any
from app.modules.risk_prediction.domain.enums import ModelType
from app.modules.risk_prediction.application.risk_models.base_model import RiskModel, ModelPrediction, ModelNotAvailableError

try:
    from sklearn.ensemble import RandomForestClassifier
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

class RandomForestRiskModel(RiskModel):
    model_type = ModelType.RANDOM_FOREST
    
    def __init__(self):
        self.model = None

    def is_available(self) -> bool:
        return True

    def fit(self, X: np.ndarray, y: np.ndarray):
        if HAS_SKLEARN:
            self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            self.model.fit(X, y)
        else:
            # Fallback bootstrap aggregation placeholder
            self.model = "fallback_trained"

    async def predict(self, features: np.ndarray, feature_names: list[str]) -> ModelPrediction:
        if self.model is None:
            # Unfitted fallback
            prob = 0.5
            explanation = "Random Forest not fitted, using fallback baseline."
            importances = {name: 1.0 / len(feature_names) for name in feature_names}
        elif HAS_SKLEARN and isinstance(self.model, RandomForestClassifier):
            probs = self.model.predict_proba(features.reshape(1, -1))
            prob = float(probs[0, 1]) if probs.shape[1] > 1 else float(probs[0, 0])
            explanation = f"Random Forest predicted probability: {prob:.4f}"
            importances = {name: float(imp) for name, imp in zip(feature_names, self.model.feature_importances_)}
        else:
            # Fallback prediction
            prob = float(np.clip(np.mean(features) / (np.max(features) + 1e-6), 0.0, 1.0))
            explanation = "Random Forest fallback prediction based on mean feature value."
            importances = {name: float(np.abs(f)) for name, f in zip(feature_names, features)}
            
        return ModelPrediction(
            probability=prob,
            confidence=0.8 if self.model is not None else 0.4,
            uncertainty=0.15,
            feature_importance=importances,
            explanation=explanation,
            model_type=self.model_type.value,
            raw_scores={"rf_score": prob}
        )

    async def predict_proba(self, features: np.ndarray) -> np.ndarray:
        if HAS_SKLEARN and isinstance(self.model, RandomForestClassifier):
            return self.model.predict_proba(features)
        return np.array([[0.5, 0.5]] * len(features))

    def explain(self, features: np.ndarray, feature_names: list[str]) -> dict[str, float]:
        if HAS_SKLEARN and isinstance(self.model, RandomForestClassifier):
            return {name: float(imp) for name, imp in zip(feature_names, self.model.feature_importances_)}
        return {name: 1.0 / len(feature_names) for name in feature_names}

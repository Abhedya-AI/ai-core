import numpy as np
from typing import Any
from app.modules.risk_prediction.domain.enums import ModelType
from app.modules.risk_prediction.application.risk_models.base_model import RiskModel, ModelPrediction

try:
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

class IsolationForestRiskModel(RiskModel):
    model_type = ModelType.ISOLATION_FOREST
    
    def __init__(self):
        self.model = None
        self.mean = None
        self.std = None

    def fit(self, X: np.ndarray):
        if HAS_SKLEARN:
            self.model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
            self.model.fit(X)
        else:
            self.mean = np.mean(X, axis=0)
            self.std = np.std(X, axis=0)
            self.std[self.std == 0] = 1e-6

    async def predict(self, features: np.ndarray, feature_names: list[str]) -> ModelPrediction:
        if HAS_SKLEARN and self.model is not None:
            score = self.model.score_samples(features.reshape(1, -1))[0]
            # Convert negative outlier factor to probability (roughly -1 to 0)
            prob = float(np.clip((-score - 0.4) / 0.4, 0.0, 1.0))
            explanation = "Sklearn Isolation Forest anomaly score converted to probability."
        else:
            # Fallback numpy implementation
            if self.mean is not None:
                dist = np.abs((features - self.mean) / self.std)
                avg_dist = np.mean(dist)
                prob = float(np.clip(avg_dist / 3.0, 0.0, 1.0)) # 3 sigma = 100% risk
                explanation = "Numpy fallback normalized distance anomaly score."
            else:
                prob = 0.2
                explanation = "Isolation Forest uncalibrated baseline."
                
        importances = self.explain(features, feature_names)
        
        return ModelPrediction(
            probability=prob,
            confidence=0.7,
            uncertainty=0.2,
            feature_importance=importances,
            explanation=explanation,
            model_type=self.model_type.value,
            raw_scores={"iforest_anomaly": prob}
        )

    async def predict_proba(self, features: np.ndarray) -> np.ndarray:
        return np.array([[0.5]])

    def explain(self, features: np.ndarray, feature_names: list[str]) -> dict[str, float]:
        if not HAS_SKLEARN and self.mean is not None:
            dist = np.abs((features - self.mean) / self.std)
            return {name: float(d) for name, d in zip(feature_names, dist)}
        return {name: float(np.abs(f)) for name, f in zip(feature_names, features)}

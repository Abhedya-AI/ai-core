from dataclasses import dataclass
from typing import Any
import numpy as np
from app.modules.risk_prediction.domain.enums import RiskType
from app.modules.risk_prediction.application.risk_models.base_model import RiskModel, ModelPrediction, ModelNotAvailableError

@dataclass
class EnsemblePrediction:
    probability: float
    confidence: float
    uncertainty: float
    model_contributions: dict[str, float]  # model → probability
    ensemble_explanation: str
    top_features: dict[str, float]  # aggregated feature importance
    available_models: list[str]

class EnsembleEngine:
    def __init__(self, models: list[RiskModel], weights: dict[str, float] | None = None):
        self.models = models
        self.weights = weights or {model.model_type.value: 1.0 for model in models}
        self.performance_history = {model.model_type.value: 1.0 for model in models}
        
    async def predict(
        self,
        features: np.ndarray,
        feature_names: list[str],
        risk_type: RiskType,
    ) -> EnsemblePrediction:
        predictions = []
        available_models = []
        
        for model in self.models:
            if model.is_available():
                try:
                    pred = await model.predict(features, feature_names)
                    predictions.append(pred)
                    available_models.append(model.model_type.value)
                except ModelNotAvailableError:
                    pass
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Model {model.model_type.value} failed to predict: {e}")
                    
        if not predictions:
            raise RuntimeError("No models available for prediction")
            
        selected_preds = self._select_best_models(predictions)
        
        avg_prob = self._weighted_average(selected_preds)
        uncertainty = self._compute_uncertainty([p.probability for p in selected_preds])
        
        avg_confidence = sum(p.confidence for p in selected_preds) / len(selected_preds)
        calibrated_confidence = self._calibrate_confidence(avg_confidence, uncertainty)
        
        contributions = {p.model_type: p.probability for p in selected_preds}
        
        # Aggregate feature importance
        top_features = {}
        for p in selected_preds:
            for feat, imp in p.feature_importance.items():
                top_features[feat] = top_features.get(feat, 0.0) + imp
        total_imp = sum(top_features.values())
        if total_imp > 0:
            top_features = {k: v / total_imp for k, v in top_features.items()}
            
        explanation = f"Ensemble prediction aggregated from {len(selected_preds)} models. Uncertainty: {uncertainty:.2f}"
        
        return EnsemblePrediction(
            probability=avg_prob,
            confidence=calibrated_confidence,
            uncertainty=uncertainty,
            model_contributions=contributions,
            ensemble_explanation=explanation,
            top_features=top_features,
            available_models=available_models
        )
        
    def _weighted_average(self, predictions: list[ModelPrediction]) -> float:
        total_weight = 0.0
        weighted_sum = 0.0
        for p in predictions:
            w = self.weights.get(p.model_type, 1.0) * self.performance_history.get(p.model_type, 1.0)
            weighted_sum += p.probability * w
            total_weight += w
        if total_weight == 0:
            return sum(p.probability for p in predictions) / len(predictions)
        return float(np.clip(weighted_sum / total_weight, 0.0, 1.0))
        
    def _calibrate_confidence(self, raw_confidence: float, uncertainty: float) -> float:
        # Lower confidence if uncertainty is high
        penalty = uncertainty * 0.5
        return float(np.clip(raw_confidence - penalty, 0.0, 1.0))
        
    def _compute_uncertainty(self, probabilities: list[float]) -> float:
        if len(probabilities) < 2:
            return 0.1
        return float(np.std(probabilities))
        
    def _select_best_models(self, available: list[ModelPrediction]) -> list[ModelPrediction]:
        # Filter out predictions with zero confidence or completely anomalous results
        selected = [p for p in available if p.confidence > 0.1]
        if not selected:
            return available
        return selected
        
    def update_weights_dynamic(self, model_type: str, performance_delta: float):
        # performance_delta could be based on actual vs predicted Brier score
        current = self.performance_history.get(model_type, 1.0)
        self.performance_history[model_type] = max(0.1, min(2.0, current + performance_delta))

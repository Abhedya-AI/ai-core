import numpy as np
from typing import Any
from app.modules.risk_prediction.domain.enums import ModelType, RiskType
from app.modules.risk_prediction.application.risk_models.base_model import RiskModel, ModelPrediction

class BayesianRiskModel(RiskModel):
    model_type = ModelType.BAYESIAN
    
    def __init__(self, risk_type: RiskType = RiskType.EQUIPMENT_FAILURE):
        self.risk_type = risk_type
        self.base_rates = {
            RiskType.EQUIPMENT_FAILURE: 0.05,
            RiskType.FIRE: 0.01,
            RiskType.GAS_LEAK: 0.02,
            RiskType.WORKER_INJURY: 0.03,
            RiskType.EXPLOSION: 0.005,
            RiskType.ELECTRICAL_FAULT: 0.04,
            RiskType.STRUCTURAL_FAILURE: 0.01,
            RiskType.CHEMICAL_SPILL: 0.015,
            RiskType.ENVIRONMENTAL: 0.02,
            RiskType.OPERATIONAL: 0.06,
            RiskType.COMPLIANCE: 0.05,
            RiskType.CYBER_PHYSICAL: 0.01,
            RiskType.COMPOSITE: 0.03
        }
        self.prior = self.base_rates.get(self.risk_type, 0.05)
        
    async def predict(self, features: np.ndarray, feature_names: list[str]) -> ModelPrediction:
        # P(H|E) = P(E|H) * P(H) / P(E)
        # Using naive bayes simplification: multiply odds
        odds = self.prior / (1.0 - self.prior)
        importances = {}
        
        feature_dict = dict(zip(feature_names, features.tolist()))
        
        for name, val in feature_dict.items():
            likelihood_ratio = 1.0
            
            # Simple feature evidence likelihood ratios
            if 'anomaly' in name and val > 0:
                likelihood_ratio = 1.0 + (val * 0.5)
            elif 'score' in name:
                likelihood_ratio = 1.0 + (val * 0.3)
            elif 'count' in name and val > 0:
                likelihood_ratio = 1.0 + (val * 0.1)
                
            odds *= likelihood_ratio
            if likelihood_ratio > 1.0:
                importances[name] = likelihood_ratio
                
        posterior = odds / (1.0 + odds)
        posterior = float(np.clip(posterior, 0.0, 1.0))
        
        # Normalize importances
        total_imp = sum(importances.values())
        if total_imp > 0:
            importances = {k: v / total_imp for k, v in importances.items()}
            
        return ModelPrediction(
            probability=posterior,
            confidence=0.75,
            uncertainty=0.2,
            feature_importance=importances,
            explanation=f"Bayesian update from prior {self.prior:.4f} to posterior {posterior:.4f}.",
            model_type=self.model_type.value,
            raw_scores={"posterior_odds": odds}
        )

    async def predict_proba(self, features: np.ndarray) -> np.ndarray:
        return np.array([[0.5]])

    def explain(self, features: np.ndarray, feature_names: list[str]) -> dict[str, float]:
        importances = {}
        feature_dict = dict(zip(feature_names, features.tolist()))
        for name, val in feature_dict.items():
            if 'anomaly' in name and val > 0:
                importances[name] = 1.0 + (val * 0.5)
            elif 'score' in name:
                importances[name] = 1.0 + (val * 0.3)
            elif 'count' in name and val > 0:
                importances[name] = 1.0 + (val * 0.1)
        total_imp = sum(importances.values())
        if total_imp > 0:
            return {k: v / total_imp for k, v in importances.items()}
        return {name: 1.0 / len(feature_names) for name in feature_names}

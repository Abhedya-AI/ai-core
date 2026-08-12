from __future__ import annotations

import asyncio
import numpy as np
from typing import Any
from .base import ForecastModelResult, AbstractForecastModel
from .statistical import ARIMAForecastModel, ExponentialSmoothingModel
from .prophet_model import ProphetForecastAbstraction
from .bayesian_model import BayesianForecastAbstraction
from .rule_based import RuleBasedForecastModel

class ForecastEnsemble:
    def __init__(self, models: list[AbstractForecastModel] | None = None, weights: list[float] | None = None) -> None:
        if models is None:
            self.models = [
                ARIMAForecastModel(),
                ExponentialSmoothingModel(),
                ProphetForecastAbstraction(),
                BayesianForecastAbstraction(),
                RuleBasedForecastModel()
            ]
        else:
            self.models = models
            
        if weights is None:
            self.weights = [1.0 / len(self.models)] * len(self.models)
        else:
            self.weights = weights

    async def train_all(self, time_series: list[float], timestamps: list[str]) -> None:
        tasks = [model.train(time_series, timestamps) for model in self.models]
        await asyncio.gather(*tasks)

    async def forecast_ensemble(self, steps: int, context: dict[str, Any]) -> ForecastModelResult:
        tasks = [model.forecast(steps, context) for model in self.models]
        results: list[ForecastModelResult] = await asyncio.gather(*tasks)
        
        preds_matrix = np.array([res.predicted_values for res in results])
        lower_matrix = np.array([res.confidence_lower for res in results])
        upper_matrix = np.array([res.confidence_upper for res in results])
        
        w = np.array(self.weights)
        
        ensemble_preds = np.average(preds_matrix, axis=0, weights=w)
        
        # Confidence bands: weighted average of bands, plus variance between models
        variance_between = np.average((preds_matrix - ensemble_preds)**2, axis=0, weights=w)
        ensemble_lower = np.average(lower_matrix, axis=0, weights=w) - np.sqrt(variance_between)
        ensemble_upper = np.average(upper_matrix, axis=0, weights=w) + np.sqrt(variance_between)
        
        avg_confidence = float(np.average([res.confidence_score for res in results], weights=w))
        avg_uncertainty = float(np.average([res.uncertainty_score for res in results], weights=w))
        
        return ForecastModelResult(
            predicted_values=ensemble_preds.tolist(),
            confidence_lower=ensemble_lower.tolist(),
            confidence_upper=ensemble_upper.tolist(),
            confidence_score=avg_confidence,
            feature_importance={f"model_{i}": float(w[i]) for i in range(len(w))},
            model_family="Ensemble",
            methodology="Weighted Average Ensemble",
            uncertainty_score=avg_uncertainty,
            metadata={"num_models": len(self.models)}
        )

    def update_weights(self, performance_scores: list[float]) -> None:
        """Softmax normalization of weights based on accuracy scores."""
        scores = np.array(performance_scores)
        e_x = np.exp(scores - np.max(scores))
        self.weights = (e_x / e_x.sum()).tolist()

    def explain_ensemble(self) -> dict[str, Any]:
        return {
            "model_weights": self.weights,
            "model_explanations": [model.explain() for model in self.models]
        }

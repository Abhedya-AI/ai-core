from __future__ import annotations

import math
import numpy as np
from typing import Any
from .base import ForecastModelResult

class BayesianForecastAbstraction:
    def __init__(self, prior_mean: float = 0.0, prior_var: float = 1.0) -> None:
        self.prior_mean = prior_mean
        self.prior_var = prior_var
        self.posterior_mean = prior_mean
        self.posterior_var = prior_var
        self.likelihood_var: float = 1.0
        self.history: list[float] = []

    async def train(self, time_series: list[float], timestamps: list[str]) -> None:
        self.history = time_series.copy()
        if not time_series:
            return
            
        data = np.array(time_series, dtype=float)
        n = len(data)
        sample_mean = np.mean(data)
        sample_var = np.var(data) if n > 1 else 1.0
        self.likelihood_var = float(sample_var)
        
        # Conjugate Gaussian update
        # Posterior precision = prior precision + data precision
        prior_prec = 1.0 / max(self.prior_var, 1e-9)
        data_prec = n / max(self.likelihood_var, 1e-9)
        post_prec = prior_prec + data_prec
        
        self.posterior_var = 1.0 / post_prec
        self.posterior_mean = float((prior_prec * self.prior_mean + data_prec * sample_mean) / post_prec)

    async def forecast(self, steps: int, context: dict[str, Any]) -> ForecastModelResult:
        if not self.history:
            raise ValueError("Model not trained")
            
        preds = [self.posterior_mean] * steps
        
        conf_lower = []
        conf_upper = []
        # Total variance grows over time
        for i in range(steps):
            total_var = self.posterior_var + self.likelihood_var * (i + 1)
            std_dev = math.sqrt(total_var)
            margin = 1.96 * std_dev
            conf_lower.append(float(preds[i] - margin))
            conf_upper.append(float(preds[i] + margin))

        return ForecastModelResult(
            predicted_values=preds,
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            confidence_score=self.confidence(),
            feature_importance={"prior_weight": self.prior_var / (self.posterior_var + 1e-9)},
            model_family="Bayesian",
            methodology="Conjugate Gaussian Update",
            uncertainty_score=math.sqrt(self.posterior_var) / (abs(self.posterior_mean) + 1e-9),
            metadata={"posterior_var": self.posterior_var}
        )

    def confidence(self) -> float:
        # High if posterior variance is smaller than prior variance
        return float(max(0.0, min(1.0, 1.0 - (self.posterior_var / max(self.prior_var, 1e-9)))))

    def explain(self) -> dict[str, Any]:
        return {
            "prior_mean": self.prior_mean,
            "prior_var": self.prior_var,
            "posterior_mean": self.posterior_mean,
            "posterior_var": self.posterior_var,
            "likelihood_var": self.likelihood_var
        }

    def serialize(self) -> dict[str, Any]:
        return {
            "prior_mean": self.prior_mean,
            "prior_var": self.prior_var,
            "posterior_mean": self.posterior_mean,
            "posterior_var": self.posterior_var,
            "likelihood_var": self.likelihood_var
        }

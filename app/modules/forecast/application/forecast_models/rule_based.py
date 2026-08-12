from __future__ import annotations

import math
import numpy as np
from typing import Any
from .base import ForecastModelResult

class RuleBasedForecastModel:
    def __init__(self, rules: list[dict[str, Any]] | None = None) -> None:
        self.rules = rules or []
        self.baseline: float = 0.0
        self.residual_std: float = 0.0
        self.matched_rules: list[dict[str, Any]] = []

    async def train(self, time_series: list[float], timestamps: list[str]) -> None:
        if not time_series:
            return
        series = np.array(time_series, dtype=float)
        self.baseline = float(np.mean(series))
        self.residual_std = float(np.std(series))
        
        # Build simple index/threshold detection if rules depend on history
        # For simplicity, we just store baseline statistics
        
    async def forecast(self, steps: int, context: dict[str, Any]) -> ForecastModelResult:
        preds = []
        conf_lower = []
        conf_upper = []
        
        self.matched_rules = []
        adjustment = 0.0
        rule_conf_penalty = 0.0
        
        for rule in self.rules:
            condition = rule.get("condition", lambda ctx: False)
            # Evaluate as string condition in context if it's a simple key check
            if isinstance(condition, str) and context.get(condition):
                adjustment += rule.get("forecast_adjustment", 0.0)
                rule_conf_penalty += (1.0 - rule.get("confidence", 1.0))
                self.matched_rules.append(rule)
        
        base_pred = self.baseline + adjustment
        
        for i in range(steps):
            preds.append(base_pred)
            margin = 1.96 * self.residual_std * math.sqrt(i + 1) * (1.0 + rule_conf_penalty)
            conf_lower.append(base_pred - margin)
            conf_upper.append(base_pred + margin)

        return ForecastModelResult(
            predicted_values=preds,
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            confidence_score=self.confidence(),
            feature_importance={"rules_fired": len(self.matched_rules)},
            model_family="Rule-Based",
            methodology="Deterministic adjustments over baseline",
            uncertainty_score=self.residual_std / (abs(self.baseline) + 1e-9),
            metadata={"rules_applied": len(self.matched_rules)}
        )

    def confidence(self) -> float:
        base_conf = 0.8
        for rule in self.matched_rules:
            base_conf *= rule.get("confidence", 1.0)
        return float(base_conf)

    def explain(self) -> dict[str, Any]:
        return {
            "baseline": self.baseline,
            "fired_rules": [r.get("name", "unnamed_rule") for r in self.matched_rules],
            "total_adjustment": sum(r.get("forecast_adjustment", 0.0) for r in self.matched_rules)
        }

    def serialize(self) -> dict[str, Any]:
        return {
            "baseline": self.baseline,
            "residual_std": self.residual_std,
            "rules_count": len(self.rules)
        }

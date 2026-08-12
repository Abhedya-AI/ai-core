from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)

class ScenarioComparator:
    async def compare(self, scenarios: list[dict[str, Any]]) -> dict[str, Any]:
        if not scenarios:
            return {}
            
        risk_deltas = [s.get("risk_delta", 0.0) for s in scenarios]
        best_scenario = min(scenarios, key=lambda s: s.get("risk_delta", 0.0))
        worst_scenario = max(scenarios, key=lambda s: s.get("risk_delta", 0.0))
        
        spread = max(risk_deltas) - min(risk_deltas)
        
        # recommended = scenario with best (lowest) risk_delta weighted by probability
        recommended = min(scenarios, key=lambda s: s.get("risk_delta", 0.0) * (1.0 - s.get("probability", 0.0)))
        
        comparison_matrix = []
        for s in scenarios:
            comparison_matrix.append({
                "scenario_type": s.get("scenario_type", "UNKNOWN"),
                "risk_delta": s.get("risk_delta", 0.0),
                "health_delta": s.get("health_delta", 0.0),
                "probability": s.get("probability", 0.0),
                "confidence": s.get("confidence", 0.0),
                "key_drivers": s.get("key_drivers", [])
            })
            
        return {
            "best_outcome": best_scenario.get("scenario_type"),
            "worst_outcome": worst_scenario.get("scenario_type"),
            "spread": spread,
            "recommended": recommended.get("scenario_type"),
            "comparison_matrix": comparison_matrix,
            "key_differentiators": ["risk_delta", "health_delta"]
        }

    async def rank_scenarios(self, scenarios: list[dict[str, Any]], weight_risk: float = 0.6, weight_probability: float = 0.4) -> list[dict[str, Any]]:
        ranked = []
        for s in scenarios:
            risk = s.get("risk_delta", 0.0)
            prob = s.get("probability", 0.0)
            # lower composite_score is better (less risk, higher probability)
            score = (risk * weight_risk) + ((1.0 - prob) * weight_probability)
            s_copy = dict(s)
            s_copy["composite_score"] = score
            ranked.append(s_copy)
            
        ranked.sort(key=lambda x: x["composite_score"])
        for i, s in enumerate(ranked):
            s["rank"] = i + 1
            
        return ranked

    def compute_scenario_spread(self, scenarios: list[dict[str, Any]]) -> dict[str, float]:
        if not scenarios:
            return {"risk_spread": 0.0, "health_spread": 0.0, "probability_variance": 0.0}
            
        risks = [s.get("risk_delta", 0.0) for s in scenarios]
        healths = [s.get("health_delta", 0.0) for s in scenarios]
        probs = [s.get("probability", 0.0) for s in scenarios]
        
        return {
            "risk_spread": float(max(risks) - min(risks)),
            "health_spread": float(max(healths) - min(healths)),
            "probability_variance": float(max(probs) - min(probs))
        }

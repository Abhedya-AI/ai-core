from __future__ import annotations
import numpy as np
from app.core.logging import get_logger

log = get_logger(__name__)

class CascadeProbabilityCalculator:
    """Calculates probabilities for hazard cascades."""

    def __init__(self, n_samples: int = 500) -> None:
        self.n_samples = n_samples

    def compute_cascade_probability_mc(self, hazard_type: str, intensity: float, environmental_factors: dict, n_samples: int | None = None) -> dict:
        """Monte Carlo simulation for cascade probability."""
        samples = n_samples if n_samples else self.n_samples
        
        # Simplified simulation
        base_prob = 0.5  # placeholder base
        adjusted_prob = base_prob * intensity
        
        random_vals = np.random.uniform(0, 1, samples)
        successes = np.sum(adjusted_prob > random_vals)
        
        prob = successes / samples
        std = np.sqrt(prob * (1 - prob) / samples)
        
        return {
            "probability": float(prob),
            "ci_lower": max(0.0, float(prob - 1.96 * std)),
            "ci_upper": min(1.0, float(prob + 1.96 * std)),
            "std": float(std)
        }

    def bayesian_update(self, prior_prob: float, evidence_intensity: float, evidence_weight: float = 0.5) -> float:
        """Update probability with new evidence."""
        p_post = prior_prob * evidence_intensity * evidence_weight + prior_prob * (1.0 - evidence_weight)
        return max(0.0, min(1.0, p_post))

    def compute_joint_cascade_probability(self, cascade_chain: list[dict]) -> float:
        """Product of probabilities."""
        if not cascade_chain:
            return 0.0
        prob = 1.0
        for stage in cascade_chain:
            prob *= stage.get("probability", 1.0)
        return prob

    def sensitivity_analysis(self, base_intensity: float, variations: list[float], hazard_type: str) -> dict[str, float]:
        """Analyze probability across variations."""
        results = {}
        for var in variations:
            # Fake logic for simulation
            prob = max(0.0, min(1.0, base_intensity * var * 0.5))
            results[str(var)] = prob
        return results

    def compute_domino_effect_probability(self, stages: list[float]) -> float:
        """Compute domino probability with correlation."""
        if not stages:
            return 0.0
        prob = 1.0
        for p in stages:
            prob *= p
            
        correlation_factor = max(0.3, 1.0 - len(stages) * 0.1)
        return prob * correlation_factor

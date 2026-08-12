"""
app/modules/risk_prediction/application/services/risk_scoring_service.py
Converts raw ML probabilities into calibrated RiskScore objects
with confidence intervals, composite risk computation, and uncertainty quantification.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

from app.modules.risk_prediction.domain.enums import (
    EntityType,
    FeatureCategory,
    RiskType,
)
from app.modules.risk_prediction.domain.models import (
    RiskConfidence,
    RiskEvidence,
    RiskFactor,
    RiskScore,
)

if TYPE_CHECKING:
    from app.modules.risk_prediction.application.feature_engineering.feature_collector import FeatureVector


class RiskScoringService:
    """Converts raw ML probabilities into calibrated RiskScore objects
    with confidence intervals and uncertainty quantification."""

    # Default composite dimension weights
    DEFAULT_COMPOSITE_WEIGHTS: dict[str, float] = {
        "equipment": 0.30,
        "worker": 0.25,
        "zone": 0.20,
        "environmental": 0.15,
        "operational": 0.10,
    }

    def compute_risk_score(
        self,
        raw_probability: float,
        confidence: RiskConfidence,
        uncertainty: float,
        risk_type: RiskType,
    ) -> RiskScore:
        """Calibrate raw probability using Platt scaling approximation,
        adjust for feature completeness, and return RiskScore."""
        calibrated_prob = self.calibrate_probability(raw_probability)
        # Adjust confidence by completeness ratio
        adjusted_confidence = confidence.overall * confidence.completeness_ratio
        adjusted_confidence = float(np.clip(adjusted_confidence, 0.0, 1.0))

        return RiskScore.from_probability(
            probability=calibrated_prob,
            confidence=adjusted_confidence,
            uncertainty=float(np.clip(uncertainty, 0.0, 1.0)),
        )

    def compute_composite_risk(
        self,
        dimension_scores: dict[str, float],  # dimension → probability
        dimension_weights: dict[str, float],  # dimension → weight
    ) -> RiskScore:
        """Weighted geometric mean of multiple risk dimensions.
        Uses geometric mean (not arithmetic) to avoid masking high-risk dimensions."""
        if not dimension_scores:
            return RiskScore.from_probability(0.0)

        log_sum = 0.0
        weight_sum = 0.0

        for dim, score in dimension_scores.items():
            weight = dimension_weights.get(dim, 1.0)
            clamped_score = max(score, 1e-9)
            log_sum += weight * math.log(clamped_score)
            weight_sum += weight

        if weight_sum == 0:
            return RiskScore.from_probability(0.0)

        geo_mean = math.exp(log_sum / weight_sum)
        return RiskScore.from_probability(float(np.clip(geo_mean, 0.0, 1.0)))

    def compute_confidence(
        self,
        feature_vector_completeness: dict[str, float],  # category → completeness
        model_confidences: list[float],
        base_confidence: float = 0.8,
    ) -> RiskConfidence:
        """Compute RiskConfidence from feature completeness and model agreement."""
        # Aggregate category-level completeness
        sensor_completeness = feature_vector_completeness.get("SENSOR", 0.0)
        vision_completeness = feature_vector_completeness.get("VISION", 0.0)
        graph_completeness = feature_vector_completeness.get("GRAPH", 0.0)
        graphrag_completeness = feature_vector_completeness.get("GRAPHRAG", 0.0)

        # Average completeness across available categories
        available = [v for v in feature_vector_completeness.values()]
        avg_completeness = sum(available) / len(available) if available else 0.5

        # Model agreement from confidences
        avg_model_confidence = (
            sum(model_confidences) / len(model_confidences)
            if model_confidences
            else base_confidence
        )

        overall = float(np.clip(base_confidence * avg_completeness * avg_model_confidence, 0.0, 1.0))

        return RiskConfidence(
            overall=overall,
            sensor_completeness=float(np.clip(sensor_completeness, 0.0, 1.0)),
            vision_completeness=float(np.clip(vision_completeness, 0.0, 1.0)),
            graph_completeness=float(np.clip(graph_completeness, 0.0, 1.0)),
            graphrag_completeness=float(np.clip(graphrag_completeness, 0.0, 1.0)),
        )

    def calibrate_probability(
        self,
        raw_prob: float,
        a: float = 1.0,
        b: float = 0.0,
    ) -> float:
        """Platt scaling: calibrated = 1 / (1 + exp(a * raw_prob + b)).
        With default a=1, b=0: maps [0,1] through sigmoid, which compresses extremes.
        We invert the sign convention so high raw_prob → high calibrated_prob."""
        try:
            # Standard Platt: f(x) = 1/(1+exp(a*x+b))
            # For risk: use negative so high prob stays high
            exp_term = math.exp(a * (1.0 - raw_prob) + b)
            calibrated = 1.0 / (1.0 + exp_term)
            return float(np.clip(calibrated, 0.0, 1.0))
        except OverflowError:
            return 0.0 if raw_prob < 0.5 else 1.0

    def compute_uncertainty(self, probabilities: list[float]) -> float:
        """Ensemble disagreement (std of predictions)."""
        if not probabilities or len(probabilities) < 2:
            return 0.0
        return float(np.std(probabilities))

    def extract_top_factors(
        self,
        feature_importance: dict[str, float],
        feature_vector: "FeatureVector",
        limit: int = 10,
    ) -> list[RiskFactor]:
        """Convert feature importance dict into sorted list of RiskFactor objects."""
        if not feature_importance:
            return []

        sorted_items = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        top_items = sorted_items[:limit]

        # Build feature name → feature object lookup for metadata
        feature_lookup = {f.name: f for f in feature_vector.features}

        factors = []
        total_importance = sum(imp for _, imp in top_items) or 1.0

        for feature_name, importance in top_items:
            feature_obj = feature_lookup.get(feature_name)
            category = feature_obj.category if feature_obj else FeatureCategory.SENSOR
            current_value = feature_obj.value if feature_obj else 0.0

            factors.append(
                RiskFactor(
                    name=feature_name,
                    weight=float(np.clip(importance / total_importance, 0.0, 1.0)),
                    contribution=float(np.clip(importance, 0.0, 1.0)),
                    category=category,
                    description=(
                        f"Feature '{feature_name}' has importance score {importance:.3f} "
                        f"(current value: {current_value:.3f})"
                    ),
                )
            )

        return factors

    def build_explanation(
        self,
        risk_score: RiskScore,
        top_factors: list[RiskFactor],
        evidence: list[RiskEvidence],
        risk_type: RiskType,
        entity_type: EntityType,
    ) -> str:
        """Generate a human-readable explanation of the risk prediction."""
        level_str = risk_score.level.value if hasattr(risk_score.level, "value") else str(risk_score.level)
        value_str = f"{risk_score.value:.2f}"

        parts = [
            f"{level_str} {risk_type.value} risk detected for {entity_type.value} (score: {value_str}).",
        ]

        if top_factors:
            factor_descriptions = [
                f"{f.name} (contribution: {f.contribution:.2f})"
                for f in top_factors[:5]
            ]
            parts.append(f"Primary drivers: {', '.join(factor_descriptions)}.")

        if evidence:
            source_names = list({e.source for e in evidence})[:3]
            parts.append(f"Evidence from: {', '.join(source_names)}.")

        return " ".join(parts)

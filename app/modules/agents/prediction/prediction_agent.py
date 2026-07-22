"""
prediction_agent.py — Master Predictive Intelligence Agent.

Shifts system from reactive to proactive by forecasting future state probabilities.
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.types import Capability
from app.modules.agents.prediction.anomaly import AnomalyDetector
from app.modules.agents.prediction.calibration import ProbabilityCalibrator
from app.modules.agents.prediction.confidence import PredictionConfidenceEngine
from app.modules.agents.prediction.events import PredictionEventGenerator
from app.modules.agents.prediction.explanation import PredictionExplanationGenerator
from app.modules.agents.prediction.feature_engineering import FeatureEngineer
from app.modules.agents.prediction.forecasting import MultiHorizonForecaster
from app.modules.agents.prediction.model_registry import PredictionModelRegistry
from app.modules.agents.prediction.models import PredictionAgentResult, PredictionOutput, PredictionWindow
from app.modules.agents.prediction.recommendation import PredictiveRecommendationEngine

log = get_logger("agents.prediction.orchestrator")


class PredictionAgent(BaseAgent):
    """
    Master Predictive Intelligence Agent.

    Orchestrates:
      Context -> Feature Engineering -> Model Registry Inference -> Multi-Horizon Forecasting -> Confidence Engine -> XAI Explanation -> Recommendations -> Event Generation.
    """

    name: str = "PredictionAgent"
    version: str = "1.0.0"
    description: str = "Evaluates AI predictive failure forecasts and remaining useful life (RUL)."
    capabilities: list[Capability] = [Capability.PREDICTION]

    def __init__(self) -> None:
        super().__init__()
        self.registry = PredictionModelRegistry.get()
        self.forecaster = MultiHorizonForecaster()

    async def can_handle(self, context: AgentContext) -> bool:
        return True

    async def _run(self, context: AgentContext) -> AgentResult:
        # 1. Feature Engineering
        features = FeatureEngineer.extract_features(context)

        # 2. Multi-Horizon Forecasting across providers
        all_predictions: list[PredictionOutput] = []

        models_to_run = ["equipment_failure", "incident_prediction", "maintenance"]
        for m_name in models_to_run:
            windows = [
                PredictionWindow(horizon_hours=1.0, horizon_label="1h"),
                PredictionWindow(horizon_hours=24.0, horizon_label="24h"),
                PredictionWindow(horizon_hours=168.0, horizon_label="7d"),
            ]
            forecasts = self.forecaster.forecast_horizons(m_name, features, windows)
            all_predictions.extend(forecasts)

        # 3. Probability Calibration & Confidence Calculation
        for p in all_predictions:
            p.probability = ProbabilityCalibrator.calibrate(p.probability)
            p.confidence = PredictionConfidenceEngine.calculate_confidence(features, p.confidence.model_confidence)

        # 4. Feature Importance Explanations
        explanations = []
        for p in all_predictions:
            if p.probability > 0.30:
                explanations.append(PredictionExplanationGenerator.generate_explanation(p, features))

        # 5. Categorized Action Recommendations
        recs = PredictiveRecommendationEngine.generate_recommendations(all_predictions)
        flattened_recs = []
        for k, v in recs.items():
            flattened_recs.extend(v)

        # 6. Domain Event Generation
        events = PredictionEventGenerator.generate_events(self.name, all_predictions, context.trace_id)

        evidence_items = [f"Generated {len(all_predictions)} predictive forecasts across 3 time horizons"]
        anomalies = AnomalyDetector.detect_anomalies(features)
        evidence_items.extend(anomalies)

        horizons = list(dict.fromkeys(p.prediction_window.horizon_label for p in all_predictions))

        avg_confidence = round(sum(p.confidence.overall_confidence for p in all_predictions) / max(1, len(all_predictions)), 2)

        return PredictionAgentResult(
            agent_name=self.name,
            success=True,
            confidence=avg_confidence,
            evidence=evidence_items,
            recommendations=flattened_recs,
            recommended_actions=recs,
            events=events,
            predictions=all_predictions,
            forecast_horizons=horizons,
            feature_explanations=explanations,
            output_data={
                "target_id": features.target_entity_id,
                "prediction_count": len(all_predictions),
                "horizons": horizons,
                "recommended_actions": recs,
            },
            explanation="\n\n".join(explanations) if explanations else "All equipment and zone parameters normal.",
        )

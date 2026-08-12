from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import uuid
import numpy as np

from app.modules.risk_prediction.domain.enums import EntityType, RiskType, ForecastHorizon
from app.modules.risk_prediction.domain.models import RiskForecast, RiskPrediction, RiskRecommendation, RiskWindow, RiskEvidence, RiskTrend, RiskScore
from app.modules.risk_prediction.domain.enums import TrendDirection
from app.modules.risk_prediction.application.ensemble.ensemble_engine import EnsembleEngine

class TimeSeriesEngine:
    # Placeholder for actual TimeSeriesEngine
    def get_trend_slope(self, entity_id: str, risk_type: RiskType) -> float:
        return 0.05

FeatureVector = dict[str, float]

class MultiHorizonForecaster:
    def __init__(self, ensemble_engine: EnsembleEngine, ts_engine: TimeSeriesEngine):
        self.ensemble_engine = ensemble_engine
        self.ts_engine = ts_engine
        
    async def generate_forecast(
        self,
        entity_id: str,
        entity_type: EntityType,
        feature_vector: FeatureVector,
        risk_type: RiskType,
        horizons: list[ForecastHorizon] | None = None,
    ) -> RiskForecast:
        if horizons is None:
            horizons = [
                ForecastHorizon.FIVE_MIN,
                ForecastHorizon.FIFTEEN_MIN,
                ForecastHorizon.THIRTY_MIN,
                ForecastHorizon.ONE_HOUR,
                ForecastHorizon.SIX_HOUR,
                ForecastHorizon.TWENTY_FOUR_HOUR,
                ForecastHorizon.SEVEN_DAY
            ]
            
        feature_names = list(feature_vector.keys())
        features = np.array(list(feature_vector.values()), dtype=float)
        
        ensemble_pred = await self.ensemble_engine.predict(features, feature_names, risk_type)
        base_prob = ensemble_pred.probability
        base_conf = ensemble_pred.confidence
        
        trend_slope = self.ts_engine.get_trend_slope(entity_id, risk_type)
        
        predictions = []
        probs = []
        now = datetime.now(timezone.utc)
        
        for horizon in horizons:
            horizon_mins = horizon.minutes
            adjusted_prob = base_prob
            
            trend_contribution = max(-0.3, min(0.3, trend_slope * horizon_mins * 0.001))
            
            if horizon == ForecastHorizon.FIVE_MIN:
                adjusted_prob = base_prob
                conf_factor = 1.0
            elif horizon == ForecastHorizon.FIFTEEN_MIN:
                adjusted_prob = (base_prob * 1.05) + trend_contribution
                conf_factor = 0.95
            elif horizon == ForecastHorizon.THIRTY_MIN:
                adjusted_prob = (base_prob * 1.1) + (trend_contribution * 2)
                conf_factor = 0.92
            elif horizon == ForecastHorizon.ONE_HOUR:
                adjusted_prob = (base_prob * 1.15) + (trend_contribution * 3)
                conf_factor = 0.9
            elif horizon == ForecastHorizon.SIX_HOUR:
                adjusted_prob = (base_prob * 1.2) + (trend_contribution * 5)
                conf_factor = 0.75
            elif horizon == ForecastHorizon.TWENTY_FOUR_HOUR:
                # mean reversion towards historical average (assuming 0.2)
                adjusted_prob = (base_prob * 0.8) + 0.04 + (trend_contribution * 2)
                conf_factor = 0.6
            elif horizon == ForecastHorizon.SEVEN_DAY:
                adjusted_prob = (base_prob * 0.5) + 0.1
                conf_factor = 0.45
            else:
                conf_factor = 1.0
                
            adjusted_prob = float(np.clip(adjusted_prob, 0.0, 1.0))
            probs.append(adjusted_prob)
            
            final_conf = float(np.clip(base_conf * conf_factor, 0.0, 1.0))
            
            predictions.append(
                RiskPrediction(
                    id=str(uuid.uuid4()),
                    entity_id=entity_id,
                    entity_type=entity_type,
                    risk_type=risk_type,
                    window=RiskWindow.for_horizon(horizon),
                    score=RiskScore.from_probability(
                        probability=adjusted_prob,
                        confidence=final_conf,
                        uncertainty=ensemble_pred.uncertainty
                    ),
                    evidence=[RiskEvidence(
                        feature_name=fname,
                        value=float(val),
                        importance=ensemble_pred.top_features.get(fname, 0.0),
                        description=f"Evidence from {fname}"
                    ) for fname, val in list(feature_vector.items())[:5]],
                    recommendations=[RiskRecommendation(
                        action="Monitor",
                        priority="LOW",
                        description=f"Monitor risk over {horizon.label}"
                    )],
                    generated_at=now,
                    valid_until=now + timedelta(minutes=5)
                )
            )
            
        if len(probs) > 1 and probs[-1] > probs[0] + 0.1:
            trend_dir = TrendDirection.INCREASING
        elif len(probs) > 1 and probs[-1] < probs[0] - 0.1:
            trend_dir = TrendDirection.DECREASING
        else:
            trend_dir = TrendDirection.STABLE
            
        trend = RiskTrend(
            direction=trend_dir,
            slope=float(probs[-1] - probs[0]),
            historical_average=0.2,
            volatility=ensemble_pred.uncertainty
        )
        
        return RiskForecast(
            id=str(uuid.uuid4()),
            entity_id=entity_id,
            entity_type=entity_type,
            risk_type=risk_type,
            predictions=predictions,
            trend=trend,
            generated_at=now
        )

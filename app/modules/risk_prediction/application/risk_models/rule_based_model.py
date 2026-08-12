import numpy as np
from typing import Any
from app.modules.risk_prediction.domain.enums import ModelType
from app.modules.risk_prediction.application.risk_models.base_model import RiskModel, ModelPrediction

class RuleBasedRiskModel(RiskModel):
    model_type = ModelType.RULE_BASED
    
    async def predict(self, features: np.ndarray, feature_names: list[str]) -> ModelPrediction:
        feature_dict = dict(zip(feature_names, features.tolist()))
        risk = 0.0
        explanations = []
        importances = {}
        
        if feature_dict.get('sensor_anomaly_count_1h', 0) > 3:
            risk += 0.3
            explanations.append("High sensor anomaly count (>3)")
            importances['sensor_anomaly_count_1h'] = 0.3
        if feature_dict.get('sensor_drift_score', 0) > 0.7:
            risk += 0.25
            explanations.append("High sensor drift score (>0.7)")
            importances['sensor_drift_score'] = 0.25
        if feature_dict.get('maintenance_gap_days', 0) > 30:
            risk += 0.2
            explanations.append("Maintenance gap > 30 days")
            importances['maintenance_gap_days'] = 0.2
        if feature_dict.get('rate_of_change', 0) > 0.8:
            risk += 0.15
            explanations.append("High rate of change (>0.8)")
            importances['rate_of_change'] = 0.15
        if feature_dict.get('quality_score', 1.0) < 0.5:
            risk += 0.1
            explanations.append("Low quality score (<0.5)")
            importances['quality_score'] = 0.1
            
        if feature_dict.get('ppe_compliance', 1.0) < 0.6:
            risk += 0.3
            explanations.append("Low PPE compliance (<0.6)")
            importances['ppe_compliance'] = 0.3
        if feature_dict.get('restricted_zone_violation', 0) > 0:
            risk += 0.25
            explanations.append("Restricted zone violation detected")
            importances['restricted_zone_violation'] = 0.25
        if feature_dict.get('fall_detection_score', 0) > 0.5:
            risk += 0.4
            explanations.append("Fall detection score high (>0.5)")
            importances['fall_detection_score'] = 0.4
        if feature_dict.get('exposure_hours', 0) > 8:
            risk += 0.1
            explanations.append("Exposure hours > 8")
            importances['exposure_hours'] = 0.1
            
        if feature_dict.get('fire_detection_score', 0) > 0.3:
            risk += 0.5
            explanations.append("Fire detection score > 0.3")
            importances['fire_detection_score'] = 0.5
        if feature_dict.get('gas_leak_indicators', 0) > 0.3:
            risk += 0.4
            explanations.append("Gas leak indicators > 0.3")
            importances['gas_leak_indicators'] = 0.4
        if feature_dict.get('worker_density', 0) > 0.8:
            risk += 0.15
            explanations.append("Worker density > 0.8")
            importances['worker_density'] = 0.15
        if feature_dict.get('anomaly_aggregate_count', 0) > 5:
            risk += 0.2
            explanations.append("Anomaly aggregate count > 5")
            importances['anomaly_aggregate_count'] = 0.2
            
        if feature_dict.get('critical_path_score', 0) == 1.0:
            risk *= 1.3
            explanations.append("Critical path score is 1 (multiplier 1.3x)")
            importances['critical_path_score'] = risk - (risk / 1.3) if risk > 0 else 0.0
        if feature_dict.get('hazard_proximity', 1.0) < 0.2:
            risk += 0.15
            explanations.append("Hazard proximity < 0.2")
            importances['hazard_proximity'] = 0.15
        if feature_dict.get('historical_failure_count', 0) > 2:
            risk += 0.1
            explanations.append("Historical failure count > 2")
            importances['historical_failure_count'] = 0.1
            
        final_probability = float(np.clip(risk, 0.0, 1.0))
        explanation_str = "Rules fired: " + ", ".join(explanations) if explanations else "No critical rules fired."
        
        completeness = min(1.0, len(feature_dict) / 16.0)
        confidence = float(np.clip(completeness, 0.5, 1.0))
        
        return ModelPrediction(
            probability=final_probability,
            confidence=confidence,
            uncertainty=0.1,
            feature_importance=importances,
            explanation=explanation_str,
            model_type=self.model_type.value,
            raw_scores={"base_risk": risk}
        )
        
    async def predict_proba(self, features: np.ndarray) -> np.ndarray:
        return np.array([[0.5]])
        
    def explain(self, features: np.ndarray, feature_names: list[str]) -> dict[str, float]:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Not standard but suffices for explain heuristic if needed without true async context
                # Real approach: mock or evaluate sync
                pass
        except RuntimeError:
            pass
            
        # Simplified sync explanation
        feature_dict = dict(zip(feature_names, features.tolist()))
        importances = {}
        if feature_dict.get('sensor_anomaly_count_1h', 0) > 3: importances['sensor_anomaly_count_1h'] = 0.3
        if feature_dict.get('sensor_drift_score', 0) > 0.7: importances['sensor_drift_score'] = 0.25
        if feature_dict.get('maintenance_gap_days', 0) > 30: importances['maintenance_gap_days'] = 0.2
        if feature_dict.get('rate_of_change', 0) > 0.8: importances['rate_of_change'] = 0.15
        if feature_dict.get('quality_score', 1.0) < 0.5: importances['quality_score'] = 0.1
        if feature_dict.get('ppe_compliance', 1.0) < 0.6: importances['ppe_compliance'] = 0.3
        if feature_dict.get('restricted_zone_violation', 0) > 0: importances['restricted_zone_violation'] = 0.25
        if feature_dict.get('fall_detection_score', 0) > 0.5: importances['fall_detection_score'] = 0.4
        if feature_dict.get('exposure_hours', 0) > 8: importances['exposure_hours'] = 0.1
        if feature_dict.get('fire_detection_score', 0) > 0.3: importances['fire_detection_score'] = 0.5
        if feature_dict.get('gas_leak_indicators', 0) > 0.3: importances['gas_leak_indicators'] = 0.4
        if feature_dict.get('worker_density', 0) > 0.8: importances['worker_density'] = 0.15
        if feature_dict.get('anomaly_aggregate_count', 0) > 5: importances['anomaly_aggregate_count'] = 0.2
        if feature_dict.get('critical_path_score', 0) == 1.0: importances['critical_path_score'] = 0.3
        if feature_dict.get('hazard_proximity', 1.0) < 0.2: importances['hazard_proximity'] = 0.15
        if feature_dict.get('historical_failure_count', 0) > 2: importances['historical_failure_count'] = 0.1
        return importances

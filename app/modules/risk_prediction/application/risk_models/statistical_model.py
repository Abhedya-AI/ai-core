import numpy as np
from typing import Any
from app.modules.risk_prediction.domain.enums import ModelType
from app.modules.risk_prediction.application.risk_models.base_model import RiskModel, ModelPrediction

class StatisticalRiskModel(RiskModel):
    model_type = ModelType.STATISTICAL
    
    def __init__(self):
        self.mean_vector = None
        self.cov_matrix_inv = None
        self.std_vector = None
        self.feature_weights = None
        self.feature_names_fit = None

    def fit_baseline(self, features_matrix: np.ndarray, feature_names: list[str]):
        self.feature_names_fit = feature_names
        self.mean_vector = np.mean(features_matrix, axis=0)
        self.std_vector = np.std(features_matrix, axis=0)
        self.std_vector[self.std_vector == 0] = 1e-6
        cov_matrix = np.cov(features_matrix, rowvar=False)
        # Add small regularization to diagonal to prevent singular matrix
        cov_matrix += np.eye(cov_matrix.shape[0]) * 1e-6
        self.cov_matrix_inv = np.linalg.pinv(cov_matrix)
        
        # Information content (variance-based weighting)
        variances = np.var(features_matrix, axis=0)
        self.feature_weights = variances / (np.sum(variances) + 1e-6)
        
    def _sigmoid(self, x: float) -> float:
        return 1.0 / (1.0 + np.exp(-x))

    async def predict(self, features: np.ndarray, feature_names: list[str]) -> ModelPrediction:
        if self.mean_vector is None:
            # Default baseline using feature-value heuristics
            z_scores = np.abs(features)  # Fallback assumption: features are already somewhat z-scored or scaled
            avg_z = np.mean(z_scores) if len(z_scores) > 0 else 0
            if avg_z == 0: probability = 0.1
            elif avg_z <= 2: probability = 0.1 + (0.4 / 2) * avg_z
            elif avg_z <= 3: probability = 0.5 + (0.3 / 1) * (avg_z - 2)
            else: probability = min(0.95, 0.8 + (0.15 / 1) * (avg_z - 3))
            
            explanation = "Using uncalibrated default z-score heuristics."
            importances = {name: float(z) for name, z in zip(feature_names, z_scores)}
            mahalanobis_dist = avg_z
        else:
            # Align features with fitted features
            aligned_features = np.zeros(len(self.feature_names_fit))
            for i, fname in enumerate(feature_names):
                if fname in self.feature_names_fit:
                    idx = self.feature_names_fit.index(fname)
                    aligned_features[idx] = features[i]
            
            diff = aligned_features - self.mean_vector
            mahalanobis_dist = np.sqrt(np.dot(np.dot(diff.T, self.cov_matrix_inv), diff))
            
            # Convert Mahalanobis distance to probability using sigmoid scaling
            probability = self._sigmoid(mahalanobis_dist - 3.0)  # Offset by 3 standard deviations
            
            z_scores = np.abs(diff / self.std_vector)
            weighted_z_scores = z_scores * self.feature_weights
            importances = {self.feature_names_fit[i]: float(weighted_z_scores[i]) for i in range(len(self.feature_names_fit))}
            explanation = f"Calculated Mahalanobis distance of {mahalanobis_dist:.2f} from safe operating envelope."

        probability = float(np.clip(probability, 0.0, 1.0))
        confidence = 0.8 if self.mean_vector is not None else 0.4
        
        return ModelPrediction(
            probability=probability,
            confidence=confidence,
            uncertainty=0.15,
            feature_importance=importances,
            explanation=explanation,
            model_type=self.model_type.value,
            raw_scores={"mahalanobis_dist": float(mahalanobis_dist)}
        )

    async def predict_proba(self, features: np.ndarray) -> np.ndarray:
        return np.array([[0.5]])

    def explain(self, features: np.ndarray, feature_names: list[str]) -> dict[str, float]:
        if self.mean_vector is None:
            return {name: float(np.abs(f)) for name, f in zip(feature_names, features)}
            
        aligned_features = np.zeros(len(self.feature_names_fit))
        for i, fname in enumerate(feature_names):
            if fname in self.feature_names_fit:
                idx = self.feature_names_fit.index(fname)
                aligned_features[idx] = features[i]
        
        diff = aligned_features - self.mean_vector
        z_scores = np.abs(diff / self.std_vector)
        return {self.feature_names_fit[i]: float(z_scores[i]) for i in range(len(self.feature_names_fit))}

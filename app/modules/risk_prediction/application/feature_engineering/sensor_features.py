from datetime import datetime, timezone
import uuid
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import FeatureCategory
from app.modules.risk_prediction.domain.models import RiskFeature
from app.modules.risk_prediction.application.feature_engineering.time_series_engine import TimeSeriesEngine

try:
    from app.modules.sensor.domain.models import SensorAnomaly, SensorReading, AnomalySeverity
except ImportError:
    SensorAnomaly = None
    SensorReading = None
    AnomalySeverity = None

log = get_logger(__name__)

class SensorFeatureExtractor:
    """Extracts features from sensor data."""
    
    def __init__(self):
        self.ts_engine = TimeSeriesEngine()

    async def extract(self, sensor_ids: list[str], lookback_minutes: int = 60) -> list[RiskFeature]:
        features = []
        now_iso = datetime.now(timezone.utc).isoformat()
        
        aggregate_anomaly_count = 0
        critical_anomaly_count = 0
        health_scores = []
        
        for sensor_id in sensor_ids:
            # Try to fetch readings/anomalies
            # In a real impl, this would query a repository
            has_data = False
            
            if not has_data:
                # Add missing features
                missing_feats = [
                    f"{sensor_id}_rolling_mean",
                    f"{sensor_id}_rolling_std",
                    f"{sensor_id}_rate_of_change",
                    f"{sensor_id}_trend_slope",
                    f"{sensor_id}_drift_score",
                    f"{sensor_id}_anomaly_score",
                    f"{sensor_id}_quality_score"
                ]
                for name in missing_feats:
                    features.append(RiskFeature(
                        id=str(uuid.uuid4()),
                        name=name,
                        value=0.0,
                        category=FeatureCategory.SENSOR,
                        timestamp=now_iso,
                        is_missing=True
                    ))
                log.warning(f"Sensor data unavailable for {sensor_id}")
                
        # Aggregate features
        features.extend([
            RiskFeature(
                id=str(uuid.uuid4()),
                name="sensor_aggregate_anomaly_count",
                value=float(aggregate_anomaly_count),
                category=FeatureCategory.SENSOR,
                timestamp=now_iso,
                is_missing=len(sensor_ids) == 0
            ),
            RiskFeature(
                id=str(uuid.uuid4()),
                name="sensor_critical_count",
                value=float(critical_anomaly_count),
                category=FeatureCategory.SENSOR,
                timestamp=now_iso,
                is_missing=len(sensor_ids) == 0
            ),
            RiskFeature(
                id=str(uuid.uuid4()),
                name="sensor_health_score",
                value=float(sum(health_scores)/len(health_scores)) if health_scores else 0.0,
                category=FeatureCategory.SENSOR,
                timestamp=now_iso,
                is_missing=len(health_scores) == 0
            )
        ])
        
        return features

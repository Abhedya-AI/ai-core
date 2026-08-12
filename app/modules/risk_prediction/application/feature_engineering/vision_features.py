import uuid
from datetime import datetime, timezone
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import FeatureCategory
from app.modules.risk_prediction.domain.models import RiskFeature

try:
    from app.modules.vision.domain.entities.detection import Detection
except ImportError:
    Detection = None

log = get_logger(__name__)

class VisionFeatureExtractor:
    """Extracts features from vision intelligence system."""
    
    async def extract(self, zone_id: str, lookback_minutes: int = 30) -> list[RiskFeature]:
        features = []
        now_iso = datetime.now(timezone.utc).isoformat()
        
        has_data = False
        
        names = [
            "vision_ppe_compliance_score",
            "vision_worker_count",
            "vision_violation_count",
            "vision_anomaly_score",
            "vision_fire_detection_score",
            "vision_restricted_zone_violation_score",
            "vision_fall_detection_score",
            "vision_worker_density"
        ]
        
        for name in names:
            features.append(RiskFeature(
                id=str(uuid.uuid4()),
                name=name,
                value=0.0,
                category=FeatureCategory.VISION,
                timestamp=now_iso,
                is_missing=not has_data
            ))
            
        if not has_data:
            log.warning(f"Vision data unavailable for zone {zone_id}")
            
        return features

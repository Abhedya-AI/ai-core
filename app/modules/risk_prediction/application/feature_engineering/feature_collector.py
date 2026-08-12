import asyncio
import numpy as np
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Tuple
from app.modules.risk_prediction.domain.enums import EntityType, FeatureCategory
from app.modules.risk_prediction.domain.models import RiskFeature
from .sensor_features import SensorFeatureExtractor
from .vision_features import VisionFeatureExtractor
from .graph_features import GraphFeatureExtractor
from .graphrag_features import GraphRAGFeatureExtractor
from .time_series_engine import TimeSeriesEngine
from app.core.logging import get_logger

log = get_logger(__name__)

@dataclass
class FeatureVector:
    """A collected set of features for ML models."""
    entity_id: str
    entity_type: EntityType
    features: List[RiskFeature]
    collected_at: str
    sensor_completeness: float
    vision_completeness: float
    graph_completeness: float
    graphrag_completeness: float

    def to_numpy_array(self) -> Tuple[np.ndarray, List[str]]:
        values = [f.value for f in self.features]
        names = [f.name for f in self.features]
        return np.array(values), names

    def get_by_category(self, category: FeatureCategory) -> List[RiskFeature]:
        return [f for f in self.features if f.category == category]

    def overall_completeness(self) -> float:
        return (
            self.sensor_completeness + 
            self.vision_completeness + 
            self.graph_completeness + 
            self.graphrag_completeness
        ) / 4.0

class FeatureCollector:
    """Orchestrates the collection of features from multiple domains."""
    
    def __init__(self):
        self.sensor_extractor = SensorFeatureExtractor()
        self.vision_extractor = VisionFeatureExtractor()
        self.graph_extractor = GraphFeatureExtractor()
        self.graphrag_extractor = GraphRAGFeatureExtractor()
        self.ts_engine = TimeSeriesEngine()

    def _compute_completeness(self, features: List[RiskFeature]) -> float:
        if not features:
            return 0.0
        missing = sum(1 for f in features if getattr(f, 'is_missing', False))
        return 1.0 - (missing / len(features))

    async def collect(
        self,
        entity_id: str,
        entity_type: EntityType,
        sensor_ids: List[str],
        lookback_minutes: int = 60,
    ) -> FeatureVector:
        
        log.info(f"Collecting features for {entity_type.value} {entity_id}")
        
        results = await asyncio.gather(
            self.sensor_extractor.extract(sensor_ids, lookback_minutes),
            self.vision_extractor.extract(entity_id, lookback_minutes),
            self.graph_extractor.extract(entity_id, entity_type),
            self.graphrag_extractor.extract(entity_id, entity_type),
            return_exceptions=True
        )

        sensor_feats = results[0] if not isinstance(results[0], Exception) else []
        vision_feats = results[1] if not isinstance(results[1], Exception) else []
        graph_feats = results[2] if not isinstance(results[2], Exception) else []
        graphrag_feats = results[3] if not isinstance(results[3], Exception) else []

        if isinstance(results[0], Exception):
            log.error(f"Sensor extraction failed: {results[0]}")
        if isinstance(results[1], Exception):
            log.error(f"Vision extraction failed: {results[1]}")
        if isinstance(results[2], Exception):
            log.error(f"Graph extraction failed: {results[2]}")
        if isinstance(results[3], Exception):
            log.error(f"GraphRAG extraction failed: {results[3]}")

        all_features = []
        all_features.extend(sensor_feats)
        all_features.extend(vision_feats)
        all_features.extend(graph_feats)
        all_features.extend(graphrag_feats)

        return FeatureVector(
            entity_id=entity_id,
            entity_type=entity_type,
            features=all_features,
            collected_at=datetime.now(timezone.utc).isoformat(),
            sensor_completeness=self._compute_completeness(sensor_feats),
            vision_completeness=self._compute_completeness(vision_feats),
            graph_completeness=self._compute_completeness(graph_feats),
            graphrag_completeness=self._compute_completeness(graphrag_feats)
        )

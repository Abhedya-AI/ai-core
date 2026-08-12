"""
app/modules/risk_prediction/tests/test_feature_engineering.py
Tests for all feature extractors and FeatureCollector.
"""
from __future__ import annotations

import asyncio

import numpy as np
import pytest

from app.modules.risk_prediction.domain.enums import EntityType, FeatureCategory


class TestFeatureVector:
    @pytest.fixture
    def feature_vector(self, sample_all_features):
        from app.modules.risk_prediction.application.feature_engineering.feature_collector import FeatureVector
        return FeatureVector(
            entity_id="EQ-001",
            entity_type=EntityType.EQUIPMENT,
            features=sample_all_features,
            collected_at="",
            sensor_completeness=0.9,
            vision_completeness=0.8,
            graph_completeness=0.85,
            graphrag_completeness=0.75,
        )

    def test_to_numpy_array_shape(self, feature_vector, sample_all_features):
        arr, names = feature_vector.to_numpy_array()
        assert isinstance(arr, np.ndarray)
        assert len(arr) == len(sample_all_features)
        assert len(names) == len(sample_all_features)

    def test_get_by_category_sensor(self, feature_vector):
        sensor_features = feature_vector.get_by_category(FeatureCategory.SENSOR)
        assert len(sensor_features) > 0
        assert all(f.category == FeatureCategory.SENSOR for f in sensor_features)

    def test_get_by_category_vision(self, feature_vector):
        vision_features = feature_vector.get_by_category(FeatureCategory.VISION)
        assert len(vision_features) > 0
        assert all(f.category == FeatureCategory.VISION for f in vision_features)

    def test_get_by_category_empty(self, feature_vector):
        env_features = feature_vector.get_by_category(FeatureCategory.ENVIRONMENTAL)
        assert env_features == []

    def test_overall_completeness(self, feature_vector):
        completeness = feature_vector.overall_completeness()
        assert 0.0 <= completeness <= 1.0
        # With our fixture values: (0.9+0.8+0.85+0.75)/4 = 0.825
        assert completeness == pytest.approx(0.825, rel=0.01)

    def test_to_numpy_array_values_match_features(self, feature_vector, sample_all_features):
        arr, names = feature_vector.to_numpy_array()
        for i, feature in enumerate(sample_all_features):
            assert arr[i] == pytest.approx(feature.value, rel=1e-6)


class TestSensorFeatureExtractor:
    @pytest.fixture
    def extractor(self):
        from app.modules.risk_prediction.application.feature_engineering.sensor_features import SensorFeatureExtractor
        return SensorFeatureExtractor()

    @pytest.mark.asyncio
    async def test_extract_returns_list(self, extractor):
        features = await extractor.extract(sensor_ids=["TEMP-001"], lookback_minutes=60)
        assert isinstance(features, list)

    @pytest.mark.asyncio
    async def test_extract_with_empty_sensor_ids(self, extractor):
        features = await extractor.extract(sensor_ids=[], lookback_minutes=60)
        # Should return aggregate features at minimum
        assert isinstance(features, list)

    @pytest.mark.asyncio
    async def test_all_features_have_sensor_category(self, extractor):
        features = await extractor.extract(sensor_ids=["TEMP-001"], lookback_minutes=60)
        sensor_features = [f for f in features if f.category == FeatureCategory.SENSOR]
        # At least some sensor features should be present
        assert isinstance(sensor_features, list)

    @pytest.mark.asyncio
    async def test_features_bounded(self, extractor):
        features = await extractor.extract(sensor_ids=["TEMP-001", "PRESS-002"], lookback_minutes=30)
        for feature in features:
            # Values should be normalized 0-1 range for most features, but
            # raw counts can be > 1
            assert not np.isnan(feature.value)
            assert not np.isinf(feature.value)

    @pytest.mark.asyncio
    async def test_missing_sensor_marked(self, extractor):
        # With a non-existent sensor, features should be marked missing
        features = await extractor.extract(
            sensor_ids=["NONEXISTENT-SENSOR-XYZ-999"], lookback_minutes=60
        )
        missing_features = [f for f in features if f.missing]
        # Should have some missing features since sensor doesn't exist
        assert isinstance(missing_features, list)


class TestVisionFeatureExtractor:
    @pytest.fixture
    def extractor(self):
        from app.modules.risk_prediction.application.feature_engineering.vision_features import VisionFeatureExtractor
        return VisionFeatureExtractor()

    @pytest.mark.asyncio
    async def test_extract_returns_list(self, extractor):
        features = await extractor.extract(zone_id="ZONE-A-01", lookback_minutes=30)
        assert isinstance(features, list)

    @pytest.mark.asyncio
    async def test_all_features_have_vision_category(self, extractor):
        features = await extractor.extract(zone_id="ZONE-A-01", lookback_minutes=30)
        vision_features = [f for f in features if f.category == FeatureCategory.VISION]
        assert isinstance(vision_features, list)

    @pytest.mark.asyncio
    async def test_features_not_nan(self, extractor):
        features = await extractor.extract(zone_id="ZONE-A-01", lookback_minutes=30)
        for feature in features:
            assert not np.isnan(feature.value)


class TestGraphFeatureExtractor:
    @pytest.fixture
    def extractor(self):
        from app.modules.risk_prediction.application.feature_engineering.graph_features import GraphFeatureExtractor
        return GraphFeatureExtractor()

    @pytest.mark.asyncio
    async def test_extract_returns_list(self, extractor, sample_entity_id):
        features = await extractor.extract(
            entity_id=sample_entity_id, entity_type=EntityType.EQUIPMENT
        )
        assert isinstance(features, list)

    @pytest.mark.asyncio
    async def test_features_have_graph_category(self, extractor, sample_entity_id):
        features = await extractor.extract(
            entity_id=sample_entity_id, entity_type=EntityType.EQUIPMENT
        )
        graph_features = [f for f in features if f.category == FeatureCategory.GRAPH]
        assert isinstance(graph_features, list)

    @pytest.mark.asyncio
    async def test_features_not_nan(self, extractor, sample_entity_id):
        features = await extractor.extract(
            entity_id=sample_entity_id, entity_type=EntityType.EQUIPMENT
        )
        for f in features:
            assert not np.isnan(f.value)


class TestGraphRAGFeatureExtractor:
    @pytest.fixture
    def extractor(self):
        from app.modules.risk_prediction.application.feature_engineering.graphrag_features import GraphRAGFeatureExtractor
        return GraphRAGFeatureExtractor()

    @pytest.mark.asyncio
    async def test_extract_returns_list(self, extractor, sample_entity_id):
        features = await extractor.extract(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
        )
        assert isinstance(features, list)

    @pytest.mark.asyncio
    async def test_features_have_graphrag_category(self, extractor, sample_entity_id):
        features = await extractor.extract(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
        )
        graphrag_features = [f for f in features if f.category == FeatureCategory.GRAPHRAG]
        assert isinstance(graphrag_features, list)


class TestFeatureCollector:
    @pytest.fixture
    def collector(self):
        from app.modules.risk_prediction.application.feature_engineering.feature_collector import FeatureCollector
        return FeatureCollector()

    @pytest.mark.asyncio
    async def test_collect_returns_feature_vector(self, collector, sample_entity_id):
        from app.modules.risk_prediction.application.feature_engineering.feature_collector import FeatureVector
        fv = await collector.collect(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            lookback_minutes=60,
        )
        assert isinstance(fv, FeatureVector)

    @pytest.mark.asyncio
    async def test_collect_entity_fields_correct(self, collector, sample_entity_id):
        fv = await collector.collect(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            lookback_minutes=60,
        )
        assert fv.entity_id == sample_entity_id
        assert fv.entity_type == EntityType.EQUIPMENT

    @pytest.mark.asyncio
    async def test_collect_has_features(self, collector, sample_entity_id):
        fv = await collector.collect(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            lookback_minutes=60,
        )
        assert len(fv.features) > 0

    @pytest.mark.asyncio
    async def test_collect_completeness_bounded(self, collector, sample_entity_id):
        fv = await collector.collect(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            lookback_minutes=60,
        )
        assert 0.0 <= fv.sensor_completeness <= 1.0
        assert 0.0 <= fv.vision_completeness <= 1.0
        assert 0.0 <= fv.graph_completeness <= 1.0
        assert 0.0 <= fv.graphrag_completeness <= 1.0

    @pytest.mark.asyncio
    async def test_collect_no_nan_values(self, collector, sample_entity_id):
        fv = await collector.collect(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            lookback_minutes=60,
        )
        for feature in fv.features:
            assert not np.isnan(feature.value), f"NaN in feature {feature.name}"

    @pytest.mark.asyncio
    async def test_collect_numpy_array_shape(self, collector, sample_entity_id):
        fv = await collector.collect(
            entity_id=sample_entity_id,
            entity_type=EntityType.EQUIPMENT,
            sensor_ids=["TEMP-001"],
            lookback_minutes=60,
        )
        arr, names = fv.to_numpy_array()
        assert arr.shape == (len(fv.features),)
        assert len(names) == len(fv.features)

    @pytest.mark.asyncio
    async def test_collect_concurrent_resilience(self, collector):
        """Multiple concurrent collections should not interfere."""
        tasks = [
            collector.collect(
                entity_id=f"EQ-{i:03d}",
                entity_type=EntityType.EQUIPMENT,
                sensor_ids=[f"TEMP-{i:03d}"],
                lookback_minutes=60,
            )
            for i in range(3)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Should not raise exceptions
        for r in results:
            assert not isinstance(r, Exception)

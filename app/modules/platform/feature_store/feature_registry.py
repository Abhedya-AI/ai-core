from __future__ import annotations

import time
import uuid
from typing import Any
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger

log = get_logger(__name__)

class FeatureType(str, Enum):
    NUMERICAL = "NUMERICAL"
    CATEGORICAL = "CATEGORICAL"
    BOOLEAN = "BOOLEAN"
    EMBEDDING = "EMBEDDING"
    DATETIME = "DATETIME"
    STRING = "STRING"

class FeatureDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    feature_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    owner: str
    feature_type: FeatureType
    entity_type: str
    source_module: str
    tags: list[str] = Field(default_factory=list)
    is_online: bool = True
    is_offline: bool = True
    ttl_seconds: int = 3600
    validation_rules: dict[str, Any] = Field(default_factory=dict)
    lineage_sources: list[str] = Field(default_factory=list)
    version: int = 1
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FeatureRegistry:
    def __init__(self) -> None:
        self._features: dict[str, FeatureDefinition] = {}
        self._by_name: dict[str, str] = {}

    async def register(
        self,
        name: str,
        description: str,
        owner: str,
        feature_type: FeatureType,
        entity_type: str,
        source_module: str,
        tags: list[str] | None = None,
        is_online: bool = True,
        is_offline: bool = True,
        ttl_seconds: int = 3600,
        validation_rules: dict[str, Any] | None = None,
        lineage_sources: list[str] | None = None
    ) -> FeatureDefinition:
        t0 = time.perf_counter()
        
        if name in self._by_name:
            raise ValueError(f"Feature name '{name}' is already registered")
            
        feature = FeatureDefinition(
            name=name,
            description=description,
            owner=owner,
            feature_type=feature_type,
            entity_type=entity_type,
            source_module=source_module,
            tags=tags or [],
            is_online=is_online,
            is_offline=is_offline,
            ttl_seconds=ttl_seconds,
            validation_rules=validation_rules or {},
            lineage_sources=lineage_sources or []
        )
        
        self._features[feature.feature_id] = feature
        self._by_name[feature.name] = feature.feature_id
        
        log.info(f"Registered feature {name} in {time.perf_counter() - t0:.4f}s")
        return feature

    async def get(self, feature_id: str) -> FeatureDefinition | None:
        return self._features.get(feature_id)

    async def get_by_name(self, name: str) -> FeatureDefinition | None:
        feature_id = self._by_name.get(name)
        if feature_id:
            return self._features.get(feature_id)
        return None

    async def list(
        self,
        entity_type: str | None = None,
        source_module: str | None = None,
        feature_type: FeatureType | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[FeatureDefinition]:
        t0 = time.perf_counter()
        
        results = []
        for feat in self._features.values():
            if entity_type and feat.entity_type != entity_type:
                continue
            if source_module and feat.source_module != source_module:
                continue
            if feature_type and feat.feature_type != feature_type:
                continue
            results.append(feat)
            
        results.sort(key=lambda x: x.name)
        paginated = results[offset:offset+limit]
        
        log.debug(f"Listed {len(paginated)} features in {time.perf_counter() - t0:.4f}s")
        return paginated

    async def update(self, feature_id: str, updates: dict[str, Any]) -> FeatureDefinition:
        t0 = time.perf_counter()
        if feature_id not in self._features:
            raise ValueError(f"Feature ID {feature_id} not found")
            
        current = self._features[feature_id]
        
        # Don't allow changing ID
        if "feature_id" in updates:
            del updates["feature_id"]
            
        # Update name mapping if name changed
        if "name" in updates and updates["name"] != current.name:
            if updates["name"] in self._by_name:
                raise ValueError(f"Feature name '{updates['name']}' is already in use")
            del self._by_name[current.name]
            self._by_name[updates["name"]] = feature_id
            
        updates["version"] = current.version + 1
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        updated = current.model_copy(update=updates)
        self._features[feature_id] = updated
        
        log.info(f"Updated feature {updated.name} to version {updated.version} in {time.perf_counter() - t0:.4f}s")
        return updated

    async def delete(self, feature_id: str) -> bool:
        t0 = time.perf_counter()
        if feature_id in self._features:
            feat = self._features[feature_id]
            if feat.name in self._by_name:
                del self._by_name[feat.name]
            del self._features[feature_id]
            log.info(f"Deleted feature {feat.name} in {time.perf_counter() - t0:.4f}s")
            return True
        return False

    async def search(self, query: str) -> list[FeatureDefinition]:
        t0 = time.perf_counter()
        query = query.lower()
        results = []
        
        for feat in self._features.values():
            match = False
            if query in feat.name.lower():
                match = True
            elif query in feat.description.lower():
                match = True
            elif any(query in tag.lower() for tag in feat.tags):
                match = True
                
            if match:
                results.append(feat)
                
        log.debug(f"Search for '{query}' found {len(results)} features in {time.perf_counter() - t0:.4f}s")
        return results

    async def get_lineage(self, feature_id: str) -> dict[str, Any]:
        feat = await self.get(feature_id)
        if not feat:
            return {}
            
        upstream = []
        for src_name in feat.lineage_sources:
            src_feat = await self.get_by_name(src_name)
            if src_feat:
                upstream.append(src_feat.model_dump())
                
        # Simulate downstream models (would query ModelRegistry in reality)
        downstream = []
        
        return {
            "feature": feat.model_dump(),
            "upstream_features": upstream,
            "downstream_models": downstream
        }

    async def count(self) -> dict[str, Any]:
        by_type = {}
        by_entity = {}
        online_count = 0
        offline_count = 0
        
        for feat in self._features.values():
            f_type = str(feat.feature_type.value)
            by_type[f_type] = by_type.get(f_type, 0) + 1
            
            by_entity[feat.entity_type] = by_entity.get(feat.entity_type, 0) + 1
            
            if feat.is_online:
                online_count += 1
            if feat.is_offline:
                offline_count += 1
                
        return {
            "total": len(self._features),
            "by_type": by_type,
            "by_entity_type": by_entity,
            "online_count": online_count,
            "offline_count": offline_count
        }

_feature_registry_instance = None

def get_feature_registry() -> FeatureRegistry:
    global _feature_registry_instance
    if _feature_registry_instance is None:
        _feature_registry_instance = FeatureRegistry()
    return _feature_registry_instance

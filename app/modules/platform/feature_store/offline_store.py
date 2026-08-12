from __future__ import annotations

import time
import uuid
from typing import Any
from datetime import datetime, timezone
import asyncio

from app.core.logging import get_logger

log = get_logger(__name__)

class OfflineFeatureStore:
    def __init__(self) -> None:
        # entity_id -> list of {timestamp, features_dict, source_module, record_id}
        self._store: dict[str, list[dict[str, Any]]] = {}
        self._max_history = 10000

    async def materialize(
        self,
        entity_id: str,
        entity_type: str,
        features: dict[str, float | str | bool],
        source_module: str,
        timestamp: str | None = None
    ) -> str:
        start_time = time.perf_counter()
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        record_id = str(uuid.uuid4())
        record = {
            "record_id": record_id,
            "timestamp": timestamp,
            "entity_type": entity_type,
            "features": features,
            "source_module": source_module
        }

        if entity_id not in self._store:
            self._store[entity_id] = []
            
        self._store[entity_id].append(record)
        
        # Sort by timestamp
        self._store[entity_id].sort(key=lambda x: x["timestamp"])
        
        # Cap history
        if len(self._store[entity_id]) > self._max_history:
            self._store[entity_id] = self._store[entity_id][-self._max_history:]
            
        latency = time.perf_counter() - start_time
        log.info(f"Materialized features for {entity_id} in {latency:.4f}s")
        return record_id

    async def get_features(self, entity_id: str, as_of_timestamp: str | None = None) -> dict[str, Any] | None:
        start_time = time.perf_counter()
        if entity_id not in self._store or not self._store[entity_id]:
            return None
            
        history = self._store[entity_id]
        
        if as_of_timestamp is None:
            result = history[-1]["features"]
        else:
            # Binary search for the latest record <= as_of_timestamp
            left, right = 0, len(history) - 1
            best_idx = -1
            
            while left <= right:
                mid = (left + right) // 2
                if history[mid]["timestamp"] <= as_of_timestamp:
                    best_idx = mid
                    left = mid + 1
                else:
                    right = mid - 1
                    
            if best_idx == -1:
                result = None
            else:
                result = history[best_idx]["features"]
                
        latency = time.perf_counter() - start_time
        log.debug(f"Retrieved features for {entity_id} in {latency:.4f}s")
        return result

    async def get_history(self, entity_id: str, limit: int = 100) -> list[dict[str, Any]]:
        start_time = time.perf_counter()
        if entity_id not in self._store:
            return []
            
        result = self._store[entity_id][-limit:]
        latency = time.perf_counter() - start_time
        log.debug(f"Retrieved history for {entity_id} in {latency:.4f}s")
        return result

    async def get_training_dataset(
        self,
        entity_ids: list[str],
        feature_names: list[str],
        start_time: str,
        end_time: str
    ) -> list[dict[str, Any]]:
        t0 = time.perf_counter()
        dataset = []
        
        for entity_id in entity_ids:
            if entity_id not in self._store:
                continue
                
            for record in self._store[entity_id]:
                ts = record["timestamp"]
                if start_time <= ts <= end_time:
                    features = record["features"]
                    subset = {k: v for k, v in features.items() if k in feature_names}
                    
                    dataset.append({
                        "entity_id": entity_id,
                        "timestamp": ts,
                        "features": subset
                    })
                    
        latency = time.perf_counter() - t0
        log.info(f"Generated training dataset with {len(dataset)} records in {latency:.4f}s")
        return dataset

    async def compute_feature_statistics(self, entity_id: str, feature_name: str) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        import numpy as np
        
        if entity_id not in self._store:
            return {}
            
        values = []
        null_count = 0
        total_count = 0
        
        for record in self._store[entity_id]:
            total_count += 1
            features = record["features"]
            if feature_name in features:
                val = features[feature_name]
                if val is None:
                    null_count += 1
                elif isinstance(val, (int, float)):
                    values.append(float(val))
            else:
                null_count += 1
                
        if not values:
            return {
                "null_count": null_count,
                "total_count": total_count,
                "null_rate": null_count / total_count if total_count > 0 else 0
            }
            
        arr = np.array(values)
        
        stats = {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "p25": float(np.percentile(arr, 25)),
            "p50": float(np.percentile(arr, 50)),
            "p75": float(np.percentile(arr, 75)),
            "p95": float(np.percentile(arr, 95)),
            "null_count": null_count,
            "total_count": total_count,
            "null_rate": null_count / total_count
        }
        
        latency = time.perf_counter() - t0
        log.debug(f"Computed stats for {entity_id}.{feature_name} in {latency:.4f}s")
        return stats

    async def list_entities(self, entity_type: str, limit: int, offset: int) -> list[str]:
        t0 = time.perf_counter()
        entities = []
        
        for entity_id, records in self._store.items():
            if not records:
                continue
            if records[0].get("entity_type") == entity_type:
                entities.append(entity_id)
                
        # Sort for consistent pagination
        entities.sort()
        result = entities[offset:offset+limit]
        
        latency = time.perf_counter() - t0
        log.debug(f"Listed entities in {latency:.4f}s")
        return result

    async def delete_entity_history(self, entity_id: str, older_than_hours: int) -> int:
        t0 = time.perf_counter()
        if entity_id not in self._store:
            return 0
            
        now_ts = datetime.now(timezone.utc).timestamp()
        cutoff_ts = now_ts - (older_than_hours * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff_ts, timezone.utc).isoformat()
        
        original_count = len(self._store[entity_id])
        self._store[entity_id] = [r for r in self._store[entity_id] if r["timestamp"] > cutoff_iso]
        deleted_count = original_count - len(self._store[entity_id])
        
        if not self._store[entity_id]:
            del self._store[entity_id]
            
        latency = time.perf_counter() - t0
        log.info(f"Deleted {deleted_count} records for {entity_id} in {latency:.4f}s")
        return deleted_count

_offline_store_instance = None

def get_offline_feature_store() -> OfflineFeatureStore:
    global _offline_store_instance
    if _offline_store_instance is None:
        _offline_store_instance = OfflineFeatureStore()
    return _offline_store_instance

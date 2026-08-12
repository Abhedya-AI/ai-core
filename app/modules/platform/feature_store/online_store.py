from __future__ import annotations

import time
import json
import asyncio
from typing import Any
from datetime import datetime, timezone

from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.infrastructure.redis.client import get_redis_client
except ImportError:
    get_redis_client = None

class OnlineFeatureStore:
    def __init__(self) -> None:
        self._memory_store: dict[str, dict[str, Any]] = {}
        # Simple memory TTL support: key -> expiry timestamp
        self._memory_expiry: dict[str, float] = {}

    def _get_key(self, entity_id: str, feature_group: str) -> str:
        return f"platform:features:{entity_id}:{feature_group}"

    async def set(self, entity_id: str, feature_group: str, features: dict[str, Any], ttl_seconds: int = 300) -> None:
        t0 = time.perf_counter()
        key = self._get_key(entity_id, feature_group)
        
        if get_redis_client:
            try:
                redis = await get_redis_client()
                if redis:
                    await redis.set(key, json.dumps(features), ex=ttl_seconds)
                    log.debug(f"Set features in Redis for {key} in {time.perf_counter() - t0:.4f}s")
                    return
            except Exception as e:
                log.warning(f"Redis set failed, falling back to memory: {e}")
                
        # Fallback to memory
        self._memory_store[key] = features
        if ttl_seconds > 0:
            self._memory_expiry[key] = datetime.now(timezone.utc).timestamp() + ttl_seconds
            
        log.debug(f"Set features in memory for {key} in {time.perf_counter() - t0:.4f}s")

    async def get(self, entity_id: str, feature_group: str) -> dict[str, Any] | None:
        t0 = time.perf_counter()
        key = self._get_key(entity_id, feature_group)
        
        if get_redis_client:
            try:
                redis = await get_redis_client()
                if redis:
                    val = await redis.get(key)
                    if val:
                        result = json.loads(val)
                        log.debug(f"Got features from Redis for {key} in {time.perf_counter() - t0:.4f}s")
                        return result
                    return None
            except Exception as e:
                log.warning(f"Redis get failed, falling back to memory: {e}")
                
        # Fallback to memory
        if key in self._memory_store:
            # Check expiry
            if key in self._memory_expiry:
                if datetime.now(timezone.utc).timestamp() > self._memory_expiry[key]:
                    del self._memory_store[key]
                    del self._memory_expiry[key]
                    return None
            
            result = self._memory_store[key]
            log.debug(f"Got features from memory for {key} in {time.perf_counter() - t0:.4f}s")
            return result
            
        return None

    async def get_multi(self, entity_ids: list[str], feature_group: str) -> dict[str, dict[str, Any]]:
        t0 = time.perf_counter()
        keys = [self._get_key(eid, feature_group) for eid in entity_ids]
        result = {}
        
        if get_redis_client and keys:
            try:
                redis = await get_redis_client()
                if redis:
                    values = await redis.mget(keys)
                    for eid, val in zip(entity_ids, values):
                        if val:
                            result[eid] = json.loads(val)
                    log.debug(f"MGET from Redis for {len(keys)} keys in {time.perf_counter() - t0:.4f}s")
                    return result
            except Exception as e:
                log.warning(f"Redis mget failed, falling back to memory: {e}")
                
        # Fallback to memory via gathering individual gets
        tasks = [self.get(eid, feature_group) for eid in entity_ids]
        values = await asyncio.gather(*tasks)
        for eid, val in zip(entity_ids, values):
            if val is not None:
                result[eid] = val
                
        log.debug(f"Got multi from memory for {len(keys)} keys in {time.perf_counter() - t0:.4f}s")
        return result

    async def delete(self, entity_id: str, feature_group: str) -> bool:
        t0 = time.perf_counter()
        key = self._get_key(entity_id, feature_group)
        deleted = False
        
        if get_redis_client:
            try:
                redis = await get_redis_client()
                if redis:
                    res = await redis.delete(key)
                    deleted = res > 0
            except Exception as e:
                log.warning(f"Redis delete failed, falling back to memory: {e}")
                
        if key in self._memory_store:
            del self._memory_store[key]
            if key in self._memory_expiry:
                del self._memory_expiry[key]
            deleted = True
            
        log.debug(f"Deleted {key} in {time.perf_counter() - t0:.4f}s")
        return deleted

    async def set_batch(self, updates: list[dict[str, Any]]) -> None:
        t0 = time.perf_counter()
        
        if get_redis_client and updates:
            try:
                redis = await get_redis_client()
                if redis:
                    pipe = redis.pipeline()
                    for update in updates:
                        key = self._get_key(update["entity_id"], update["feature_group"])
                        val = json.dumps(update["features"])
                        ttl = update.get("ttl_seconds", 300)
                        if ttl > 0:
                            pipe.set(key, val, ex=ttl)
                        else:
                            pipe.set(key, val)
                    await pipe.execute()
                    log.debug(f"Batch set {len(updates)} in Redis in {time.perf_counter() - t0:.4f}s")
                    return
            except Exception as e:
                log.warning(f"Redis pipeline failed, falling back to memory: {e}")
                
        # Memory fallback
        for update in updates:
            await self.set(
                entity_id=update["entity_id"],
                feature_group=update["feature_group"],
                features=update["features"],
                ttl_seconds=update.get("ttl_seconds", 300)
            )
            
        log.debug(f"Batch set {len(updates)} in memory in {time.perf_counter() - t0:.4f}s")

    async def get_ttl(self, entity_id: str, feature_group: str) -> int:
        t0 = time.perf_counter()
        key = self._get_key(entity_id, feature_group)
        
        if get_redis_client:
            try:
                redis = await get_redis_client()
                if redis:
                    ttl = await redis.ttl(key)
                    return int(ttl)
            except Exception as e:
                pass
                
        if key not in self._memory_store:
            return -2
            
        if key not in self._memory_expiry:
            return -1
            
        remaining = self._memory_expiry[key] - datetime.now(timezone.utc).timestamp()
        if remaining <= 0:
            del self._memory_store[key]
            del self._memory_expiry[key]
            return -2
            
        return int(remaining)

    async def refresh(self, entity_id: str, feature_group: str, ttl_seconds: int) -> bool:
        t0 = time.perf_counter()
        key = self._get_key(entity_id, feature_group)
        
        if get_redis_client:
            try:
                redis = await get_redis_client()
                if redis:
                    res = await redis.expire(key, ttl_seconds)
                    return bool(res)
            except Exception:
                pass
                
        if key in self._memory_store:
            self._memory_expiry[key] = datetime.now(timezone.utc).timestamp() + ttl_seconds
            return True
            
        return False

    async def stats(self) -> dict[str, Any]:
        has_redis = False
        if get_redis_client:
            try:
                redis = await get_redis_client()
                if redis:
                    has_redis = await redis.ping()
            except Exception:
                pass
                
        # Clean up expired memory items
        now = datetime.now(timezone.utc).timestamp()
        expired = [k for k, v in self._memory_expiry.items() if v <= now]
        for k in expired:
            if k in self._memory_store:
                del self._memory_store[k]
            del self._memory_expiry[k]
            
        return {
            "total_keys": len(self._memory_store),
            "memory_store_size": len(self._memory_store),
            "redis_available": bool(has_redis)
        }

_online_store_instance = None

def get_online_feature_store() -> OnlineFeatureStore:
    global _online_store_instance
    if _online_store_instance is None:
        _online_store_instance = OnlineFeatureStore()
    return _online_store_instance

from __future__ import annotations

import json
import hashlib
import time
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)

try:
    from app.infrastructure.redis.client import get_redis_client
except ImportError:
    get_redis_client = None  # type: ignore


class ResponseCacheManager:
    def __init__(self):
        self._memory_cache: dict[str, tuple[Any, float]] = {}
        self._hits: int = 0
        self._misses: int = 0

    def _make_key(self, tenant_id: str, endpoint: str, params: dict) -> str:
        sorted_params = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()
        return f"platform:cache:{tenant_id}:{endpoint_hash}:{params_hash}"

    async def get(self, tenant_id: str, endpoint: str, params: dict) -> Any | None:
        key = self._make_key(tenant_id, endpoint, params)
        if get_redis_client:
            redis = await get_redis_client()
            val = await redis.get(key)
            if val:
                self._hits += 1
                return json.loads(val)
        
        # Memory fallback
        if key in self._memory_cache:
            val, expires_at = self._memory_cache[key]
            if time.time() < expires_at:
                self._hits += 1
                return val
            else:
                del self._memory_cache[key]
                
        self._misses += 1
        return None

    async def set(self, tenant_id: str, endpoint: str, params: dict, value: Any, ttl_seconds: int = 300) -> None:
        key = self._make_key(tenant_id, endpoint, params)
        if get_redis_client:
            redis = await get_redis_client()
            await redis.set(key, json.dumps(value), ex=ttl_seconds)
        
        self._memory_cache[key] = (value, time.time() + ttl_seconds)

    async def invalidate(self, tenant_id: str, endpoint: str) -> int:
        count = 0
        endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()
        prefix = f"platform:cache:{tenant_id}:{endpoint_hash}:"
        
        if get_redis_client:
            redis = await get_redis_client()
            keys = await redis.keys(f"{prefix}*")
            if keys:
                await redis.delete(*keys)
                count += len(keys)
                
        keys_to_del = [k for k in self._memory_cache.keys() if k.startswith(prefix)]
        for k in keys_to_del:
            del self._memory_cache[k]
            count += 1
            
        return count

    async def invalidate_tenant(self, tenant_id: str) -> int:
        count = 0
        prefix = f"platform:cache:{tenant_id}:"
        
        if get_redis_client:
            redis = await get_redis_client()
            keys = await redis.keys(f"{prefix}*")
            if keys:
                await redis.delete(*keys)
                count += len(keys)
                
        keys_to_del = [k for k in self._memory_cache.keys() if k.startswith(prefix)]
        for k in keys_to_del:
            del self._memory_cache[k]
            count += 1
            
        return count

    async def get_stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (self._hits / total) if total > 0 else 0.0,
            "total_keys": len(self._memory_cache),
            "memory_cache_size": len(self._memory_cache)
        }

    async def warm_cache(self, tenant_id: str, endpoints: list[dict]) -> int:
        count = 0
        for ep in endpoints:
            await self.set(tenant_id, ep.get("endpoint", ""), ep.get("params", {}), ep.get("value"))
            count += 1
        return count

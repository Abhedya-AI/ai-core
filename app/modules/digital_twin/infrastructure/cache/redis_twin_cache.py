from __future__ import annotations

import json
from typing import Any, Optional
from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.infrastructure.redis.client import redis_client
except ImportError:
    redis_client = None

class RedisTwinCache:
    def __init__(self):
        self._redis = redis_client
        self._fallback: dict[str, Any] = {}

    async def _get(self, key: str) -> Optional[dict[str, Any]]:
        if self._redis:
            try:
                data = await self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                log.warning(f"Redis get failed for {key}: {e}")
        return self._fallback.get(key)

    async def _set(self, key: str, data: dict[str, Any], ttl: int) -> None:
        if self._redis:
            try:
                await self._redis.setex(key, ttl, json.dumps(data))
                return
            except Exception as e:
                log.warning(f"Redis set failed for {key}: {e}")
        self._fallback[key] = data

    async def get_twin_state(self, twin_id: str) -> Optional[dict[str, Any]]:
        return await self._get(f"twin:state:{twin_id}")

    async def set_twin_state(self, twin_id: str, data: dict[str, Any]) -> None:
        await self._set(f"twin:state:{twin_id}", data, 30)

    async def get_entity_state(self, entity_id: str) -> Optional[dict[str, Any]]:
        return await self._get(f"twin:entity:{entity_id}")

    async def set_entity_state(self, entity_id: str, data: dict[str, Any]) -> None:
        await self._set(f"twin:entity:{entity_id}", data, 60)

    async def get_snapshot(self, snapshot_id: str) -> Optional[dict[str, Any]]:
        return await self._get(f"twin:snapshot:{snapshot_id}")

    async def set_snapshot(self, snapshot_id: str, data: dict[str, Any]) -> None:
        await self._set(f"twin:snapshot:{snapshot_id}", data, 3600)

    async def get_simulation(self, simulation_id: str) -> Optional[dict[str, Any]]:
        return await self._get(f"twin:sim:{simulation_id}")

    async def set_simulation(self, simulation_id: str, data: dict[str, Any]) -> None:
        await self._set(f"twin:sim:{simulation_id}", data, 600)

    async def get_optimization(self, optimization_id: str) -> Optional[dict[str, Any]]:
        return await self._get(f"twin:opt:{optimization_id}")

    async def set_optimization(self, optimization_id: str, data: dict[str, Any]) -> None:
        await self._set(f"twin:opt:{optimization_id}", data, 600)

    async def get_replay_session(self, replay_id: str) -> Optional[dict[str, Any]]:
        return await self._get(f"twin:replay:{replay_id}")

    async def set_replay_session(self, replay_id: str, data: dict[str, Any]) -> None:
        await self._set(f"twin:replay:{replay_id}", data, 1800)

    async def get_sync_status(self, twin_id: str) -> Optional[dict[str, Any]]:
        return await self._get(f"twin:sync:{twin_id}")

    async def set_sync_status(self, twin_id: str, data: dict[str, Any]) -> None:
        await self._set(f"twin:sync:{twin_id}", data, 30)

    async def get_twin_health(self, twin_id: str) -> Optional[dict[str, Any]]:
        return await self._get(f"twin:health:{twin_id}")

    async def set_twin_health(self, twin_id: str, data: dict[str, Any]) -> None:
        await self._set(f"twin:health:{twin_id}", data, 30)

    async def invalidate(self, key_prefix: str) -> None:
        if self._redis:
            try:
                keys = await self._redis.keys(f"{key_prefix}*")
                if keys:
                    await self._redis.delete(*keys)
            except Exception as e:
                log.warning(f"Redis invalidate failed for {key_prefix}: {e}")
        
        keys_to_remove = [k for k in self._fallback.keys() if k.startswith(key_prefix)]
        for k in keys_to_remove:
            del self._fallback[k]

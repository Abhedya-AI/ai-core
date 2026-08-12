from __future__ import annotations
import json
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class RedisHazardCache:
    def __init__(self) -> None:
        self._redis = None
        self._fallback: dict[str, Any] = {}
        try:
            from app.infrastructure.redis.client import redis_client
            self._redis = redis_client
        except Exception:
            log.warning("Redis client not available for Hazard Cache, using in-memory fallback")

    async def _get(self, key: str) -> dict[str, Any] | None:
        if self._redis:
            try:
                data = await self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                log.warning(f"Redis get failed: {e}")
        return self._fallback.get(key)

    async def _set(self, key: str, data: dict[str, Any], ttl: int) -> None:
        if self._redis:
            try:
                await self._redis.setex(key, ttl, json.dumps(data))
                return
            except Exception as e:
                log.warning(f"Redis set failed: {e}")
        self._fallback[key] = data

    async def get_propagation(self, propagation_id: str) -> dict[str, Any] | None:
        return await self._get(f"hazard:propagation:{propagation_id}")

    async def set_propagation(self, propagation_id: str, data: dict[str, Any]) -> None:
        await self._set(f"hazard:propagation:{propagation_id}", data, 120)

    async def get_exposure(self, propagation_id: str) -> dict[str, Any] | None:
        return await self._get(f"hazard:exposure:{propagation_id}")

    async def set_exposure(self, propagation_id: str, data: dict[str, Any]) -> None:
        await self._set(f"hazard:exposure:{propagation_id}", data, 60)

    async def get_containment(self, propagation_id: str) -> dict[str, Any] | None:
        return await self._get(f"hazard:containment:{propagation_id}")

    async def set_containment(self, propagation_id: str, data: dict[str, Any]) -> None:
        await self._set(f"hazard:containment:{propagation_id}", data, 300)

    async def get_evacuation(self, propagation_id: str) -> dict[str, Any] | None:
        return await self._get(f"hazard:evacuation:{propagation_id}")

    async def set_evacuation(self, propagation_id: str, data: dict[str, Any]) -> None:
        await self._set(f"hazard:evacuation:{propagation_id}", data, 60)

    async def get_simulation(self, simulation_id: str) -> dict[str, Any] | None:
        return await self._get(f"hazard:simulation:{simulation_id}")

    async def set_simulation(self, simulation_id: str, data: dict[str, Any]) -> None:
        await self._set(f"hazard:simulation:{simulation_id}", data, 600)

    async def invalidate(self, key_prefix: str) -> None:
        if self._redis:
            try:
                keys = await self._redis.keys(f"{key_prefix}*")
                if keys:
                    await self._redis.delete(*keys)
                return
            except Exception as e:
                log.warning(f"Redis invalidate failed: {e}")
        keys_to_delete = [k for k in self._fallback.keys() if k.startswith(key_prefix)]
        for k in keys_to_delete:
            del self._fallback[k]

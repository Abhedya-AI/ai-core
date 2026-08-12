from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger(__name__)

class RedisForecastCache:
    TTLs = {
        "forecast": 300,        # 5 minutes
        "scenario": 600,        # 10 minutes  
        "analytics": 120,       # 2 minutes
        "plant_forecast": 180,  # 3 minutes
    }
    
    def __init__(self, redis_client: Any = None):
        self._client = redis_client
        self._local: dict = {}
    
    async def _get_client(self) -> Any:
        if self._client:
            return self._client
        try:
            from app.infrastructure.redis.client import get_client
            self._client = await get_client()
            return self._client
        except Exception:
            return None

    async def cache_forecast(self, entity_id: str, forecast_type: str, horizon: str, data: dict) -> None:
        key = f"forecast:{entity_id}:{forecast_type}:{horizon}"
        client = await self._get_client()
        if client:
            try:
                await client.setex(key, self.TTLs["forecast"], json.dumps(data))
            except Exception as e:
                log.error(f"Redis error: {e}")
        else:
            self._local[key] = data

    async def get_cached_forecast(self, entity_id: str, forecast_type: str, horizon: str) -> dict | None:
        key = f"forecast:{entity_id}:{forecast_type}:{horizon}"
        client = await self._get_client()
        if client:
            try:
                val = await client.get(key)
                if val:
                    return json.loads(val)
            except Exception:
                pass
        return self._local.get(key)

    async def cache_plant_forecast(self, plant_id: str, data: dict) -> None:
        key = f"forecast:plant:{plant_id}"
        client = await self._get_client()
        if client:
            try:
                await client.setex(key, self.TTLs["plant_forecast"], json.dumps(data))
            except Exception:
                pass
        else:
            self._local[key] = data

    async def get_cached_plant_forecast(self, plant_id: str) -> dict | None:
        key = f"forecast:plant:{plant_id}"
        client = await self._get_client()
        if client:
            try:
                val = await client.get(key)
                if val:
                    return json.loads(val)
            except Exception:
                pass
        return self._local.get(key)

    async def cache_scenario(self, entity_id: str, forecast_type: str, data: dict) -> None:
        key = f"forecast:scenario:{entity_id}:{forecast_type}"
        client = await self._get_client()
        if client:
            try:
                await client.setex(key, self.TTLs["scenario"], json.dumps(data))
            except Exception:
                pass
        else:
            self._local[key] = data

    async def get_cached_scenario(self, entity_id: str, forecast_type: str) -> dict | None:
        key = f"forecast:scenario:{entity_id}:{forecast_type}"
        client = await self._get_client()
        if client:
            try:
                val = await client.get(key)
                if val:
                    return json.loads(val)
            except Exception:
                pass
        return self._local.get(key)

    async def invalidate_entity(self, entity_id: str) -> None:
        # Simplified invalidation, typically you'd use SCAN or keep track of keys
        to_delete = [k for k in self._local if f":{entity_id}:" in k]
        for k in to_delete:
            del self._local[k]

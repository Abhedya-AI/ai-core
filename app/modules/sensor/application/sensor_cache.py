"""
sensor/application/sensor_cache.py — Sensor Intelligence Cache Layer.

Redis-backed cache with in-memory fallback for:
  - Latest readings per sensor
  - Latest anomalies per sensor
  - Latest health states
  - Rolling averages
  - Zone summaries
  - Fleet summary

Cache strategy:
  - Write-through: update cache immediately on ingestion
  - TTL: readings=300s, anomalies=3600s, health=60s, fleet=30s
  - Graceful degradation: if Redis unavailable, use in-memory dict
"""
from __future__ import annotations
import json
import time
from typing import Any
from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly, SensorHealthState

log = get_logger("sensor.sensor_cache")

class SensorCache:
    """Cache layer for fast retrieval of sensor states using Redis with memory fallback."""
    
    def __init__(self):
        self._redis = None
        self._local: dict[str, Any] = {}
        self._local_ttl: dict[str, float] = {}
        self._use_redis: bool = False
        self._connect_redis()
        
    def _connect_redis(self) -> bool:
        """Initialize Redis connection if available."""
        try:
            import redis.asyncio as aioredis
            from app.core.config.settings import get_settings
            settings = get_settings()
            url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
            self._redis = aioredis.from_url(url, decode_responses=True, socket_timeout=1.0)
            self._use_redis = True
            return True
        except Exception as exc:
            log.warning(f"Redis unavailable, using in-memory cache: {exc}")
            self._use_redis = False
            return False
            
    def _set_local(self, key: str, value: Any, ttl: int) -> None:
        """Set value in local in-memory fallback cache."""
        self._local[key] = value
        self._local_ttl[key] = time.time() + ttl
        
    def _get_local(self, key: str) -> Any | None:
        """Get value from local cache if not expired."""
        if key not in self._local:
            return None
        if time.time() > self._local_ttl.get(key, 0):
            self._local.pop(key, None)
            self._local_ttl.pop(key, None)
            return None
        return self._local[key]

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a value in cache with TTL."""
        val_str = json.dumps(value) if not isinstance(value, str) else value
        if self._use_redis and self._redis:
            try:
                await self._redis.set(key, val_str, ex=ttl)
                return
            except Exception as e:
                log.warning(f"Redis set failed for {key}: {e}")
        self._set_local(key, val_str, ttl)
        
    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        val_str = None
        if self._use_redis and self._redis:
            try:
                val_str = await self._redis.get(key)
            except Exception as e:
                log.warning(f"Redis get failed for {key}: {e}")
                
        if val_str is None:
            val_str = self._get_local(key)
            
        if val_str is not None:
            try:
                return json.loads(val_str)
            except Exception:
                return val_str
        return None

    async def cache_reading(self, reading: SensorReading) -> None:
        """Cache the latest sensor reading."""
        key = f"sensor:reading:{reading.sensor_id}"
        val = reading.model_dump(mode="json") if hasattr(reading, "model_dump") else reading.dict()
        await self.set(key, val, ttl=300)
        
    async def cache_anomaly(self, anomaly: SensorAnomaly) -> None:
        """Cache the latest anomaly and append to recent list."""
        key = f"sensor:anomaly:{anomaly.sensor_id}:latest"
        val = anomaly.model_dump(mode="json") if hasattr(anomaly, "model_dump") else anomaly.dict()
        await self.set(key, val, ttl=3600)
        
        if self._use_redis and self._redis:
            try:
                list_key = f"sensor:anomalies:{anomaly.sensor_id}"
                await self._redis.lpush(list_key, json.dumps(val))
                await self._redis.ltrim(list_key, 0, 49)
            except Exception as e:
                log.warning(f"Failed to update anomalies list for {anomaly.sensor_id}: {e}")

    async def cache_health(self, state: SensorHealthState) -> None:
        """Cache the latest sensor health state."""
        key = f"sensor:health:{state.sensor_id}"
        val = state.model_dump(mode="json") if hasattr(state, "model_dump") else state.dict()
        await self.set(key, val, ttl=60)
        
    async def get_latest_reading(self, sensor_id: str) -> dict | None:
        """Get the latest reading for a sensor."""
        key = f"sensor:reading:{sensor_id}"
        return await self.get(key)
        
    async def get_latest_anomaly(self, sensor_id: str) -> dict | None:
        """Get the latest anomaly for a sensor."""
        key = f"sensor:anomaly:{sensor_id}:latest"
        return await self.get(key)
        
    async def get_health(self, sensor_id: str) -> dict | None:
        """Get the health state for a sensor."""
        key = f"sensor:health:{sensor_id}"
        return await self.get(key)
        
    async def cache_zone_summary(self, zone_id: str, summary: dict) -> None:
        """Cache a zone summary."""
        key = f"sensor:zone:{zone_id}:summary"
        await self.set(key, summary, ttl=30)
        
    async def get_zone_summary(self, zone_id: str) -> dict | None:
        """Get a cached zone summary."""
        key = f"sensor:zone:{zone_id}:summary"
        return await self.get(key)
        
    async def cache_fleet_summary(self, summary: dict) -> None:
        """Cache the global fleet summary."""
        key = "sensor:fleet:summary"
        await self.set(key, summary, ttl=30)
        
    async def get_fleet_summary(self) -> dict | None:
        """Get the cached global fleet summary."""
        key = "sensor:fleet:summary"
        return await self.get(key)

from __future__ import annotations

import time
import asyncio
from typing import Any
from pydantic import BaseModel, ConfigDict
from enum import Enum

from app.core.logging import get_logger
log = get_logger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


class HealthReport(BaseModel):
    model_config = ConfigDict(frozen=True)
    status: HealthStatus
    uptime_seconds: float
    components: dict[str, dict]


class PlatformHealthAggregator:
    def __init__(self):
        self._start_time = time.time()
        self._last_checks: dict[str, dict] = {}

    async def check_component(self, name: str, check_fn: Any) -> tuple[str, HealthStatus, float]:
        start = time.perf_counter()
        try:
            status = await asyncio.wait_for(check_fn(), timeout=5.0)
            status_enum = HealthStatus.HEALTHY if status else HealthStatus.UNHEALTHY
        except Exception as e:
            log.warning(f"Health check for {name} failed: {e}")
            status_enum = HealthStatus.UNHEALTHY
            
        latency_ms = (time.perf_counter() - start) * 1000
        return (name, status_enum, latency_ms)

    async def _check_postgres(self) -> bool:
        try:
            from app.infrastructure.postgres.health import check_postgres_health
            return await check_postgres_health()
        except ImportError:
            return False

    async def _check_redis(self) -> bool:
        try:
            from app.infrastructure.redis.health import check_redis_health
            return await check_redis_health()
        except ImportError:
            return False

    async def _check_neo4j(self) -> bool:
        try:
            from app.infrastructure.neo4j.health import check_neo4j_health
            return await check_neo4j_health()
        except ImportError:
            return False

    async def _check_kafka(self) -> bool:
        try:
            from app.infrastructure.kafka.health import check_kafka_health
            return await check_kafka_health()
        except ImportError:
            return False
            
    async def _check_memory_component(self) -> bool:
        return True

    async def aggregate_health(self) -> HealthReport:
        tasks = [
            self.check_component("postgres", self._check_postgres),
            self.check_component("redis", self._check_redis),
            self.check_component("neo4j", self._check_neo4j),
            self.check_component("kafka", self._check_kafka),
            self.check_component("model_registry", self._check_memory_component),
            self.check_component("feature_store", self._check_memory_component)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        components = {}
        all_healthy = True
        any_unhealthy = False
        
        for res in results:
            if isinstance(res, tuple):
                name, status, latency = res
                components[name] = {
                    "status": status.value,
                    "latency_ms": latency,
                    "checked_at": time.time()
                }
                self._last_checks[name] = components[name]
                if status == HealthStatus.UNHEALTHY:
                    all_healthy = False
                    any_unhealthy = True
                elif status == HealthStatus.DEGRADED:
                    all_healthy = False
                    
        overall_status = HealthStatus.HEALTHY
        if any_unhealthy:
            overall_status = HealthStatus.UNHEALTHY
        elif not all_healthy:
            overall_status = HealthStatus.DEGRADED
            
        return HealthReport(
            status=overall_status,
            uptime_seconds=await self.get_uptime(),
            components=components
        )

    async def get_component_health(self, component: str) -> dict:
        return self._last_checks.get(component, {
            "component": component,
            "status": "UNKNOWN",
            "latency_ms": 0.0,
            "checked_at": 0.0
        })

    async def get_uptime(self) -> float:
        return time.time() - self._start_time

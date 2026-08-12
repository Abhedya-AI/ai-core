from __future__ import annotations

import time
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict
from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.infrastructure.redis.client import get_redis_client
except ImportError:
    get_redis_client = None

try:
    from app.modules.platform.domain.models import QuotaUsage
except ImportError:
    class QuotaUsage(BaseModel):
        model_config = ConfigDict(frozen=True)
        tenant_id: str
        api_calls_minute: int
        model_versions: int
        storage_gb: float
        simulations: int
        last_updated: str

class QuotaManager:
    def __init__(self) -> None:
        self._counters: dict[str, dict] = {}

    def _get_tenant_store(self, tenant_id: str) -> dict:
        if tenant_id not in self._counters:
            self._counters[tenant_id] = {
                "api_calls_minute": 0,
                "api_minute_reset": time.time() + 60,
                "model_versions": 0,
                "storage_gb": 0.0,
                "simulations": 0,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        return self._counters[tenant_id]

    async def check_api_quota(self, tenant_id: str, limit: int) -> dict:
        start_time = time.perf_counter()
        try:
            store = self._get_tenant_store(tenant_id)
            now = time.time()
            if now > store["api_minute_reset"]:
                store["api_calls_minute"] = 0
                store["api_minute_reset"] = now + 60

            allowed = store["api_calls_minute"] < limit
            return {
                "allowed": allowed,
                "current": store["api_calls_minute"],
                "limit": limit,
                "remaining": max(0, limit - store["api_calls_minute"])
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"check_api_quota executed in {latency:.4f}s")

    async def increment_api_calls(self, tenant_id: str) -> int:
        start_time = time.perf_counter()
        try:
            store = self._get_tenant_store(tenant_id)
            now = time.time()
            if now > store["api_minute_reset"]:
                store["api_calls_minute"] = 0
                store["api_minute_reset"] = now + 60
                
            store["api_calls_minute"] += 1
            store["last_updated"] = datetime.now(timezone.utc).isoformat()
            return store["api_calls_minute"]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"increment_api_calls executed in {latency:.4f}s")

    async def check_model_quota(self, tenant_id: str, current_count: int, limit: int) -> dict:
        start_time = time.perf_counter()
        try:
            store = self._get_tenant_store(tenant_id)
            store["model_versions"] = current_count
            store["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            allowed = current_count < limit
            return {
                "allowed": allowed,
                "current": current_count,
                "limit": limit,
                "remaining": max(0, limit - current_count)
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"check_model_quota executed in {latency:.4f}s")

    async def check_storage_quota(self, tenant_id: str, requested_gb: float, limit_gb: float) -> dict:
        start_time = time.perf_counter()
        try:
            store = self._get_tenant_store(tenant_id)
            current = store["storage_gb"]
            projected = current + requested_gb
            allowed = projected <= limit_gb
            return {
                "allowed": allowed,
                "current": current,
                "requested": requested_gb,
                "limit": limit_gb,
                "remaining": max(0.0, limit_gb - current)
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"check_storage_quota executed in {latency:.4f}s")

    async def get_usage(self, tenant_id: str) -> QuotaUsage:
        start_time = time.perf_counter()
        try:
            store = self._get_tenant_store(tenant_id)
            return QuotaUsage(
                tenant_id=tenant_id,
                api_calls_minute=store["api_calls_minute"],
                model_versions=store["model_versions"],
                storage_gb=store["storage_gb"],
                simulations=store["simulations"],
                last_updated=store["last_updated"]
            )
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_usage executed in {latency:.4f}s")

    async def reset_minute_counter(self, tenant_id: str) -> None:
        start_time = time.perf_counter()
        try:
            if tenant_id in self._counters:
                self._counters[tenant_id]["api_calls_minute"] = 0
                self._counters[tenant_id]["api_minute_reset"] = time.time() + 60
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"reset_minute_counter executed in {latency:.4f}s")

    async def record_storage_usage(self, tenant_id: str, delta_gb: float) -> float:
        start_time = time.perf_counter()
        try:
            store = self._get_tenant_store(tenant_id)
            store["storage_gb"] = max(0.0, store["storage_gb"] + delta_gb)
            store["last_updated"] = datetime.now(timezone.utc).isoformat()
            return store["storage_gb"]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"record_storage_usage executed in {latency:.4f}s")

    async def get_all_tenants_usage(self) -> list[QuotaUsage]:
        start_time = time.perf_counter()
        try:
            return [
                QuotaUsage(
                    tenant_id=tid,
                    api_calls_minute=store["api_calls_minute"],
                    model_versions=store["model_versions"],
                    storage_gb=store["storage_gb"],
                    simulations=store["simulations"],
                    last_updated=store["last_updated"]
                )
                for tid, store in self._counters.items()
            ]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_all_tenants_usage executed in {latency:.4f}s")

    async def alert_quota_exceeded(self, tenant_id: str, quota_type: str, used: float, limit: float) -> None:
        start_time = time.perf_counter()
        try:
            log.warning(f"QUOTA EXCEEDED: Tenant {tenant_id} exceeded {quota_type} (Used: {used}, Limit: {limit})")
            try:
                from app.infrastructure.kafka.producer import EventBus
                if EventBus:
                    # Mock event publishing
                    pass
            except ImportError:
                pass
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"alert_quota_exceeded executed in {latency:.4f}s")

_service_instance = None
def get_service() -> QuotaManager:
    global _service_instance
    if _service_instance is None:
        _service_instance = QuotaManager()
    return _service_instance

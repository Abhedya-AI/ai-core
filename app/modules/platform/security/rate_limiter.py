from __future__ import annotations

import time
from datetime import datetime, timezone

from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.infrastructure.redis.client import get_redis_client
except ImportError:
    get_redis_client = None

TIER_LIMITS: dict[str, int] = {
    "COMMUNITY": 100,
    "PROFESSIONAL": 1000,
    "ENTERPRISE": 10000,
    "GOVERNMENT": 50000
}

class AdvancedRateLimiter:
    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = {}
        self._blocked: int = 0
        self._total: int = 0

    async def check_and_increment(self, tenant_id: str, endpoint: str, tier: str = "COMMUNITY") -> dict:
        start_time = time.perf_counter()
        try:
            self._total += 1
            limit = TIER_LIMITS.get(tier, TIER_LIMITS["COMMUNITY"])
            key = f"{tenant_id}:{endpoint}"
            now = time.time()
            
            redis = get_redis_client() if get_redis_client else None
            
            if redis:
                # Simplified redis fallback logic for interface compliance
                log.warning("Redis client integration mocked.")
                
            if key not in self._windows:
                self._windows[key] = []
                
            # Sliding window: keep timestamps within last 60 seconds
            self._windows[key] = [ts for ts in self._windows[key] if now - ts < 60]
            
            count = len(self._windows[key])
            if count >= limit:
                self._blocked += 1
                return {
                    "allowed": False,
                    "count": count,
                    "limit": limit,
                    "remaining": 0,
                    "reset_at": datetime.fromtimestamp(self._windows[key][0] + 60, timezone.utc).isoformat(),
                    "tier": tier
                }
                
            self._windows[key].append(now)
            
            return {
                "allowed": True,
                "count": count + 1,
                "limit": limit,
                "remaining": limit - (count + 1),
                "reset_at": datetime.fromtimestamp(self._windows[key][0] + 60 if self._windows[key] else now + 60, timezone.utc).isoformat(),
                "tier": tier
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"check_and_increment executed in {latency:.4f}s")

    async def check_burst(self, tenant_id: str, endpoint: str, burst_limit: int = 50, burst_window_seconds: int = 10) -> bool:
        start_time = time.perf_counter()
        try:
            key = f"{tenant_id}:{endpoint}"
            if key not in self._windows:
                return True
                
            now = time.time()
            burst_requests = [ts for ts in self._windows[key] if now - ts < burst_window_seconds]
            return len(burst_requests) <= burst_limit
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"check_burst executed in {latency:.4f}s")

    async def get_usage(self, tenant_id: str) -> dict:
        start_time = time.perf_counter()
        try:
            endpoints = {}
            total_count = 0
            
            prefix = f"{tenant_id}:"
            for k, timestamps in self._windows.items():
                if k.startswith(prefix):
                    endpoint = k[len(prefix):]
                    count = len(timestamps)
                    endpoints[endpoint] = count
                    total_count += count
                    
            return {
                "tenant_id": tenant_id,
                "current_minute_count": total_count,
                "endpoints": endpoints,
                "tier": "UNKNOWN" # To be enriched by caller
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_usage executed in {latency:.4f}s")

    async def reset(self, tenant_id: str, endpoint: str) -> None:
        start_time = time.perf_counter()
        try:
            key = f"{tenant_id}:{endpoint}"
            if key in self._windows:
                del self._windows[key]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"reset executed in {latency:.4f}s")

    async def get_stats(self) -> dict:
        return {
            "tracked_keys": len(self._windows),
            "total_requests": self._total,
            "blocked_requests": self._blocked
        }

_service_instance = None
def get_service() -> AdvancedRateLimiter:
    global _service_instance
    if _service_instance is None:
        _service_instance = AdvancedRateLimiter()
    return _service_instance

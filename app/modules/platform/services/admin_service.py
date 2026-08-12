from __future__ import annotations
import time
import uuid
from typing import Any
from datetime import datetime, timezone

from app.core.logging import get_logger
log = get_logger(__name__)

class AdminService:
    def __init__(self, tenant_manager=None, health_aggregator=None, cost_tracker=None, event_publisher=None):
        self.tenant_manager = tenant_manager
        self.health_aggregator = health_aggregator
        self.cost_tracker = cost_tracker
        self.event_publisher = event_publisher
        self._maintenance_mode = False
        self._maintenance_reason = ""
        self._start_time = time.time()

    async def get_system_status(self) -> dict:
        t0 = time.perf_counter()
        uptime = time.time() - self._start_time
        
        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "version": "1.0.0",
            "sprint": "12",
            "uptime_seconds": uptime,
            "maintenance_mode": self._maintenance_mode,
            "environment": "PRODUCTION",
            "active_tenants": 42,
            "total_requests": 1000000,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "latency_ms": latency_ms
        }

    async def enable_maintenance_mode(self, reason: str, enabled_by: str) -> dict:
        self._maintenance_mode = True
        self._maintenance_reason = reason
        log.warning(f"Maintenance mode enabled by {enabled_by}: {reason}")
        return {"status": "ENABLED", "reason": reason}

    async def disable_maintenance_mode(self, disabled_by: str) -> dict:
        self._maintenance_mode = False
        self._maintenance_reason = ""
        log.info(f"Maintenance mode disabled by {disabled_by}")
        return {"status": "DISABLED"}

    async def get_system_config(self) -> dict:
        return {
            "max_workers": 16,
            "cache_ttl": 3600,
            "batch_size": 256,
            "rate_limits": {"api": 1000, "inference": 500}
        }

    async def list_tenants(self, tier: str | None, is_active: bool | None, limit: int, offset: int) -> dict:
        t0 = time.perf_counter()
        latency_ms = (time.perf_counter() - t0) * 1000
        return {"items": [], "total": 0, "limit": limit, "offset": offset, "latency_ms": latency_ms}

    async def suspend_tenant(self, tenant_id: str, reason: str, by: str) -> dict:
        return {"tenant_id": tenant_id, "status": "SUSPENDED", "reason": reason}

    async def reactivate_tenant(self, tenant_id: str, by: str) -> dict:
        return {"tenant_id": tenant_id, "status": "ACTIVE"}

    async def get_cost_summary(self, tenant_id: str | None, period: str) -> dict:
        t0 = time.perf_counter()
        # Mock logic
        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "period": period,
            "tenant_id": tenant_id or "ALL",
            "total_cost_usd": 1500.50,
            "latency_ms": latency_ms
        }

    async def trigger_backup(self, backup_type: str, triggered_by: str) -> dict:
        t0 = time.perf_counter()
        backup_id = str(uuid.uuid4())
        log.info(f"Triggered {backup_type} backup by {triggered_by}, id {backup_id}")
        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "backup_id": backup_id,
            "type": backup_type,
            "status": "INITIATED",
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "latency_ms": latency_ms
        }

    async def get_admin_analytics(self) -> dict:
        return {
            "usage_stats": {},
            "top_tenants": []
        }

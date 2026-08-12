from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict
from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.modules.platform.domain.models import TenantProfile
    from app.modules.platform.domain.enums import TenantTier
except ImportError:
    TenantTier = str
    class TenantProfile(BaseModel):
        model_config = ConfigDict(frozen=True)
        tenant_id: str
        name: str
        slug: str
        description: str
        tier: TenantTier
        contact_email: str
        max_plants: int
        max_api_calls_per_minute: int
        max_model_versions: int
        max_storage_gb: float
        is_active: bool
        created_at: str
        updated_at: str

class TenantManager:
    def __init__(self) -> None:
        self._tenants: dict[str, TenantProfile] = {}
        self._slug_index: dict[str, str] = {}

    def _get_tier_limits(self, tier: str) -> dict:
        limits = {
            "COMMUNITY": {"max_plants": 1, "max_api_calls": 100, "max_models": 5, "max_storage_gb": 10.0},
            "PROFESSIONAL": {"max_plants": 5, "max_api_calls": 1000, "max_models": 50, "max_storage_gb": 100.0},
            "ENTERPRISE": {"max_plants": 50, "max_api_calls": 10000, "max_models": 500, "max_storage_gb": 1000.0},
            "GOVERNMENT": {"max_plants": 100, "max_api_calls": 50000, "max_models": 2000, "max_storage_gb": 10000.0},
        }
        return limits.get(tier, limits["COMMUNITY"])

    async def create(self, name: str, slug: str, description: str, tier: str, contact_email: str) -> TenantProfile:
        start_time = time.perf_counter()
        try:
            if not slug.replace("-", "").isalnum() or not slug.islower():
                raise ValueError("Slug must be lowercase alphanumeric with hyphens")
            
            if slug in self._slug_index:
                raise ValueError("Tenant slug already exists")

            tenant_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            limits = self._get_tier_limits(tier)

            tenant = TenantProfile(
                tenant_id=tenant_id,
                name=name,
                slug=slug,
                description=description,
                tier=tier,
                contact_email=contact_email,
                max_plants=limits["max_plants"],
                max_api_calls_per_minute=limits["max_api_calls"],
                max_model_versions=limits["max_models"],
                max_storage_gb=limits["max_storage_gb"],
                is_active=True,
                created_at=now,
                updated_at=now
            )

            self._tenants[tenant_id] = tenant
            self._slug_index[slug] = tenant_id

            return tenant
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"Tenant {name} created in {latency:.4f}s")

    async def get(self, tenant_id: str) -> TenantProfile | None:
        return self._tenants.get(tenant_id)

    async def get_by_slug(self, slug: str) -> TenantProfile | None:
        tenant_id = self._slug_index.get(slug)
        if tenant_id:
            return self._tenants.get(tenant_id)
        return None

    async def list(self, tier: str | None = None, is_active: bool | None = None, limit: int = 50, offset: int = 0) -> list[TenantProfile]:
        start_time = time.perf_counter()
        try:
            results = list(self._tenants.values())
            if tier:
                results = [t for t in results if t.tier == tier]
            if is_active is not None:
                results = [t for t in results if t.is_active == is_active]
            return results[offset:offset + limit]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"list tenants executed in {latency:.4f}s")

    async def update(self, tenant_id: str, updates: dict) -> TenantProfile:
        start_time = time.perf_counter()
        try:
            tenant = self._tenants.get(tenant_id)
            if not tenant:
                raise ValueError("Tenant not found")
            
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated_tenant = tenant.model_copy(update=updates)
            self._tenants[tenant_id] = updated_tenant

            if "slug" in updates and updates["slug"] != tenant.slug:
                del self._slug_index[tenant.slug]
                self._slug_index[updates["slug"]] = tenant_id

            return updated_tenant
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"update tenant executed in {latency:.4f}s")

    async def suspend(self, tenant_id: str, reason: str) -> TenantProfile:
        log.info(f"Suspending tenant {tenant_id}. Reason: {reason}")
        return await self.update(tenant_id, {"is_active": False})

    async def reactivate(self, tenant_id: str) -> TenantProfile:
        log.info(f"Reactivating tenant {tenant_id}.")
        return await self.update(tenant_id, {"is_active": True})

    async def delete(self, tenant_id: str) -> bool:
        start_time = time.perf_counter()
        try:
            if tenant_id in self._tenants:
                tenant = self._tenants[tenant_id]
                del self._slug_index[tenant.slug]
                del self._tenants[tenant_id]
                return True
            return False
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"delete tenant executed in {latency:.4f}s")

    async def get_tenant_limits(self, tenant_id: str) -> dict:
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")
        return {
            "max_plants": tenant.max_plants,
            "max_api_calls_per_minute": tenant.max_api_calls_per_minute,
            "max_model_versions": tenant.max_model_versions,
            "max_storage_gb": tenant.max_storage_gb,
            "tier": tenant.tier
        }

    async def count(self) -> dict:
        total = len(self._tenants)
        active = sum(1 for t in self._tenants.values() if t.is_active)
        tiers = {}
        for t in self._tenants.values():
            tiers[t.tier] = tiers.get(t.tier, 0) + 1

        return {
            "total": total,
            "by_tier": tiers,
            "active_count": active,
            "suspended_count": total - active
        }

_service_instance = None
def get_service() -> TenantManager:
    global _service_instance
    if _service_instance is None:
        _service_instance = TenantManager()
    return _service_instance

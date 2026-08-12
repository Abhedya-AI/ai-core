from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone, timedelta

from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.modules.platform.domain.enums import LicenseTier
except ImportError:
    LicenseTier = str

FEATURE_GATES: dict[str, set[str]] = {
    "COMMUNITY": {"basic_risk", "basic_forecast", "basic_sensor", "api_access"},
    "PROFESSIONAL": {"basic_risk", "advanced_risk", "basic_forecast", "advanced_forecast", "hazard_propagation", "digital_twin", "basic_sensor", "advanced_sensor", "api_access", "websocket_access", "model_registry"},
    "ENTERPRISE": {"all_features", "model_registry", "feature_store", "online_learning", "drift_detection", "governance", "multi_plant", "multi_tenant", "api_access", "websocket_access", "observability", "deployment_automation"},
    "UNLIMITED": {"all_features", "source_code_access", "dedicated_support", "custom_models", "on_premise"},
}

class LicenseManager:
    def __init__(self) -> None:
        self._licenses: dict[str, dict] = {}

    async def issue_license(self, tenant_id: str, tier: str, expires_at: str | None = None) -> dict:
        start_time = time.perf_counter()
        try:
            if not expires_at:
                expires_at = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
                
            license_key = f"LIC-{uuid.uuid4().hex.upper()}"
            now = datetime.now(timezone.utc).isoformat()
            
            features = FEATURE_GATES.get(tier, FEATURE_GATES["COMMUNITY"])
            
            license_record = {
                "tenant_id": tenant_id,
                "tier": tier,
                "expires_at": expires_at,
                "features": list(features),
                "issued_at": now,
                "license_key": license_key
            }
            
            self._licenses[tenant_id] = license_record
            log.info(f"Issued license {license_key} for tenant {tenant_id} (Tier: {tier})")
            return license_record
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"issue_license executed in {latency:.4f}s")

    async def validate_license(self, tenant_id: str) -> dict:
        start_time = time.perf_counter()
        try:
            record = self._licenses.get(tenant_id)
            if not record:
                return {"valid": False, "tier": None, "expires_at": None, "days_remaining": None, "expired": True}
                
            exp_dt = datetime.fromisoformat(record["expires_at"])
            now = datetime.now(timezone.utc)
            
            days_remaining = (exp_dt - now).days
            is_expired = now > exp_dt
            
            return {
                "valid": not is_expired,
                "tier": record["tier"],
                "expires_at": record["expires_at"],
                "days_remaining": days_remaining,
                "expired": is_expired
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"validate_license executed in {latency:.4f}s")

    async def check_feature(self, tenant_id: str, feature: str) -> bool:
        start_time = time.perf_counter()
        try:
            validity = await self.validate_license(tenant_id)
            if not validity["valid"]:
                return False
                
            record = self._licenses.get(tenant_id)
            if not record:
                return False
                
            features = record["features"]
            if "all_features" in features:
                return True
                
            return feature in features
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"check_feature executed in {latency:.4f}s")

    async def get_available_features(self, tenant_id: str) -> list[str]:
        start_time = time.perf_counter()
        try:
            record = self._licenses.get(tenant_id)
            if not record:
                return []
                
            features = record["features"]
            return sorted(list(features))
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_available_features executed in {latency:.4f}s")

    async def revoke_license(self, tenant_id: str) -> bool:
        start_time = time.perf_counter()
        try:
            if tenant_id in self._licenses:
                del self._licenses[tenant_id]
                log.info(f"Revoked license for tenant {tenant_id}")
                return True
            return False
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"revoke_license executed in {latency:.4f}s")

    async def extend_license(self, tenant_id: str, extend_days: int) -> dict:
        start_time = time.perf_counter()
        try:
            record = self._licenses.get(tenant_id)
            if not record:
                raise ValueError("License not found")
                
            exp_dt = datetime.fromisoformat(record["expires_at"])
            new_exp = exp_dt + timedelta(days=extend_days)
            record["expires_at"] = new_exp.isoformat()
            
            self._licenses[tenant_id] = record
            log.info(f"Extended license for {tenant_id} by {extend_days} days")
            return record
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"extend_license executed in {latency:.4f}s")

    async def get_usage_report(self, tenant_id: str) -> dict:
        start_time = time.perf_counter()
        try:
            record = self._licenses.get(tenant_id)
            validity = await self.validate_license(tenant_id)
            
            if not record:
                return {
                    "tenant_id": tenant_id,
                    "tier": "NONE",
                    "features_used": [],
                    "features_available": [],
                    "license_valid": False
                }
                
            return {
                "tenant_id": tenant_id,
                "tier": record["tier"],
                "features_used": [], # Placeholder for actual feature usage tracking
                "features_available": record["features"],
                "license_valid": validity["valid"]
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_usage_report executed in {latency:.4f}s")

    async def list_expiring(self, days: int = 30) -> list[dict]:
        start_time = time.perf_counter()
        try:
            now = datetime.now(timezone.utc)
            threshold = now + timedelta(days=days)
            
            expiring = []
            for tid, record in self._licenses.items():
                exp_dt = datetime.fromisoformat(record["expires_at"])
                if now < exp_dt <= threshold:
                    expiring.append(record)
                    
            return expiring
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"list_expiring executed in {latency:.4f}s")

_service_instance = None
def get_service() -> LicenseManager:
    global _service_instance
    if _service_instance is None:
        _service_instance = LicenseManager()
    return _service_instance

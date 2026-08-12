from __future__ import annotations

import time
import uuid
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict
from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from argon2 import PasswordHasher
    _ph = PasswordHasher()
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False

try:
    from app.modules.platform.domain.models import ApiKey
except ImportError:
    class ApiKey(BaseModel):
        model_config = ConfigDict(frozen=True)
        key_id: str
        key_prefix: str
        key_hash: str
        tenant_id: str
        name: str
        description: str
        scopes: list[str]
        created_by: str
        created_at: str
        expires_at: str | None
        last_used_at: str | None
        is_active: bool

class APIKeyManager:
    def __init__(self) -> None:
        self._keys: dict[str, ApiKey] = {}
        self._prefix_index: dict[str, str] = {}
        self._redis_ttl: int = 3600

    def _hash_key(self, raw_key: str) -> str:
        if ARGON2_AVAILABLE:
            return _ph.hash(raw_key)
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def _verify_hash(self, hash_str: str, raw_key: str) -> bool:
        if ARGON2_AVAILABLE and hash_str.startswith("$argon2"):
            try:
                return _ph.verify(hash_str, raw_key)
            except Exception:
                return False
        return hashlib.sha256(raw_key.encode()).hexdigest() == hash_str

    async def generate(self, tenant_id: str, name: str, description: str, scopes: list[str], created_by: str, expires_at: str | None = None) -> dict:
        start_time = time.perf_counter()
        try:
            key_id = str(uuid.uuid4())
            raw_key = "abhedya_" + secrets.token_urlsafe(32)
            key_prefix = raw_key[:8]
            key_hash = self._hash_key(raw_key)
            created_at = datetime.now(timezone.utc).isoformat()

            api_key = ApiKey(
                key_id=key_id,
                key_prefix=key_prefix,
                key_hash=key_hash,
                tenant_id=tenant_id,
                name=name,
                description=description,
                scopes=scopes,
                created_by=created_by,
                created_at=created_at,
                expires_at=expires_at,
                last_used_at=None,
                is_active=True
            )

            self._keys[key_id] = api_key
            self._prefix_index[key_prefix] = key_id

            return {
                "key_id": key_id,
                "raw_key": raw_key,
                "key_prefix": key_prefix,
                "scopes": scopes,
                "name": name
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"API key generated in {latency:.4f}s")

    async def verify(self, raw_key: str) -> ApiKey | None:
        start_time = time.perf_counter()
        try:
            prefix = raw_key[:8]
            key_id = self._prefix_index.get(prefix)
            if not key_id:
                return None
            
            api_key = self._keys.get(key_id)
            if not api_key or not api_key.is_active:
                return None
                
            if api_key.expires_at:
                exp_dt = datetime.fromisoformat(api_key.expires_at)
                if datetime.now(timezone.utc) > exp_dt:
                    return None

            if not self._verify_hash(api_key.key_hash, raw_key):
                return None

            # Update last used
            updated_key = api_key.model_copy(update={"last_used_at": datetime.now(timezone.utc).isoformat()})
            self._keys[key_id] = updated_key

            return updated_key
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"API key verified in {latency:.4f}s")

    async def revoke(self, key_id: str, revoked_by: str) -> bool:
        start_time = time.perf_counter()
        try:
            if key_id not in self._keys:
                return False
            old_key = self._keys[key_id]
            self._keys[key_id] = old_key.model_copy(update={"is_active": False})
            log.info(f"API key {key_id} revoked by {revoked_by}")
            return True
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"API key revoked in {latency:.4f}s")

    async def list(self, tenant_id: str) -> list[ApiKey]:
        start_time = time.perf_counter()
        try:
            return [k for k in self._keys.values() if k.tenant_id == tenant_id]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"API keys listed in {latency:.4f}s")

    async def get(self, key_id: str) -> ApiKey | None:
        return self._keys.get(key_id)

    async def rotate(self, key_id: str, created_by: str) -> dict:
        start_time = time.perf_counter()
        try:
            old_key = self._keys.get(key_id)
            if not old_key:
                raise ValueError("Key not found")
            
            await self.revoke(key_id, created_by)
            
            return await self.generate(
                tenant_id=old_key.tenant_id,
                name=old_key.name,
                description=old_key.description,
                scopes=old_key.scopes,
                created_by=created_by,
                expires_at=old_key.expires_at
            )
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"API key rotated in {latency:.4f}s")

    async def check_scope(self, key_id: str, required_scope: str) -> bool:
        start_time = time.perf_counter()
        try:
            api_key = self._keys.get(key_id)
            if not api_key:
                return False
            return required_scope in api_key.scopes
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"API key scope checked in {latency:.4f}s")

    async def audit_usage(self, key_id: str, endpoint: str, tenant_id: str) -> None:
        start_time = time.perf_counter()
        try:
            log.info(f"Audit: API Key {key_id} used for {endpoint} by tenant {tenant_id}")
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"API key usage audited in {latency:.4f}s")

_service_instance = None
def get_service() -> APIKeyManager:
    global _service_instance
    if _service_instance is None:
        _service_instance = APIKeyManager()
    return _service_instance

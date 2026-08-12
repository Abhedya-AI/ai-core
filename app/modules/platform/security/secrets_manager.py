from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from app.core.logging import get_logger

log = get_logger(__name__)

class SecretsManager:
    def __init__(self, provider: str = "env") -> None:
        self.provider = provider
        self._cache: dict[str, tuple[str, float]] = {}
        self._cache_ttl: float = 300.0
        self._access_log: list[dict] = []
        self._overrides: dict[str, str] = {}

    async def get_secret(self, key: str, caller: str = "unknown") -> str | None:
        start_time = time.perf_counter()
        try:
            now = time.time()
            from_cache = False
            value = None

            if key in self._cache and (now - self._cache[key][1]) < self._cache_ttl:
                value = self._cache[key][0]
                from_cache = True
            else:
                if key in self._overrides:
                    value = self._overrides[key]
                elif self.provider == "env":
                    value = os.environ.get(key)
                elif self.provider == "vault":
                    log.warning("Vault provider not fully implemented, falling back to env")
                    value = os.environ.get(key)
                elif self.provider == "aws":
                    log.warning("AWS provider not fully implemented, falling back to env")
                    value = os.environ.get(key)

                if value is not None:
                    self._cache[key] = (value, now)

            await self.audit_access(key, caller)
            return value
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_secret executed for key={key} in {latency:.4f}s")

    async def set_secret(self, key: str, value: str, caller: str = "unknown") -> bool:
        start_time = time.perf_counter()
        try:
            if self.provider == "env":
                self._overrides[key] = value
                log.info(f"Secret set via env override by {caller}")
                return True
            return False
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"set_secret executed for key={key} in {latency:.4f}s")

    async def rotate_secret(self, key: str, new_value: str, caller: str = "unknown") -> bool:
        start_time = time.perf_counter()
        try:
            if key in self._cache:
                del self._cache[key]
            
            success = await self.set_secret(key, new_value, caller)
            if success:
                masked_value = new_value[:3] + "***" if len(new_value) >= 3 else "***"
                log.info(f"Secret {key} rotated. New value mask: {masked_value}")
            return success
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"rotate_secret executed for key={key} in {latency:.4f}s")

    async def list_secret_keys(self, prefix: str = "") -> list[str]:
        start_time = time.perf_counter()
        try:
            return [k for k in self._overrides.keys() if k.startswith(prefix)]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"list_secret_keys executed in {latency:.4f}s")

    async def audit_access(self, key: str, caller: str) -> None:
        start_time = time.perf_counter()
        try:
            self._access_log.append({
                "key": key,
                "caller": caller,
                "accessed_at": datetime.now(timezone.utc).isoformat(),
                "from_cache": key in self._cache
            })
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"audit_access executed in {latency:.4f}s")

    async def get_audit_log(self, key: str | None = None, limit: int = 100) -> list[dict]:
        start_time = time.perf_counter()
        try:
            logs = self._access_log
            if key:
                logs = [log for log in logs if log["key"] == key]
            return logs[-limit:]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_audit_log executed in {latency:.4f}s")

_service_instance = None
def get_service() -> SecretsManager:
    global _service_instance
    if _service_instance is None:
        _service_instance = SecretsManager()
    return _service_instance

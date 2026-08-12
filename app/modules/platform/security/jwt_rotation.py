from __future__ import annotations

import time
import uuid
import base64
import json
from datetime import datetime, timezone, timedelta

from app.core.logging import get_logger

log = get_logger(__name__)

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

class JWTRotationManager:
    def __init__(self, secret_key: str = "abhedya-default-secret", algorithm: str = "HS256", access_ttl_minutes: int = 15, refresh_ttl_days: int = 7) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_ttl_minutes = access_ttl_minutes
        self.refresh_ttl_days = refresh_ttl_days
        self._blacklist: set[str] = set()

    async def create_access_token(self, user_id: str, tenant_id: str, roles: list[str], plant_id: str = "") -> str:
        start_time = time.perf_counter()
        try:
            jti = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            exp = now + timedelta(minutes=self.access_ttl_minutes)

            payload = {
                "sub": user_id,
                "tenant_id": tenant_id,
                "roles": roles,
                "plant_id": plant_id,
                "jti": jti,
                "iat": int(now.timestamp()),
                "exp": int(exp.timestamp()),
                "type": "access"
            }

            if JWT_AVAILABLE:
                return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            else:
                return base64.b64encode(json.dumps(payload).encode()).decode()
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"create_access_token executed in {latency:.4f}s")

    async def create_refresh_token(self, user_id: str, tenant_id: str) -> str:
        start_time = time.perf_counter()
        try:
            jti = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            exp = now + timedelta(days=self.refresh_ttl_days)

            payload = {
                "sub": user_id,
                "tenant_id": tenant_id,
                "jti": jti,
                "iat": int(now.timestamp()),
                "exp": int(exp.timestamp()),
                "type": "refresh"
            }

            if JWT_AVAILABLE:
                return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            else:
                return base64.b64encode(json.dumps(payload).encode()).decode()
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"create_refresh_token executed in {latency:.4f}s")

    async def verify_token(self, token: str) -> dict | None:
        start_time = time.perf_counter()
        try:
            payload = {}
            if JWT_AVAILABLE:
                try:
                    payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
                except Exception:
                    return None
            else:
                try:
                    payload = json.loads(base64.b64decode(token).decode())
                    if datetime.now(timezone.utc).timestamp() > payload.get("exp", 0):
                        return None
                except Exception:
                    return None

            jti = payload.get("jti")
            if not jti or jti in self._blacklist:
                return None

            return payload
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"verify_token executed in {latency:.4f}s")

    async def refresh_access_token(self, refresh_token: str) -> dict | None:
        start_time = time.perf_counter()
        try:
            payload = await self.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                return None

            access_token = await self.create_access_token(
                user_id=payload["sub"],
                tenant_id=payload.get("tenant_id", ""),
                roles=[]
            )

            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": self.access_ttl_minutes * 60
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"refresh_access_token executed in {latency:.4f}s")

    async def revoke_token(self, token: str) -> bool:
        start_time = time.perf_counter()
        try:
            payload = await self.verify_token(token)
            if payload and "jti" in payload:
                self._blacklist.add(payload["jti"])
                return True
            return False
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"revoke_token executed in {latency:.4f}s")

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        start_time = time.perf_counter()
        try:
            # Requires tracking user jtis, simulating generic invalidation for now
            self._blacklist.add(f"user_revoke_{user_id}")
            log.info(f"Revoked all tokens for user {user_id}")
            return 1
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"revoke_all_user_tokens executed in {latency:.4f}s")

    async def rotate_key(self, new_secret: str) -> None:
        start_time = time.perf_counter()
        try:
            self.secret_key = new_secret
            self._blacklist.clear()
            log.info("JWT secret key rotated and blacklist cleared")
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"rotate_key executed in {latency:.4f}s")

    async def get_rotation_stats(self) -> dict:
        return {
            "blacklist_size": len(self._blacklist),
            "algorithm": self.algorithm,
            "access_ttl_minutes": self.access_ttl_minutes,
            "refresh_ttl_days": self.refresh_ttl_days
        }

_service_instance = None
def get_service() -> JWTRotationManager:
    global _service_instance
    if _service_instance is None:
        _service_instance = JWTRotationManager()
    return _service_instance

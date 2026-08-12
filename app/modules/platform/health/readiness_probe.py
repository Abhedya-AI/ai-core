from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)


class ReadinessProbe:
    async def check_database(self) -> bool:
        try:
            from app.infrastructure.postgres.health import check_postgres_health
            await check_postgres_health()
            return True
        except Exception:
            return False

    async def check_redis(self) -> bool:
        try:
            from app.infrastructure.redis.health import check_redis_health
            await check_redis_health()
            return True
        except Exception:
            return False

    async def check_kafka(self) -> bool:
        try:
            from app.infrastructure.kafka.health import check_kafka_health
            await check_kafka_health()
            return True
        except Exception:
            return False

    async def check_models_loaded(self) -> bool:
        return True

    async def is_ready(self) -> dict:
        checks = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "kafka": await self.check_kafka(),
            "models_loaded": await self.check_models_loaded()
        }
        
        failed_checks = [k for k, v in checks.items() if not v]
        ready = len(failed_checks) == 0
        
        return {
            "ready": ready,
            "checks": checks,
            "failed_checks": failed_checks,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

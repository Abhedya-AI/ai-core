from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)


class LivenessProbe:
    def __init__(self):
        self._start_time: float = time.time()
        self._request_count: int = 0
        self._last_request_at: float = time.time()

    async def is_alive(self) -> dict:
        try:
            import psutil
            proc = psutil.Process()
            memory_mb = proc.memory_info().rss / 1024 / 1024
            cpu_pct = proc.cpu_percent(interval=0.1)
        except ImportError:
            memory_mb = 0.0
            cpu_pct = 0.0
            
        uptime_seconds = time.time() - self._start_time
        last_request_age_seconds = time.time() - self._last_request_at
        
        memory_ok = await self.check_memory(memory_mb)
        responsiveness_ok = await self.check_responsiveness(last_request_age_seconds)
        
        alive = uptime_seconds > 0 and memory_ok and responsiveness_ok
        
        return {
            "alive": alive,
            "uptime_seconds": uptime_seconds,
            "memory_mb": memory_mb,
            "cpu_pct": cpu_pct,
            "last_request_age_seconds": last_request_age_seconds,
            "checks": {
                "memory_ok": memory_ok,
                "responsiveness_ok": responsiveness_ok
            }
        }

    async def tick(self) -> None:
        self._request_count += 1
        self._last_request_at = time.time()

    async def check_memory(self, memory_mb: float = 0.0) -> bool:
        if memory_mb == 0.0:
            try:
                import psutil
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            except ImportError:
                return True
        return memory_mb < 4096.0

    async def check_responsiveness(self, last_request_age_seconds: float = -1.0) -> bool:
        if last_request_age_seconds < 0:
            last_request_age_seconds = time.time() - self._last_request_at
        return last_request_age_seconds < 300 or self._request_count == 0

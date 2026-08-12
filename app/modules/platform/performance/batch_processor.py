from __future__ import annotations

import asyncio
import time
from typing import Any, Callable

from app.core.logging import get_logger
log = get_logger(__name__)


class AsyncBatchProcessor:
    def __init__(self, batch_size: int = 100, flush_interval_seconds: float = 5.0, processor_name: str = "default"):
        self.batch_size = batch_size
        self.flush_interval_seconds = flush_interval_seconds
        self.processor_name = processor_name
        
        self._queue: list[dict] = []
        self._processed_count: int = 0
        self._failed_count: int = 0
        self._last_flush_time = time.perf_counter()

    def _should_flush(self) -> bool:
        return len(self._queue) >= self.batch_size

    async def add(self, item: dict) -> None:
        self._queue.append(item)
        if self._should_flush():
            await self.flush()

    async def add_batch(self, items: list[dict]) -> None:
        self._queue.extend(items)
        while self._should_flush():
            await self.flush()

    async def flush(self, processor_fn: Callable | None = None) -> dict:
        start_time = time.perf_counter()
        
        batch = self._queue[:self.batch_size]
        self._queue = self._queue[self.batch_size:]
        
        batch_size_actual = len(batch)
        if batch_size_actual == 0:
            return {
                "processed": 0,
                "failed": 0,
                "batch_size": 0,
                "flush_duration_ms": 0.0
            }
            
        processed = 0
        failed = 0
        
        if processor_fn:
            try:
                await processor_fn(batch)
                processed = batch_size_actual
            except Exception as e:
                log.error(f"Batch processing failed in {self.processor_name}: {e}")
                failed = batch_size_actual
        else:
            # Default action if no processor provided
            processed = batch_size_actual
            
        self._processed_count += processed
        self._failed_count += failed
        self._last_flush_time = time.perf_counter()
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        return {
            "processed": processed,
            "failed": failed,
            "batch_size": batch_size_actual,
            "flush_duration_ms": duration_ms
        }

    async def get_stats(self) -> dict:
        return {
            "queue_size": len(self._queue),
            "processed_count": self._processed_count,
            "failed_count": self._failed_count,
            "batch_size": self.batch_size,
            "flush_interval": self.flush_interval_seconds
        }

    async def reset(self) -> None:
        self._queue.clear()
        self._processed_count = 0
        self._failed_count = 0
        self._last_flush_time = time.perf_counter()

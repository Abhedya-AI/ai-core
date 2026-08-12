from __future__ import annotations

import asyncio
import uuid
import time
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)


class BackgroundWorkerPool:
    def __init__(self, max_workers: int = 10, name: str = "platform-workers"):
        self.max_workers = max_workers
        self.name = name
        self._tasks: dict[str, asyncio.Task] = {}
        self._task_results: dict[str, dict] = {}
        self._task_count: int = 0
        self._semaphore = asyncio.Semaphore(max_workers)

    async def _worker_wrapper(self, task_id: str, coro: Any) -> None:
        start_time = time.perf_counter()
        try:
            res = await coro
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._task_results[task_id] = {
                "task_id": task_id,
                "status": "completed",
                "result": res,
                "error": None,
                "duration_ms": duration_ms
            }
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._task_results[task_id] = {
                "task_id": task_id,
                "status": "failed",
                "result": None,
                "error": str(e),
                "duration_ms": duration_ms
            }
        finally:
            self._tasks.pop(task_id, None)

    async def submit(self, coro: Any, name: str = "", priority: int = 0) -> str:
        await self._semaphore.acquire()
        
        async def sem_wrapper():
            try:
                await self._worker_wrapper(task_id, coro)
            finally:
                self._semaphore.release()
                
        task_id = str(uuid.uuid4())
        task = asyncio.create_task(sem_wrapper())
        self._tasks[task_id] = task
        self._task_count += 1
        return task_id

    async def get_result(self, task_id: str, timeout_seconds: float = 30.0) -> dict:
        start_wait = time.perf_counter()
        while task_id in self._tasks:
            if (time.perf_counter() - start_wait) > timeout_seconds:
                return {
                    "task_id": task_id,
                    "status": "timeout",
                    "result": None,
                    "error": "Timeout waiting for task",
                    "duration_ms": (time.perf_counter() - start_wait) * 1000
                }
            await asyncio.sleep(0.1)
            
        return self._task_results.get(task_id, {
            "task_id": task_id,
            "status": "not_found",
            "result": None,
            "error": "Task not found",
            "duration_ms": 0.0
        })

    async def cancel(self, task_id: str) -> bool:
        if task_id in self._tasks:
            self._tasks[task_id].cancel()
            return True
        return False

    async def wait_all(self, timeout_seconds: float = 60.0) -> dict:
        tasks_to_wait = list(self._tasks.values())
        if not tasks_to_wait:
            return {"completed": 0, "failed": 0, "timed_out": 0}
            
        done, pending = await asyncio.wait(tasks_to_wait, timeout=timeout_seconds)
        
        for p in pending:
            p.cancel()
            
        # Simplified stats
        return {
            "completed": len(done),
            "failed": 0,  # Could analyze results
            "timed_out": len(pending)
        }

    async def get_stats(self) -> dict:
        return {
            "active_tasks": len(self._tasks),
            "completed_tasks": sum(1 for r in self._task_results.values() if r["status"] == "completed"),
            "failed_tasks": sum(1 for r in self._task_results.values() if r["status"] == "failed"),
            "max_workers": self.max_workers,
            "worker_name": self.name
        }

    async def shutdown(self, timeout_seconds: float = 30.0) -> None:
        await self.wait_all(timeout_seconds)
        for t in self._tasks.values():
            if not t.done():
                t.cancel()

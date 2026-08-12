from __future__ import annotations

from typing import Protocol, Any
from app.core.logging import get_logger

log = get_logger(__name__)

class IHazardRepository(Protocol):
    async def get(self, id: str) -> dict | None: ...
    async def save(self, data: dict) -> None: ...
    async def list_active(self) -> list[dict]: ...
    async def get_history(self, id: str) -> list[dict]: ...

class InMemoryHazardRepository(IHazardRepository):
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}
        self._history: dict[str, list[dict]] = {}

    async def get(self, id: str) -> dict | None:
        return self._store.get(id)

    async def save(self, data: dict) -> None:
        pid = data.get("id") or data.get("propagation_id")
        if not pid:
            return
        self._store[pid] = data
        if pid not in self._history:
            self._history[pid] = []
        self._history[pid].append(dict(data))

    async def list_active(self) -> list[dict]:
        return [d for d in self._store.values() if d.get("status") not in ("CONTAINED", "RESOLVED")]

    async def get_history(self, id: str) -> list[dict]:
        return self._history.get(id, [])

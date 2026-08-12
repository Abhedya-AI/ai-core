from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable, Any
from datetime import datetime, timezone

log = logging.getLogger(__name__)

@runtime_checkable
class IForecastRepository(Protocol):
    async def save_forecast(self, forecast_id: str, entity_id: str, forecast_type: str, data: dict[str, Any]) -> None: ...
    async def get_forecast(self, forecast_id: str) -> dict[str, Any] | None: ...
    async def get_latest_forecast(self, entity_id: str, forecast_type: str) -> dict[str, Any] | None: ...
    async def list_forecasts(self, entity_id: str | None, forecast_type: str | None, limit: int, offset: int) -> list[dict[str, Any]]: ...
    async def save_scenario(self, scenario_id: str, entity_id: str, data: dict[str, Any]) -> None: ...
    async def get_scenario(self, scenario_id: str) -> dict[str, Any] | None: ...
    async def list_scenarios(self, entity_id: str, limit: int) -> list[dict[str, Any]]: ...
    async def count_forecasts(self, entity_id: str | None, forecast_type: str | None) -> int: ...
    async def delete_stale_forecasts(self, older_than_hours: int) -> int: ...

class InMemoryForecastRepository:
    """In-memory implementation for development and testing."""
    def __init__(self):
        self._forecasts: dict[str, dict] = {}
        self._scenarios: dict[str, dict] = {}
        self._latest: dict[str, dict] = {}  # entity_id:forecast_type -> data

    async def save_forecast(self, forecast_id: str, entity_id: str, forecast_type: str, data: dict[str, Any]) -> None:
        self._forecasts[forecast_id] = data
        self._latest[f"{entity_id}:{forecast_type}"] = data

    async def get_forecast(self, forecast_id: str) -> dict[str, Any] | None:
        return self._forecasts.get(forecast_id)

    async def get_latest_forecast(self, entity_id: str, forecast_type: str) -> dict[str, Any] | None:
        return self._latest.get(f"{entity_id}:{forecast_type}")

    async def list_forecasts(self, entity_id: str | None, forecast_type: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        results = list(self._forecasts.values())
        if entity_id:
            results = [r for r in results if r.get("entity_id") == entity_id]
        if forecast_type:
            results = [r for r in results if r.get("forecast_type") == forecast_type]
        # Sort by generated_at descending (assuming generated_at exists)
        results.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        return results[offset:offset + limit]

    async def save_scenario(self, scenario_id: str, entity_id: str, data: dict[str, Any]) -> None:
        self._scenarios[scenario_id] = data

    async def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        return self._scenarios.get(scenario_id)

    async def list_scenarios(self, entity_id: str, limit: int) -> list[dict[str, Any]]:
        results = [s for s in self._scenarios.values() if s.get("entity_id") == entity_id]
        results.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        return results[:limit]

    async def count_forecasts(self, entity_id: str | None, forecast_type: str | None) -> int:
        results = list(self._forecasts.values())
        if entity_id:
            results = [r for r in results if r.get("entity_id") == entity_id]
        if forecast_type:
            results = [r for r in results if r.get("forecast_type") == forecast_type]
        return len(results)

    async def delete_stale_forecasts(self, older_than_hours: int) -> int:
        now = datetime.now(timezone.utc)
        to_delete = []
        for fid, data in self._forecasts.items():
            gen_at_str = data.get("generated_at")
            if gen_at_str:
                try:
                    gen_at = datetime.fromisoformat(gen_at_str.replace("Z", "+00:00"))
                    diff = (now - gen_at).total_seconds() / 3600
                    if diff > older_than_hours:
                        to_delete.append(fid)
                except ValueError:
                    pass
        for fid in to_delete:
            del self._forecasts[fid]
        return len(to_delete)

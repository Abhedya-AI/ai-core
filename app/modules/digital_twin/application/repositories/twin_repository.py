from __future__ import annotations
from typing import Protocol, Any, runtime_checkable

@runtime_checkable
class ITwinRepository(Protocol):
    async def save_twin(self, twin_id: str, data: dict[str, Any]) -> None: ...
    async def get_twin(self, twin_id: str) -> dict[str, Any] | None: ...
    async def save_state(self, entity_id: str, entity_type: str, data: dict[str, Any]) -> None: ...
    async def get_state(self, entity_id: str) -> dict[str, Any] | None: ...
    async def save_simulation(self, simulation_id: str, twin_id: str, data: dict[str, Any]) -> None: ...
    async def get_simulation(self, simulation_id: str) -> dict[str, Any] | None: ...
    async def list_simulations(self, twin_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]: ...
    async def save_scenario(self, scenario_id: str, twin_id: str, data: dict[str, Any]) -> None: ...
    async def get_scenario(self, scenario_id: str) -> dict[str, Any] | None: ...
    async def list_scenarios(self, twin_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]: ...
    async def save_optimization(self, optimization_id: str, twin_id: str, data: dict[str, Any]) -> None: ...
    async def get_optimization(self, optimization_id: str) -> dict[str, Any] | None: ...
    async def list_optimizations(self, twin_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]: ...
    async def save_replay(self, replay_id: str, twin_id: str, data: dict[str, Any]) -> None: ...
    async def get_replay(self, replay_id: str) -> dict[str, Any] | None: ...
    async def save_plan(self, plan_id: str, twin_id: str, plan_type: str, data: dict[str, Any]) -> None: ...
    async def get_plan(self, plan_id: str) -> dict[str, Any] | None: ...
    async def list_plans(self, twin_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]: ...
    async def save_event(self, event_id: str, twin_id: str, data: dict[str, Any]) -> None: ...
    async def list_events(self, twin_id: str, limit: int, offset: int) -> list[dict[str, Any]]: ...
    async def count_records(self, record_type: str, twin_id: str | None) -> int: ...
    async def delete_old_records(self, record_type: str, older_than_hours: int) -> int: ...

class InMemoryTwinRepository:
    def __init__(self):
        self._twins: dict[str, dict[str, Any]] = {}
        self._states: dict[str, dict[str, Any]] = {}
        self._simulations: dict[str, dict[str, Any]] = {}
        self._scenarios: dict[str, dict[str, Any]] = {}
        self._optimizations: dict[str, dict[str, Any]] = {}
        self._replays: dict[str, dict[str, Any]] = {}
        self._plans: dict[str, dict[str, Any]] = {}
        self._events: dict[str, dict[str, Any]] = {}

    async def save_twin(self, twin_id: str, data: dict[str, Any]) -> None:
        self._twins[twin_id] = data

    async def get_twin(self, twin_id: str) -> dict[str, Any] | None:
        return self._twins.get(twin_id)

    async def save_state(self, entity_id: str, entity_type: str, data: dict[str, Any]) -> None:
        self._states[entity_id] = data

    async def get_state(self, entity_id: str) -> dict[str, Any] | None:
        return self._states.get(entity_id)

    async def save_simulation(self, simulation_id: str, twin_id: str, data: dict[str, Any]) -> None:
        self._simulations[simulation_id] = data

    async def get_simulation(self, simulation_id: str) -> dict[str, Any] | None:
        return self._simulations.get(simulation_id)

    async def list_simulations(self, twin_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        sims = list(self._simulations.values())
        if twin_id:
            sims = [s for s in sims if s.get("twin_id") == twin_id]
        return sims[offset:offset+limit]

    async def save_scenario(self, scenario_id: str, twin_id: str, data: dict[str, Any]) -> None:
        self._scenarios[scenario_id] = data

    async def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        return self._scenarios.get(scenario_id)

    async def list_scenarios(self, twin_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        scens = list(self._scenarios.values())
        if twin_id:
            scens = [s for s in scens if s.get("twin_id") == twin_id]
        return scens[offset:offset+limit]

    async def save_optimization(self, optimization_id: str, twin_id: str, data: dict[str, Any]) -> None:
        self._optimizations[optimization_id] = data

    async def get_optimization(self, optimization_id: str) -> dict[str, Any] | None:
        return self._optimizations.get(optimization_id)

    async def list_optimizations(self, twin_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        opts = list(self._optimizations.values())
        if twin_id:
            opts = [o for o in opts if o.get("twin_id") == twin_id]
        return opts[offset:offset+limit]

    async def save_replay(self, replay_id: str, twin_id: str, data: dict[str, Any]) -> None:
        self._replays[replay_id] = data

    async def get_replay(self, replay_id: str) -> dict[str, Any] | None:
        return self._replays.get(replay_id)

    async def save_plan(self, plan_id: str, twin_id: str, plan_type: str, data: dict[str, Any]) -> None:
        self._plans[plan_id] = data

    async def get_plan(self, plan_id: str) -> dict[str, Any] | None:
        return self._plans.get(plan_id)

    async def list_plans(self, twin_id: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        plns = list(self._plans.values())
        if twin_id:
            plns = [p for p in plns if p.get("twin_id") == twin_id]
        return plns[offset:offset+limit]

    async def save_event(self, event_id: str, twin_id: str, data: dict[str, Any]) -> None:
        self._events[event_id] = data

    async def list_events(self, twin_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        evts = [e for e in self._events.values() if e.get("twin_id") == twin_id]
        return evts[offset:offset+limit]

    async def count_records(self, record_type: str, twin_id: str | None) -> int:
        records = getattr(self, f"_{record_type}s", {})
        if twin_id:
            return len([r for r in records.values() if r.get("twin_id") == twin_id])
        return len(records)

    async def delete_old_records(self, record_type: str, older_than_hours: int) -> int:
        return 0 # Mock implementation for in-memory

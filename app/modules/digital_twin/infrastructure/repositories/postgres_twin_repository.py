from __future__ import annotations

import json
from typing import Any, List, Optional
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Integer, select
from sqlalchemy.orm import declarative_base

from app.core.logging import get_logger

log = get_logger(__name__)
Base = declarative_base()

try:
    from app.infrastructure.database.session import async_session
except ImportError:
    async_session = None


class TwinRecord(Base):
    __tablename__ = "digital_twin_records"
    id = Column(String, primary_key=True)
    plant_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TwinStateRecord(Base):
    __tablename__ = "digital_twin_states"
    id = Column(String, primary_key=True)
    entity_id = Column(String, nullable=False, index=True)
    twin_id = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    version = Column(Integer, default=1)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TwinSnapshotRecord(Base):
    __tablename__ = "digital_twin_snapshots"
    snapshot_id = Column(String, primary_key=True)
    twin_id = Column(String, nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TwinSimulationRecord(Base):
    __tablename__ = "digital_twin_simulations"
    simulation_id = Column(String, primary_key=True)
    twin_id = Column(String, nullable=False, index=True)
    simulation_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TwinOptimizationRecord(Base):
    __tablename__ = "digital_twin_optimizations"
    optimization_id = Column(String, primary_key=True)
    twin_id = Column(String, nullable=False, index=True)
    target = Column(String, nullable=False)
    status = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TwinPlanRecord(Base):
    __tablename__ = "digital_twin_plans"
    plan_id = Column(String, primary_key=True)
    twin_id = Column(String, nullable=False, index=True)
    plan_type = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PostgresTwinRepository:
    def __init__(self):
        self._session_maker = async_session
        self._fallback: dict[str, Any] = {}

    async def save_twin(self, twin_id: str, data: dict[str, Any]) -> None:
        if not self._session_maker:
            self._fallback[f"twin:{twin_id}"] = data
            return
        async with self._session_maker() as session:
            record = await session.get(TwinRecord, twin_id)
            if not record:
                record = TwinRecord(id=twin_id, plant_id=data.get("plant_id", ""))
                session.add(record)
            record.status = data.get("status", "UNKNOWN")
            record.version = data.get("version", 1)
            record.data_json = json.dumps(data)
            await session.commit()

    async def get_twin(self, twin_id: str) -> Optional[dict[str, Any]]:
        if not self._session_maker:
            return self._fallback.get(f"twin:{twin_id}")
        async with self._session_maker() as session:
            record = await session.get(TwinRecord, twin_id)
            return json.loads(record.data_json) if record else None

    async def save_state(self, state_id: str, data: dict[str, Any]) -> None:
        if not self._session_maker:
            self._fallback[f"state:{state_id}"] = data
            return
        async with self._session_maker() as session:
            record = await session.get(TwinStateRecord, state_id)
            if not record:
                record = TwinStateRecord(id=state_id, entity_id=data.get("entity_id", ""), twin_id=data.get("twin_id", ""), entity_type=data.get("entity_type", ""))
                session.add(record)
            record.data_json = json.dumps(data)
            await session.commit()

    async def get_state(self, state_id: str) -> Optional[dict[str, Any]]:
        if not self._session_maker:
            return self._fallback.get(f"state:{state_id}")
        async with self._session_maker() as session:
            record = await session.get(TwinStateRecord, state_id)
            return json.loads(record.data_json) if record else None

    async def save_simulation(self, data: dict[str, Any]) -> None:
        sim_id = data.get("simulation_id")
        if not self._session_maker:
            self._fallback[f"sim:{sim_id}"] = data
            return
        async with self._session_maker() as session:
            record = await session.get(TwinSimulationRecord, sim_id)
            if not record:
                record = TwinSimulationRecord(
                    simulation_id=sim_id, twin_id=data.get("twin_id", ""), 
                    simulation_type=data.get("simulation_type", ""), status=data.get("status", "UNKNOWN")
                )
                session.add(record)
            record.data_json = json.dumps(data)
            await session.commit()

    async def get_simulation(self, simulation_id: str) -> Optional[dict[str, Any]]:
        if not self._session_maker:
            return self._fallback.get(f"sim:{simulation_id}")
        async with self._session_maker() as session:
            record = await session.get(TwinSimulationRecord, simulation_id)
            return json.loads(record.data_json) if record else None

    async def list_simulations(self, twin_id: str, limit: int, offset: int) -> List[dict[str, Any]]:
        if not self._session_maker:
            return [v for k, v in self._fallback.items() if k.startswith("sim:") and v.get("twin_id") == twin_id][offset:offset+limit]
        async with self._session_maker() as session:
            stmt = select(TwinSimulationRecord).where(TwinSimulationRecord.twin_id == twin_id).offset(offset).limit(limit)
            result = await session.execute(stmt)
            return [json.loads(r.data_json) for r in result.scalars()]

    async def save_optimization(self, data: dict[str, Any]) -> None:
        opt_id = data.get("optimization_id")
        if not self._session_maker:
            self._fallback[f"opt:{opt_id}"] = data
            return
        async with self._session_maker() as session:
            record = await session.get(TwinOptimizationRecord, opt_id)
            if not record:
                record = TwinOptimizationRecord(
                    optimization_id=opt_id, twin_id=data.get("twin_id", ""), 
                    target=data.get("target", ""), status=data.get("status", "UNKNOWN")
                )
                session.add(record)
            record.data_json = json.dumps(data)
            await session.commit()

    async def get_optimization(self, optimization_id: str) -> Optional[dict[str, Any]]:
        if not self._session_maker:
            return self._fallback.get(f"opt:{optimization_id}")
        async with self._session_maker() as session:
            record = await session.get(TwinOptimizationRecord, optimization_id)
            return json.loads(record.data_json) if record else None

    async def list_optimizations(self, twin_id: str, limit: int, offset: int) -> List[dict[str, Any]]:
        if not self._session_maker:
            return [v for k, v in self._fallback.items() if k.startswith("opt:") and v.get("twin_id") == twin_id][offset:offset+limit]
        async with self._session_maker() as session:
            stmt = select(TwinOptimizationRecord).where(TwinOptimizationRecord.twin_id == twin_id).offset(offset).limit(limit)
            result = await session.execute(stmt)
            return [json.loads(r.data_json) for r in result.scalars()]

    async def save_snapshot(self, data: dict[str, Any]) -> None:
        snap_id = data.get("snapshot_id")
        if not self._session_maker:
            self._fallback[f"snap:{snap_id}"] = data
            return
        async with self._session_maker() as session:
            record = await session.get(TwinSnapshotRecord, snap_id)
            if not record:
                record = TwinSnapshotRecord(
                    snapshot_id=snap_id, twin_id=data.get("twin_id", ""), version_number=data.get("version", 1)
                )
                session.add(record)
            record.data_json = json.dumps(data)
            await session.commit()

    async def get_snapshot(self, snapshot_id: str) -> Optional[dict[str, Any]]:
        if not self._session_maker:
            return self._fallback.get(f"snap:{snapshot_id}")
        async with self._session_maker() as session:
            record = await session.get(TwinSnapshotRecord, snapshot_id)
            return json.loads(record.data_json) if record else None

    async def list_snapshots(self, twin_id: str, limit: int, offset: int) -> List[dict[str, Any]]:
        if not self._session_maker:
            return [v for k, v in self._fallback.items() if k.startswith("snap:") and v.get("twin_id") == twin_id][offset:offset+limit]
        async with self._session_maker() as session:
            stmt = select(TwinSnapshotRecord).where(TwinSnapshotRecord.twin_id == twin_id).offset(offset).limit(limit)
            result = await session.execute(stmt)
            return [json.loads(r.data_json) for r in result.scalars()]

    async def save_plan(self, data: dict[str, Any]) -> None:
        plan_id = data.get("plan_id")
        if not self._session_maker:
            self._fallback[f"plan:{plan_id}"] = data
            return
        async with self._session_maker() as session:
            record = await session.get(TwinPlanRecord, plan_id)
            if not record:
                record = TwinPlanRecord(
                    plan_id=plan_id, twin_id=data.get("twin_id", ""), plan_type=data.get("type", "")
                )
                session.add(record)
            record.data_json = json.dumps(data)
            await session.commit()

    async def get_plan(self, plan_id: str) -> Optional[dict[str, Any]]:
        if not self._session_maker:
            return self._fallback.get(f"plan:{plan_id}")
        async with self._session_maker() as session:
            record = await session.get(TwinPlanRecord, plan_id)
            return json.loads(record.data_json) if record else None

    async def list_plans(self, twin_id: str, limit: int, offset: int) -> List[dict[str, Any]]:
        if not self._session_maker:
            return [v for k, v in self._fallback.items() if k.startswith("plan:") and v.get("twin_id") == twin_id][offset:offset+limit]
        async with self._session_maker() as session:
            stmt = select(TwinPlanRecord).where(TwinPlanRecord.twin_id == twin_id).offset(offset).limit(limit)
            result = await session.execute(stmt)
            return [json.loads(r.data_json) for r in result.scalars()]

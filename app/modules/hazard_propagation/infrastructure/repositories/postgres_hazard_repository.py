from __future__ import annotations
import json
from typing import Any
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from app.core.logging import get_logger

log = get_logger(__name__)

Base = declarative_base()

class HazardPropagationRecord(Base):
    __tablename__ = "hazard_propagation_records"
    id = Column(String, primary_key=True)
    propagation_id = Column(String, nullable=False, index=True)
    hazard_type = Column(String, nullable=False)
    state = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime)

class ExposureRecord(Base):
    __tablename__ = "hazard_exposure_records"
    id = Column(String, primary_key=True)
    assessment_id = Column(String, nullable=False, index=True)
    propagation_id = Column(String, nullable=False, index=True)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime)

class ContainmentPlanRecord(Base):
    __tablename__ = "hazard_containment_plans"
    id = Column(String, primary_key=True)
    plan_id = Column(String, nullable=False, index=True)
    propagation_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime)

class EvacuationRecord(Base):
    __tablename__ = "hazard_evacuation_records"
    id = Column(String, primary_key=True)
    recommendation_id = Column(String, nullable=False, index=True)
    propagation_id = Column(String, nullable=False, index=True)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime)

class SimulationRecord(Base):
    __tablename__ = "hazard_simulation_records"
    id = Column(String, primary_key=True)
    simulation_id = Column(String, nullable=False, index=True)
    scenario_name = Column(String)
    status = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime)

class CascadeRecord(Base):
    __tablename__ = "hazard_cascade_records"
    id = Column(String, primary_key=True)
    cascade_id = Column(String, nullable=False, index=True)
    propagation_id = Column(String, nullable=False, index=True)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime)


class PostgresHazardRepository:
    def __init__(self) -> None:
        self._session_maker = None
        self._fallback = {}
        try:
            from app.infrastructure.database.session import async_session
            self._session_maker = async_session
        except ImportError:
            log.warning("Database session not available, using in-memory fallback")

    async def save_propagation(self, propagation_id: str, data: dict[str, Any]) -> None:
        if self._session_maker:
            try:
                async with self._session_maker() as session:
                    record = HazardPropagationRecord(
                        id=propagation_id,
                        propagation_id=propagation_id,
                        hazard_type=data.get("hazard_type", ""),
                        state=data.get("state", ""),
                        severity=data.get("severity", ""),
                        data_json=json.dumps(data),
                        created_at=datetime.utcnow()
                    )
                    session.add(record)
                    await session.commit()
                return
            except Exception as e:
                log.warning(f"Failed to save to db: {e}")
        self._fallback[f"prop_{propagation_id}"] = data

    async def get_propagation(self, propagation_id: str) -> dict[str, Any] | None:
        if self._session_maker:
            try:
                from sqlalchemy import select
                async with self._session_maker() as session:
                    result = await session.execute(select(HazardPropagationRecord).filter_by(propagation_id=propagation_id))
                    record = result.scalars().first()
                    if record:
                        return json.loads(record.data_json)
            except Exception as e:
                log.warning(f"Failed to get from db: {e}")
        return self._fallback.get(f"prop_{propagation_id}")

    async def list_propagations(self, hazard_type: str | None = None, state: str | None = None, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    async def save_exposure(self, assessment_id: str, data: dict[str, Any]) -> None:
        self._fallback[f"exp_{assessment_id}"] = data

    async def save_containment(self, plan_id: str, data: dict[str, Any]) -> None:
        self._fallback[f"cont_{plan_id}"] = data

    async def save_evacuation(self, recommendation_id: str, data: dict[str, Any]) -> None:
        self._fallback[f"evac_{recommendation_id}"] = data

    async def save_cascade(self, cascade_id: str, data: dict[str, Any]) -> None:
        self._fallback[f"casc_{cascade_id}"] = data

    async def save_simulation(self, simulation_id: str, data: dict[str, Any]) -> None:
        self._fallback[f"sim_{simulation_id}"] = data

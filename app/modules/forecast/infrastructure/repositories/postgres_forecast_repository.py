from __future__ import annotations

import logging
import json
from typing import Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, Float, Text, select, delete
from sqlalchemy.orm import DeclarativeBase

log = logging.getLogger(__name__)

from app.modules.forecast.application.repositories.forecast_repository import IForecastRepository, InMemoryForecastRepository

class ForecastBase(DeclarativeBase):
    pass

class ForecastRecord(ForecastBase):
    __tablename__ = "forecast_records"
    forecast_id = Column(String, primary_key=True)
    entity_id = Column(String, nullable=False, index=True)
    forecast_type = Column(String, nullable=False, index=True)
    horizon = Column(String, nullable=True)
    data_json = Column(Text, nullable=False)
    generated_at = Column(String, nullable=False)
    valid_until = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="COMPLETED")

class ScenarioRecord(ForecastBase):
    __tablename__ = "forecast_scenarios"
    scenario_id = Column(String, primary_key=True)
    entity_id = Column(String, nullable=False, index=True)
    forecast_type = Column(String, nullable=True)
    data_json = Column(Text, nullable=False)
    generated_at = Column(String, nullable=False)

class PostgresForecastRepository(IForecastRepository):
    def __init__(self, session_factory: Any = None):
        self._session_factory = session_factory
        self._fallback = InMemoryForecastRepository()

    async def save_forecast(self, forecast_id: str, entity_id: str, forecast_type: str, data: dict[str, Any]) -> None:
        if not self._session_factory:
            return await self._fallback.save_forecast(forecast_id, entity_id, forecast_type, data)
        async with self._session_factory() as session:
            record = ForecastRecord(
                forecast_id=forecast_id,
                entity_id=entity_id,
                forecast_type=forecast_type,
                horizon=data.get("horizon_hours") or data.get("horizon", ""),
                data_json=json.dumps(data),
                generated_at=data.get("generated_at", datetime.now(timezone.utc).isoformat()),
                confidence=data.get("confidence", 0.0)
            )
            session.add(record)
            await session.commit()

    async def get_forecast(self, forecast_id: str) -> dict[str, Any] | None:
        if not self._session_factory:
            return await self._fallback.get_forecast(forecast_id)
        async with self._session_factory() as session:
            result = await session.execute(select(ForecastRecord).where(ForecastRecord.forecast_id == forecast_id))
            record = result.scalars().first()
            if record:
                return json.loads(record.data_json)
            return None

    async def get_latest_forecast(self, entity_id: str, forecast_type: str) -> dict[str, Any] | None:
        if not self._session_factory:
            return await self._fallback.get_latest_forecast(entity_id, forecast_type)
        async with self._session_factory() as session:
            result = await session.execute(
                select(ForecastRecord)
                .where(ForecastRecord.entity_id == entity_id)
                .where(ForecastRecord.forecast_type == forecast_type)
                .order_by(ForecastRecord.generated_at.desc())
                .limit(1)
            )
            record = result.scalars().first()
            if record:
                return json.loads(record.data_json)
            return None

    async def list_forecasts(self, entity_id: str | None, forecast_type: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
        if not self._session_factory:
            return await self._fallback.list_forecasts(entity_id, forecast_type, limit, offset)
        async with self._session_factory() as session:
            query = select(ForecastRecord)
            if entity_id:
                query = query.where(ForecastRecord.entity_id == entity_id)
            if forecast_type:
                query = query.where(ForecastRecord.forecast_type == forecast_type)
            query = query.order_by(ForecastRecord.generated_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            return [json.loads(r.data_json) for r in result.scalars().all()]

    async def save_scenario(self, scenario_id: str, entity_id: str, data: dict[str, Any]) -> None:
        if not self._session_factory:
            return await self._fallback.save_scenario(scenario_id, entity_id, data)
        async with self._session_factory() as session:
            record = ScenarioRecord(
                scenario_id=scenario_id,
                entity_id=entity_id,
                forecast_type=data.get("type", ""),
                data_json=json.dumps(data),
                generated_at=datetime.now(timezone.utc).isoformat()
            )
            session.add(record)
            await session.commit()

    async def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        if not self._session_factory:
            return await self._fallback.get_scenario(scenario_id)
        async with self._session_factory() as session:
            result = await session.execute(select(ScenarioRecord).where(ScenarioRecord.scenario_id == scenario_id))
            record = result.scalars().first()
            if record:
                return json.loads(record.data_json)
            return None

    async def list_scenarios(self, entity_id: str, limit: int) -> list[dict[str, Any]]:
        if not self._session_factory:
            return await self._fallback.list_scenarios(entity_id, limit)
        async with self._session_factory() as session:
            query = select(ScenarioRecord).where(ScenarioRecord.entity_id == entity_id).order_by(ScenarioRecord.generated_at.desc()).limit(limit)
            result = await session.execute(query)
            return [json.loads(r.data_json) for r in result.scalars().all()]

    async def count_forecasts(self, entity_id: str | None, forecast_type: str | None) -> int:
        if not self._session_factory:
            return await self._fallback.count_forecasts(entity_id, forecast_type)
        return 0

    async def delete_stale_forecasts(self, older_than_hours: int) -> int:
        if not self._session_factory:
            return await self._fallback.delete_stale_forecasts(older_than_hours)
        return 0

import json
from typing import Any, Optional
from sqlalchemy import Table, Column, String, Float, MetaData, JSON, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text, select, insert, desc

try:
    from app.infrastructure.postgres.engine import get_engine
except ImportError:
    def get_engine(): return None

from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import EntityType, RiskType
from app.modules.risk_prediction.domain.models import RiskAssessment, RiskTimeline

log = get_logger(__name__)
metadata = MetaData()

risk_assessments_table = Table(
    "risk_assessments",
    metadata,
    Column("assessment_id", String, primary_key=True),
    Column("entity_id", String, nullable=False),
    Column("entity_type", String, nullable=False),
    Column("timestamp", String, nullable=False), # using string for TIMESTAMPTZ as simplified map
    Column("risk_value", Float),
    Column("risk_level", String),
    Column("confidence", Float),
    Column("payload", JSONB),
    Column("created_at", String)
)

class PostgresRiskRepository:
    """PostgreSQL implementation of IRiskRepository."""
    def __init__(self):
        self.engine = get_engine()
        self._in_memory_db = {}
        
    async def initialize_schema(self):
        if not self.engine:
            return
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    async def save_assessment(self, assessment: RiskAssessment) -> None:
        if not self.engine:
            self._in_memory_db[assessment.id] = assessment
            return
            
        payload = assessment.model_dump(mode="json")
        max_pred = max(assessment.predictions, key=lambda p: p.score.probability, default=None)
        risk_val = max_pred.score.probability if max_pred else 0.0
        risk_lvl = max_pred.score.level.value if hasattr(max_pred.score, 'level') else "UNKNOWN"
        conf = max_pred.score.confidence if max_pred else 0.0
        
        async with self.engine.begin() as conn:
            stmt = insert(risk_assessments_table).values(
                assessment_id=assessment.id,
                entity_id=assessment.entity_id,
                entity_type=assessment.entity_type.value,
                timestamp=assessment.timestamp,
                risk_value=risk_val,
                risk_level=risk_lvl,
                confidence=conf,
                payload=payload
            )
            await conn.execute(stmt)

    async def get_latest_assessment(self, entity_id: str, risk_type: RiskType) -> Optional[RiskAssessment]:
        if not self.engine:
            matching = [a for a in self._in_memory_db.values() if a.entity_id == entity_id]
            return sorted(matching, key=lambda x: x.timestamp, reverse=True)[0] if matching else None

        async with self.engine.connect() as conn:
            stmt = select(risk_assessments_table).where(
                risk_assessments_table.c.entity_id == entity_id
            ).order_by(desc(risk_assessments_table.c.timestamp)).limit(1)
            
            result = await conn.execute(stmt)
            row = result.fetchone()
            if not row:
                return None
                
            return RiskAssessment.model_validate(row.payload)

    async def get_risk_history(self, entity_id: str, limit: int = 10) -> RiskTimeline:
        if not self.engine:
            matching = [a for a in self._in_memory_db.values() if a.entity_id == entity_id]
            sorted_matching = sorted(matching, key=lambda x: x.timestamp, reverse=True)[:limit]
            return RiskTimeline(entity_id=entity_id, assessments=sorted_matching)

        async with self.engine.connect() as conn:
            stmt = select(risk_assessments_table).where(
                risk_assessments_table.c.entity_id == entity_id
            ).order_by(desc(risk_assessments_table.c.timestamp)).limit(limit)
            
            result = await conn.execute(stmt)
            rows = result.fetchall()
            
            assessments = [RiskAssessment.model_validate(row.payload) for row in rows]
            return RiskTimeline(entity_id=entity_id, assessments=assessments)
